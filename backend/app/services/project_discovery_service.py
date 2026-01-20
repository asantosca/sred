# app/services/project_discovery_service.py
"""
Project Discovery Service

Automatically discovers potential SR&ED projects by clustering documents
based on temporal, semantic, and team features.
"""

import logging
from datetime import datetime, timezone, date
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass, field
from collections import Counter
from decimal import Decimal

import numpy as np
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Document, Project, ProjectDiscoveryRun,
    DocumentProjectTag, Claim
)
from app.services.vector_storage import vector_storage_service
from app.services.sred_signal_detector import sred_signal_detector
from app.services.entity_extractor import entity_extractor, project_name_normalizer
from app.core.config import settings

logger = logging.getLogger(__name__)

# Import clustering libraries (optional - graceful fallback if not installed)
try:
    from sklearn.preprocessing import StandardScaler
    from hdbscan import HDBSCAN
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False
    logger.warning(
        "scikit-learn or hdbscan not installed. "
        "Install with: pip install scikit-learn hdbscan"
    )


@dataclass
class ProjectCandidate:
    """Discovered project candidate"""
    documents: List[UUID] = field(default_factory=list)
    name: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_members: List[str] = field(default_factory=list)
    contributors: List[Dict] = field(default_factory=list)  # Structured contributor info with titles/roles
    sred_score: float = 0.0
    confidence: float = 0.0
    signals: Dict[str, int] = field(default_factory=dict)
    summary: str = ""
    discovery_source: str = "clustering"  # "sred_signal", "name_based", or "clustering"
    name_variations: List[str] = field(default_factory=list)  # Original name variations found


class ProjectDiscoveryService:
    """
    Automatically discover SR&ED projects from unorganized documents.

    Uses multi-dimensional clustering:
    1. Temporal clustering (when work happened)
    2. Semantic clustering (what work was about)
    3. Team clustering (who did the work)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def discover_projects(
        self,
        claim_id: UUID,
        company_id: UUID,
        user_id: Optional[UUID] = None,
        min_cluster_size: int = 3,
        backfill_signals: bool = True,
        discovery_mode: str = "hybrid",
        fuzzy_matching: bool = True,
        fuzzy_threshold: float = 0.8
    ) -> Dict:
        """
        Main entry point: discover projects for a claim.

        Args:
            claim_id: UUID of the claim to analyze
            company_id: Company ID for tenant isolation
            user_id: Optional user who triggered discovery
            min_cluster_size: Minimum documents per cluster (for clustering fallback)
            backfill_signals: Whether to compute SR&ED signals for docs missing them
            discovery_mode: "sred_first" (recommended), "names_only", "clustering_only", or "hybrid"
            fuzzy_matching: Enable fuzzy matching for project name variations
            fuzzy_threshold: Similarity threshold for fuzzy matching (0.0-1.0)

        Returns:
            {
                "high_confidence": [ProjectCandidate, ...],
                "medium_confidence": [...],
                "low_confidence": [...],
                "orphan_document_ids": [UUID, ...]
            }
        """
        # Validate discovery_mode
        valid_modes = ["sred_first", "names_only", "clustering_only", "hybrid"]
        if discovery_mode not in valid_modes:
            discovery_mode = "sred_first"  # Default to SR&ED-first discovery

        # Clustering modes require clustering libraries
        if discovery_mode in ["clustering_only", "hybrid", "sred_first"] and not CLUSTERING_AVAILABLE:
            if discovery_mode == "clustering_only":
                raise RuntimeError(
                    "Clustering libraries not available. "
                    "Install with: pip install scikit-learn hdbscan"
                )
            else:
                # Fall back to names_only if clustering not available
                logger.warning(
                    "Clustering not available, falling back to names_only mode"
                )
                discovery_mode = "names_only"

        # Start discovery run tracking
        run = ProjectDiscoveryRun(
            claim_id=claim_id,
            status="running",
            discovery_algorithm=f"name_based_{discovery_mode}",
            parameters={
                "min_cluster_size": min_cluster_size,
                "backfill_signals": backfill_signals,
                "discovery_mode": discovery_mode,
                "fuzzy_matching": fuzzy_matching,
                "fuzzy_threshold": fuzzy_threshold
            },
            created_by=user_id
        )
        self.db.add(run)
        await self.db.flush()

        start_time = datetime.now(timezone.utc)
        orphan_document_ids: List[UUID] = []

        try:
            logger.debug(f"[DISCOVERY] Starting project discovery for claim {claim_id}")

            # 1. Fetch all processed documents for this claim
            docs = await self._fetch_documents(claim_id, company_id)
            run.total_documents_analyzed = len(docs)

            logger.debug(f"[DISCOVERY] Found {len(docs)} documents for discovery")

            if not docs:
                logger.debug(f"[DISCOVERY] No documents found for claim {claim_id} - check processing status and fiscal year")
                result = {
                    "high_confidence": [],
                    "medium_confidence": [],
                    "low_confidence": [],
                    "orphan_document_ids": []
                }
                run.status = "completed"
                run.projects_discovered = 0
                await self.db.commit()
                return result

            # 2. Optionally backfill SR&ED signals for docs missing them
            if backfill_signals:
                await self._backfill_sred_signals(docs)

            candidates: List[ProjectCandidate] = []
            remaining_docs = docs.copy()
            orphan_document_ids: List[UUID] = []

            # 3. SR&ED-first discovery (recommended mode)
            if discovery_mode == "sred_first":
                logger.debug(f"[DISCOVERY] Using sred_first mode")

                # 3a. Identify documents with SR&ED signals (R&D work)
                sred_docs, non_sred_docs = self._identify_sred_documents(docs)

                logger.debug(f"[DISCOVERY] Found {len(sred_docs)} SR&ED documents, {len(non_sred_docs)} non-SR&ED")

                if not sred_docs:
                    # No SR&ED documents found - return empty with all as orphans
                    logger.debug(f"[DISCOVERY] No SR&ED documents found")
                    orphan_document_ids = [doc.id for doc in docs]

                elif len(sred_docs) < min_cluster_size:
                    # Too few SR&ED docs to cluster - treat each as potential project
                    logger.debug(f"[DISCOVERY] Too few SR&ED docs to cluster, creating individual projects")
                    for doc in sred_docs:
                        candidate = await self._analyze_cluster([doc], company_id)
                        candidate.name = self._generate_cluster_name_from_content([doc])
                        candidate.discovery_source = "sred_signal"
                        candidates.append(candidate)
                    orphan_document_ids = [doc.id for doc in non_sred_docs]

                else:
                    # 3b. Cluster SR&ED documents by semantic similarity
                    logger.debug(f"[DISCOVERY] Clustering {len(sred_docs)} SR&ED documents")
                    clusters = await self._cluster_documents(
                        sred_docs, company_id, min_cluster_size
                    )

                    logger.debug(f"[DISCOVERY] Found {len(clusters)} clusters from SR&ED documents")

                    # Track which SR&ED docs got clustered
                    clustered_sred_ids = set()

                    for cluster_docs in clusters:
                        # Analyze the cluster
                        candidate = await self._analyze_cluster(cluster_docs, company_id)

                        # Generate name from content (uses project names as labels, not grouping)
                        candidate.name = self._generate_cluster_name_from_content(cluster_docs)
                        candidate.discovery_source = "sred_signal"

                        # Boost confidence for SR&ED-identified clusters
                        candidate.confidence = min(candidate.confidence * 1.2, 1.0)

                        candidates.append(candidate)
                        clustered_sred_ids.update(doc.id for doc in cluster_docs)

                    # SR&ED docs not in any cluster
                    unclustered_sred = [d for d in sred_docs if d.id not in clustered_sred_ids]

                    # FALLBACK: If clustering failed completely (no clusters),
                    # create individual projects for each SR&ED document
                    if not clusters and unclustered_sred:
                        logger.debug(f"[DISCOVERY] Clustering failed, creating individual projects for {len(unclustered_sred)} unclustered SR&ED docs")
                        for doc in unclustered_sred:
                            candidate = await self._analyze_cluster([doc], company_id)
                            candidate.name = self._generate_cluster_name_from_content([doc])
                            candidate.discovery_source = "sred_signal"
                            # Lower confidence for single-doc projects
                            candidate.confidence = min(candidate.confidence, 0.5)
                            candidates.append(candidate)
                        unclustered_sred = []  # All handled, no orphans

                    orphan_document_ids = [doc.id for doc in unclustered_sred + non_sred_docs]

                    logger.debug(f"[DISCOVERY] {len(unclustered_sred)} SR&ED docs unclustered, {len(non_sred_docs)} non-SR&ED orphans")

            # 4. Name-based grouping (primary method for hybrid and names_only)
            elif discovery_mode in ["hybrid", "names_only"]:
                name_groups, orphans = self._group_by_project_names(
                    docs,
                    fuzzy_matching=fuzzy_matching,
                    fuzzy_threshold=fuzzy_threshold
                )

                # Analyze each name-based group
                for canonical_name, group_data in name_groups.items():
                    group_docs = group_data["documents"]
                    variations = group_data["variations"]

                    # Allow single-doc projects for name-based groups (explicit names are reliable)
                    if len(group_docs) >= 1:
                        candidate = await self._analyze_cluster(group_docs, company_id)
                        candidate.name = canonical_name
                        candidate.discovery_source = "name_based"
                        candidate.name_variations = variations
                        # Recalculate confidence for name-based groups
                        candidate.confidence = self._calculate_name_based_confidence(
                            group_docs, variations, candidate.sred_score
                        )
                        candidates.append(candidate)
                    else:
                        # Single-doc groups go to orphans for potential semantic matching
                        orphans.extend(group_docs)

                remaining_docs = orphans

                logger.info(
                    f"Name-based grouping: {len(name_groups)} groups, "
                    f"{len(remaining_docs)} orphan documents"
                )

            # 4. Handle remaining/orphan documents
            if discovery_mode == "hybrid" and remaining_docs:
                # 4a. Try semantic matching of orphans to existing groups
                if candidates:
                    matched, still_orphans = await self._match_orphans_semantically(
                        remaining_docs, candidates, company_id
                    )
                    remaining_docs = still_orphans

                    logger.info(
                        f"Semantic matching: {len(matched)} docs matched, "
                        f"{len(still_orphans)} still orphans"
                    )

                # 4b. Cluster remaining orphans
                if len(remaining_docs) >= min_cluster_size:
                    clusters = await self._cluster_documents(
                        remaining_docs, company_id, min_cluster_size
                    )

                    for cluster_docs in clusters:
                        candidate = await self._analyze_cluster(cluster_docs, company_id)
                        candidate.discovery_source = "clustering"
                        candidates.append(candidate)

                        # Remove clustered docs from remaining
                        clustered_ids = {doc.id for doc in cluster_docs}
                        remaining_docs = [d for d in remaining_docs if d.id not in clustered_ids]

                # Remaining docs are truly orphans
                orphan_document_ids = [doc.id for doc in remaining_docs]

            elif discovery_mode == "clustering_only":
                # Pure clustering mode
                if len(docs) >= min_cluster_size:
                    clusters = await self._cluster_documents(docs, company_id, min_cluster_size)

                    for cluster_docs in clusters:
                        candidate = await self._analyze_cluster(cluster_docs, company_id)
                        candidate.discovery_source = "clustering"
                        candidates.append(candidate)

                        clustered_ids = {doc.id for doc in cluster_docs}
                        remaining_docs = [d for d in remaining_docs if d.id not in clustered_ids]

                    orphan_document_ids = [doc.id for doc in remaining_docs]
                else:
                    # Too few docs for clustering
                    result = await self._handle_small_dataset(docs, company_id)
                    result["orphan_document_ids"] = []
                    run.status = "completed"
                    run.projects_discovered = sum(
                        len(result[k]) for k in ["high_confidence", "medium_confidence", "low_confidence"]
                    )
                    await self.db.commit()
                    return result

            elif discovery_mode == "names_only":
                # Names-only mode: remaining docs are orphans
                orphan_document_ids = [doc.id for doc in remaining_docs]

            # 5. Deduplicate candidates by name (merge documents if same name)
            logger.debug(f"[DISCOVERY] Candidates BEFORE dedup: {[(c.name, c.discovery_source, len(c.documents)) for c in candidates]}")
            candidates = self._deduplicate_candidates(candidates)
            logger.debug(f"[DISCOVERY] Candidates AFTER dedup: {[(c.name, len(c.documents)) for c in candidates]}")

            # 6. Categorize by confidence
            categorized = self._categorize_candidates(candidates)
            categorized["orphan_document_ids"] = orphan_document_ids

            # 7. Update run record
            run.status = "completed"
            run.projects_discovered = len(candidates)
            run.high_confidence_count = len(categorized["high_confidence"])
            run.medium_confidence_count = len(categorized["medium_confidence"])
            run.low_confidence_count = len(categorized["low_confidence"])
            run.execution_time_seconds = Decimal(
                str((datetime.now(timezone.utc) - start_time).total_seconds())
            )

            await self.db.commit()

            logger.info(
                f"Discovery complete for claim {claim_id}: "
                f"{len(candidates)} projects found "
                f"(high={run.high_confidence_count}, "
                f"medium={run.medium_confidence_count}, "
                f"low={run.low_confidence_count}, "
                f"orphans={len(orphan_document_ids)})"
            )

            return categorized

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            await self.db.commit()
            logger.error(f"Discovery failed for claim {claim_id}: {e}", exc_info=True)
            raise

    async def _fetch_documents(
        self,
        claim_id: UUID,
        company_id: UUID
    ) -> List[Document]:
        """Fetch all processed documents for claim with tenant isolation and fiscal year filtering"""
        # First get the claim to access fiscal year info
        claim_query = select(Claim).where(
            and_(
                Claim.id == claim_id,
                Claim.company_id == company_id
            )
        )
        claim_result = await self.db.execute(claim_query)
        claim = claim_result.scalar_one_or_none()

        if not claim:
            return []

        # Fetch all processed documents for this claim
        query = (
            select(Document)
            .where(
                and_(
                    Document.claim_id == claim_id,
                    Document.processing_status.in_(['embedded', 'complete']),
                    Document.indexed_for_search == True
                )
            )
            .order_by(Document.document_date.asc().nullslast())
        )
        result = await self.db.execute(query)
        all_docs = list(result.scalars().all())

        logger.debug(f"[DISCOVERY] Query returned {len(all_docs)} processed documents for claim {claim_id}")

        # Filter by fiscal year if fiscal_year_end is set
        if claim.fiscal_year_end:
            from dateutil.relativedelta import relativedelta
            fy_start = claim.fiscal_year_end - relativedelta(years=1) + relativedelta(days=1)
            logger.debug(f"[DISCOVERY] Fiscal year period: {fy_start} to {claim.fiscal_year_end}")

            filtered_docs = []
            excluded_count = 0
            no_dates_count = 0

            for doc in all_docs:
                is_relevant, reason = self._is_document_in_fiscal_year(doc, claim.fiscal_year_end)
                if is_relevant:
                    filtered_docs.append(doc)
                    if "No dates found" in reason:
                        no_dates_count += 1
                else:
                    excluded_count += 1
                    logger.debug(f"[DISCOVERY] Document {doc.id} ({doc.filename}) excluded: {reason}")

            logger.debug(
                f"[DISCOVERY] Fiscal year filter: {len(filtered_docs)}/{len(all_docs)} documents included "
                f"(excluded={excluded_count}, no_dates={no_dates_count})"
            )
            return filtered_docs

        # No fiscal year set - return all documents
        return all_docs

    def _is_document_in_fiscal_year(
        self,
        doc: Document,
        fiscal_year_end: date
    ) -> Tuple[bool, str]:
        """
        Check if a document's content dates overlap with the fiscal year.

        A document is considered relevant if:
        1. Its extracted date range overlaps with the fiscal year, OR
        2. It has no extracted dates but document_date falls within FY, OR
        3. It has no dates at all (included with flag for manual review)

        Args:
            doc: Document to check
            fiscal_year_end: End date of the fiscal year

        Returns:
            Tuple of (is_relevant: bool, reason: str)
        """
        from dateutil.relativedelta import relativedelta

        # Calculate fiscal year start (day after previous year's end)
        # e.g., FY ending Dec 31, 2024 starts Jan 1, 2024
        fy_start = fiscal_year_end - relativedelta(years=1) + relativedelta(days=1)
        fy_end = fiscal_year_end

        # Try to get dates from temporal metadata
        extracted_dates = []
        if doc.temporal_metadata and doc.temporal_metadata.get("date_references"):
            date_refs = doc.temporal_metadata["date_references"]
            for date_str in date_refs:
                try:
                    # Parse ISO date string (YYYY-MM-DD)
                    parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
                    extracted_dates.append(parsed)
                except (ValueError, TypeError):
                    continue

        if extracted_dates:
            # Check if document's date range overlaps with fiscal year
            doc_earliest = min(extracted_dates)
            doc_latest = max(extracted_dates)

            # Overlap check: doc_earliest <= fy_end AND doc_latest >= fy_start
            if doc_earliest <= fy_end and doc_latest >= fy_start:
                return True, f"Date range {doc_earliest} to {doc_latest} overlaps FY"
            else:
                return False, f"Date range {doc_earliest} to {doc_latest} outside FY {fy_start} to {fy_end}"

        # No extracted dates - fall back to document_date field
        if doc.document_date:
            if fy_start <= doc.document_date <= fy_end:
                return True, f"document_date {doc.document_date} within FY"
            else:
                return False, f"document_date {doc.document_date} outside FY {fy_start} to {fy_end}"

        # No dates at all - include with flag (could be relevant, needs manual review)
        # For now, we include these documents as we don't want to lose potentially relevant content
        return True, "No dates found - included for manual review"

    async def _backfill_sred_signals(self, docs: List[Document]) -> None:
        """Compute SR&ED signals for documents that don't have them"""
        backfilled = 0
        for doc in docs:
            if doc.sred_signals and doc.sred_signals.get('score') is not None:
                continue

            if not doc.extracted_text:
                continue

            # Detect signals
            signals = sred_signal_detector.detect_signals(doc.extracted_text)
            entities = entity_extractor.extract_entities(doc.extracted_text)

            doc.sred_signals = signals.to_dict()
            doc.temporal_metadata = entities.to_dict()
            backfilled += 1

        if backfilled > 0:
            await self.db.commit()
            logger.info(f"Backfilled SR&ED signals for {backfilled} documents")

    def _identify_sred_documents(
        self,
        docs: List[Document],
        min_sred_score: float = 0.2,
        require_uncertainty: bool = True
    ) -> Tuple[List[Document], List[Document]]:
        """
        Identify documents that contain SR&ED-eligible work.

        Uses SR&ED signals (uncertainty, systematic investigation, etc.)
        to find documents describing actual R&D work, rather than relying
        on project naming conventions.

        Args:
            docs: All documents to analyze
            min_sred_score: Minimum SR&ED score to be considered R&D (0.0-1.0)
            require_uncertainty: If True, document must have uncertainty signals

        Returns:
            Tuple of (sred_documents, non_sred_documents)
        """
        sred_docs = []
        non_sred_docs = []

        for doc in docs:
            if not doc.sred_signals:
                # No signals computed - treat as non-SR&ED
                non_sred_docs.append(doc)
                continue

            score = doc.sred_signals.get("score", 0)
            uncertainty = doc.sred_signals.get("uncertainty_keywords", 0)
            systematic = doc.sred_signals.get("systematic_keywords", 0)

            # Check if document describes R&D work
            is_sred = False

            if score >= min_sred_score:
                if require_uncertainty:
                    # Must have at least some uncertainty language
                    # (the core of SR&ED is technological uncertainty)
                    if uncertainty >= 1:
                        is_sred = True
                    # Or strong systematic + advancement signals (describing completed R&D)
                    elif systematic >= 2 and doc.sred_signals.get("advancement_keywords", 0) >= 1:
                        is_sred = True
                else:
                    is_sred = True

            if is_sred:
                sred_docs.append(doc)
            else:
                non_sred_docs.append(doc)

        logger.info(
            f"SR&ED identification: {len(sred_docs)} R&D documents, "
            f"{len(non_sred_docs)} non-R&D documents"
        )

        return sred_docs, non_sred_docs

    def _generate_cluster_name_from_content(
        self,
        docs: List[Document]
    ) -> str:
        """
        Generate a descriptive project name from document content.

        Uses extracted entities and document metadata to create a meaningful name.
        Falls back to generic naming if no good identifiers found.
        """
        # First try: extracted project names from metadata
        all_project_names = []
        all_jira_codes = []
        technical_terms = []

        for doc in docs:
            if doc.temporal_metadata:
                names = doc.temporal_metadata.get("project_names", [])
                jira = doc.temporal_metadata.get("jira_codes", [])
                tech = doc.temporal_metadata.get("technical_terms", [])

                # Filter out stopwords
                for name in names:
                    normalized = project_name_normalizer.normalize(name)
                    if normalized:
                        all_project_names.append(name)

                all_jira_codes.extend(jira)
                technical_terms.extend(tech)

        # Use most common valid project name
        if all_project_names:
            name_counter = Counter(all_project_names)
            return name_counter.most_common(1)[0][0]

        # Use most common Jira code prefix
        if all_jira_codes:
            prefixes = [code.split("-")[0] for code in all_jira_codes if "-" in code]
            if prefixes:
                prefix_counter = Counter(prefixes)
                return f"Project {prefix_counter.most_common(1)[0][0]}"

        # Use most common technical term (if significant)
        if technical_terms:
            term_counter = Counter(technical_terms)
            top_term, count = term_counter.most_common(1)[0]
            if count >= 2 and len(top_term) >= 3:
                return f"{top_term} R&D"

        # Fall back to document type
        doc_types = [doc.document_type for doc in docs if doc.document_type]
        if doc_types:
            type_counter = Counter(doc_types)
            common_type = type_counter.most_common(1)[0][0]
            return f"{common_type.replace('_', ' ').title()} Project"

        return f"R&D Project ({len(docs)} docs)"

    def _group_by_project_names(
        self,
        docs: List[Document],
        fuzzy_matching: bool = True,
        fuzzy_threshold: float = 0.8
    ) -> Tuple[Dict[str, Dict], List[Document]]:
        """
        Group documents by extracted project names.

        Args:
            docs: List of documents to group
            fuzzy_matching: Enable fuzzy matching for name variations
            fuzzy_threshold: Similarity threshold for fuzzy matching

        Returns:
            Tuple of:
            - Dict mapping canonical name to {"documents": [...], "variations": [...]}
            - List of orphan documents (no project names)
        """
        # Collect all project names from documents
        doc_project_names: Dict[UUID, List[str]] = {}  # doc_id -> project names

        for doc in docs:
            names = []
            if doc.temporal_metadata:
                names.extend(doc.temporal_metadata.get("project_names", []))
                # Also include Jira codes as potential project identifiers
                jira_codes = doc.temporal_metadata.get("jira_codes", [])
                # Group Jira codes by project prefix (e.g., "AURORA-123" -> "AURORA")
                for code in jira_codes:
                    prefix = code.split("-")[0] if "-" in code else code
                    if prefix and len(prefix) >= 2:
                        names.append(prefix)

            doc_project_names[doc.id] = names

        # Collect all unique project names
        all_names = []
        for names in doc_project_names.values():
            all_names.extend(names)

        logger.debug(f"[DISCOVERY] All extracted project names: {all_names}")

        if not all_names:
            # No project names found, all docs are orphans
            return {}, docs

        # Filter out stopwords before grouping
        valid_names = [
            name for name in all_names
            if project_name_normalizer.normalize(name)  # Non-empty after normalization
        ]

        logger.debug(f"[DISCOVERY] Valid names after stopword filter: {valid_names}")

        if not valid_names:
            # All names were stopwords, all docs are orphans
            return {}, docs

        # Group similar names together
        if fuzzy_matching:
            name_groups = project_name_normalizer.group_by_similarity(
                valid_names, threshold=fuzzy_threshold
            )
        else:
            # No fuzzy matching: only normalize and group exact matches
            name_groups = {}
            for name in valid_names:
                canonical = project_name_normalizer.normalize(name)
                if canonical and canonical not in name_groups:
                    name_groups[canonical] = []
                if canonical and name not in name_groups[canonical]:
                    name_groups[canonical].append(name)

        # Remove any empty-key groups (shouldn't happen but safety check)
        name_groups = {k: v for k, v in name_groups.items() if k}

        # Build canonical name mapping
        name_to_canonical: Dict[str, str] = {}
        for canonical, variations in name_groups.items():
            for var in variations:
                normalized_var = project_name_normalizer.normalize(var)
                if normalized_var:
                    name_to_canonical[normalized_var] = canonical
                name_to_canonical[var] = canonical

        # Assign documents to project groups (multi-assignment allowed)
        project_groups: Dict[str, Dict] = {}  # canonical -> {"documents": set, "variations": set}

        orphans = []

        for doc in docs:
            doc_names = doc_project_names.get(doc.id, [])

            if not doc_names:
                orphans.append(doc)
                continue

            assigned = False
            for name in doc_names:
                # Look up canonical name
                canonical = None
                normalized_name = project_name_normalizer.normalize(name)

                # Skip stopwords (normalize returns empty string)
                if not normalized_name:
                    continue

                if name in name_to_canonical:
                    canonical = name_to_canonical[name]
                elif normalized_name in name_to_canonical:
                    canonical = name_to_canonical[normalized_name]
                else:
                    # Try fuzzy matching against existing groups
                    if fuzzy_matching:
                        for group_canonical in project_groups.keys():
                            if project_name_normalizer.are_similar(
                                normalized_name, group_canonical, fuzzy_threshold
                            ):
                                canonical = group_canonical
                                break

                    if canonical is None:
                        # Create new group
                        canonical = normalized_name
                        name_to_canonical[name] = canonical
                        name_to_canonical[normalized_name] = canonical

                # Add document to group
                if canonical not in project_groups:
                    project_groups[canonical] = {
                        "documents": [],
                        "doc_ids": set(),
                        "variations": set()
                    }

                # Only add document once per group
                if doc.id not in project_groups[canonical]["doc_ids"]:
                    project_groups[canonical]["documents"].append(doc)
                    project_groups[canonical]["doc_ids"].add(doc.id)

                project_groups[canonical]["variations"].add(name)
                assigned = True

            if not assigned:
                orphans.append(doc)

        # Convert sets to lists for JSON serialization
        result_groups = {}
        for canonical, data in project_groups.items():
            result_groups[canonical] = {
                "documents": data["documents"],
                "variations": list(data["variations"])
            }

        return result_groups, orphans

    def _calculate_name_based_confidence(
        self,
        docs: List[Document],
        variations: List[str],
        sred_score: float
    ) -> float:
        """
        Calculate confidence for name-based project groups.

        Confidence factors:
        - Name match quality: 30% (fewer variations = higher confidence)
        - Document count: 25%
        - SR&ED score: 25%
        - Temporal coherence: 20% (dates within reasonable range)

        Args:
            docs: Documents in the group
            variations: Name variations found
            sred_score: SR&ED eligibility score

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Name match quality (fewer variations = more consistent naming = higher confidence)
        variation_count = len(variations) if variations else 1
        name_quality = max(0.3, 1.0 - (variation_count - 1) * 0.15)

        # Document count score (sigmoid curve)
        doc_count = len(docs)
        doc_score = min(1.0, doc_count / 5.0)  # Scales up to 5 docs

        # Temporal coherence (check if dates are within a year)
        dates = []
        for d in docs:
            if d.document_date:
                dates.append(d.document_date)

        temporal_score = 0.5  # Default if no dates
        if len(dates) >= 2:
            date_range = (max(dates) - min(dates)).days
            if date_range <= 365:  # Within a year
                temporal_score = 1.0
            elif date_range <= 730:  # Within 2 years
                temporal_score = 0.7
            else:
                temporal_score = 0.4

        # Weighted combination
        confidence = (
            name_quality * 0.30 +
            doc_score * 0.25 +
            sred_score * 0.25 +
            temporal_score * 0.20
        )

        return min(confidence, 1.0)

    async def _match_orphans_semantically(
        self,
        orphans: List[Document],
        candidates: List[ProjectCandidate],
        company_id: UUID,
        threshold: float = 0.75
    ) -> Tuple[List[Document], List[Document]]:
        """
        Try to match orphan documents to existing project groups semantically.

        Uses vector similarity between orphan document embeddings and
        average embeddings of existing project groups.

        Args:
            orphans: Documents without project name matches
            candidates: Existing project candidates to match against
            company_id: Company ID for embedding retrieval
            threshold: Minimum similarity to match

        Returns:
            Tuple of (matched documents, still-orphan documents)
        """
        if not orphans or not candidates:
            return [], orphans

        matched = []
        still_orphans = []

        # Get average embeddings for each candidate
        candidate_embeddings: Dict[int, np.ndarray] = {}

        for idx, candidate in enumerate(candidates):
            embeddings = []
            for doc_id in candidate.documents[:5]:  # Sample first 5 docs
                try:
                    emb_data = await vector_storage_service.get_embeddings(
                        document_id=doc_id,
                        company_id=company_id
                    )
                    if emb_data:
                        emb = np.array(emb_data[0]["embedding"])
                        embeddings.append(emb)
                except Exception:
                    continue

            if embeddings:
                avg_emb = np.mean(embeddings, axis=0)
                candidate_embeddings[idx] = avg_emb / np.linalg.norm(avg_emb)

        if not candidate_embeddings:
            return [], orphans

        # Match each orphan
        for orphan in orphans:
            try:
                orphan_emb_data = await vector_storage_service.get_embeddings(
                    document_id=orphan.id,
                    company_id=company_id
                )

                if not orphan_emb_data:
                    still_orphans.append(orphan)
                    continue

                orphan_emb = np.array(orphan_emb_data[0]["embedding"])
                orphan_emb = orphan_emb / np.linalg.norm(orphan_emb)

                # Find best matching candidate
                best_idx = None
                best_similarity = 0

                for idx, cand_emb in candidate_embeddings.items():
                    similarity = np.dot(orphan_emb, cand_emb)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_idx = idx

                if best_idx is not None and best_similarity >= threshold:
                    # Add orphan to matching candidate
                    candidates[best_idx].documents.append(orphan.id)
                    matched.append(orphan)
                else:
                    still_orphans.append(orphan)

            except Exception as e:
                logger.warning(f"Error matching orphan {orphan.id}: {e}")
                still_orphans.append(orphan)

        return matched, still_orphans

    async def _cluster_documents(
        self,
        docs: List[Document],
        company_id: UUID,
        min_cluster_size: int
    ) -> List[List[Document]]:
        """
        Multi-dimensional clustering algorithm.

        Combines:
        1. Temporal features (document dates)
        2. Semantic features (document embeddings)
        3. Team features (people mentioned)
        """
        # Extract features for each document
        features = []
        valid_docs = []
        docs_without_embeddings = 0

        logger.debug(f"[DISCOVERY] _cluster_documents called with {len(docs)} docs, min_cluster_size={min_cluster_size}")

        for doc in docs:
            try:
                temporal_features = self._extract_temporal_features(doc)
                semantic_features = await self._extract_semantic_features(doc, company_id)
                team_features = self._extract_team_features(doc)

                if semantic_features is None:
                    docs_without_embeddings += 1
                    logger.debug(f"[DISCOVERY] Doc {doc.id} ({doc.filename}) has no embeddings")
                    continue

                # Concatenate all features
                combined = np.concatenate([
                    temporal_features,
                    semantic_features[:50],  # Use first 50 dims of embedding for efficiency
                    team_features
                ])
                features.append(combined)
                valid_docs.append(doc)
            except Exception as e:
                logger.warning(f"Error extracting features for doc {doc.id}: {e}")
                logger.debug(f"[DISCOVERY] Error extracting features for doc {doc.id}: {e}")
                continue

        logger.debug(f"[DISCOVERY] Feature extraction: {len(valid_docs)} docs with embeddings, {docs_without_embeddings} without")

        if len(valid_docs) < min_cluster_size:
            logger.debug(f"[DISCOVERY] Not enough docs with embeddings ({len(valid_docs)} < {min_cluster_size}), returning empty")
            return []

        # Convert to numpy array
        X = np.array(features)

        # Normalize features
        scaler = StandardScaler()
        X_normalized = scaler.fit_transform(X)

        # Apply HDBSCAN
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=2,
            metric='euclidean',
            cluster_selection_method='eom'
        )

        cluster_labels = clusterer.fit_predict(X_normalized)

        # Log clustering results
        noise_count = sum(1 for label in cluster_labels if label == -1)
        unique_labels = set(label for label in cluster_labels if label != -1)
        logger.debug(f"[DISCOVERY] HDBSCAN results: {len(cluster_labels)} docs, {noise_count} noise, {len(unique_labels)} clusters")

        # Group documents by cluster
        clusters: Dict[int, List[Document]] = {}
        for doc, label in zip(valid_docs, cluster_labels):
            if label == -1:  # Noise (unclustered)
                continue
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(doc)

        logger.debug(f"[DISCOVERY] Final clusters: {[len(c) for c in clusters.values()]}")
        return list(clusters.values())

    def _extract_temporal_features(self, doc: Document) -> np.ndarray:
        """Extract temporal features from document"""
        # Use document_date or created_at
        if doc.document_date:
            date = datetime.combine(doc.document_date, datetime.min.time())
        else:
            date = doc.created_at or datetime.now(timezone.utc)

        if hasattr(date, 'tzinfo') and date.tzinfo:
            date = date.replace(tzinfo=None)

        # Days since 2020 (normalized)
        reference = datetime(2020, 1, 1)
        days_since = (date - reference).days / 365.0

        # Cyclical month encoding
        month = date.month
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)

        # Cyclical quarter encoding
        quarter = (month - 1) // 3 + 1
        quarter_sin = np.sin(2 * np.pi * quarter / 4)
        quarter_cos = np.cos(2 * np.pi * quarter / 4)

        return np.array([days_since, month_sin, month_cos, quarter_sin, quarter_cos])

    async def _extract_semantic_features(
        self,
        doc: Document,
        company_id: UUID
    ) -> Optional[np.ndarray]:
        """Get document's semantic embedding (average of chunk embeddings)"""
        try:
            embeddings_data = await vector_storage_service.get_embeddings(
                document_id=doc.id,
                company_id=company_id
            )

            if not embeddings_data:
                return None

            # Average the embeddings (first 5 chunks for efficiency)
            embeddings = [np.array(e["embedding"]) for e in embeddings_data[:5]]
            avg_embedding = np.mean(embeddings, axis=0)

            return avg_embedding

        except Exception as e:
            logger.warning(f"Error getting embeddings for doc {doc.id}: {e}")
            return None

    def _extract_team_features(self, doc: Document) -> np.ndarray:
        """Encode team membership as features using hash bucketing"""
        team_members = []
        if doc.temporal_metadata:
            team_members = doc.temporal_metadata.get("team_members", [])

        # Use 10 hash buckets to represent team composition
        team_vector = np.zeros(10)

        for member in team_members:
            bucket = hash(member) % 10
            team_vector[bucket] = 1

        return team_vector

    def _extract_sred_dates(
        self,
        docs: List[Document]
    ) -> Tuple[Optional[date], Optional[date]]:
        """
        Extract SR&ED-relevant project dates.

        Start Date: Earliest document with technological uncertainty signals
                   (when the problem was first identified)

        End Date: Latest document with advancement OR failure/abandonment signals
                 (when uncertainty was resolved or project abandoned)

        Falls back to document date range if no SR&ED signals found.
        """
        uncertainty_dates = []  # Docs mentioning uncertainty (start candidates)
        resolution_dates = []   # Docs mentioning advancement or abandonment (end candidates)
        all_dates = []          # Fallback: all document dates

        for doc in docs:
            # Get document date
            doc_date = None
            if doc.document_date:
                doc_date = doc.document_date
            elif doc.temporal_metadata and doc.temporal_metadata.get("date_references"):
                # Use earliest extracted date from content
                date_refs = doc.temporal_metadata["date_references"]
                for date_str in date_refs:
                    try:
                        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
                        if doc_date is None or parsed < doc_date:
                            doc_date = parsed
                    except (ValueError, TypeError):
                        continue
            elif doc.created_at:
                doc_date = doc.created_at.date()

            if not doc_date:
                continue

            all_dates.append(doc_date)

            # Check SR&ED signals
            if doc.sred_signals:
                uncertainty = doc.sred_signals.get("uncertainty_keywords", 0)
                advancement = doc.sred_signals.get("advancement_keywords", 0)
                failure = doc.sred_signals.get("failure_keywords", 0)

                # Documents with uncertainty = potential start points
                if uncertainty >= 1:
                    uncertainty_dates.append(doc_date)

                # Documents with advancement or failure = potential end points
                if advancement >= 1 or failure >= 1:
                    resolution_dates.append(doc_date)

        # Determine start date
        if uncertainty_dates:
            start_date = min(uncertainty_dates)
        elif all_dates:
            start_date = min(all_dates)
        else:
            start_date = None

        # Determine end date
        if resolution_dates:
            end_date = max(resolution_dates)
        elif all_dates:
            end_date = max(all_dates)
        else:
            end_date = None

        return start_date, end_date

    def _aggregate_contributors(
        self,
        docs: List[Document]
    ) -> List[Dict]:
        """
        Aggregate contributors across documents with scoring.

        Returns list of contributors sorted by contribution score:
        - Authors weighted higher than recipients
        - Technical roles weighted higher
        - Frequency across documents matters
        """
        contributor_scores: Dict[str, Dict] = {}  # name -> {info, score}

        for doc in docs:
            if not doc.temporal_metadata:
                continue

            contributors = doc.temporal_metadata.get("contributors", [])

            for contrib in contributors:
                if isinstance(contrib, dict):
                    name = contrib.get("name", "")
                    title = contrib.get("title")
                    role_type = contrib.get("role_type", "unknown")
                    is_qualified = contrib.get("is_qualified_personnel", False)
                    contrib_type = contrib.get("contribution_type", "mentioned")
                else:
                    # Legacy format - just a name string
                    name = str(contrib)
                    title = None
                    role_type = "unknown"
                    is_qualified = False
                    contrib_type = "mentioned"

                if not name:
                    continue

                # Calculate contribution score for this document
                type_scores = {"author": 10, "attendee": 5, "recipient": 3, "mentioned": 1}
                role_scores = {"technical": 5, "management": 3, "support": 1, "unknown": 2}
                doc_score = type_scores.get(contrib_type, 1) + role_scores.get(role_type, 2)

                if name in contributor_scores:
                    existing = contributor_scores[name]
                    existing["score"] += doc_score
                    existing["doc_count"] += 1
                    # Update with better info
                    if title and not existing.get("title"):
                        existing["title"] = title
                    if is_qualified:
                        existing["is_qualified_personnel"] = True
                    if role_type != "unknown" and existing.get("role_type") == "unknown":
                        existing["role_type"] = role_type
                else:
                    contributor_scores[name] = {
                        "name": name,
                        "title": title,
                        "role_type": role_type,
                        "is_qualified_personnel": is_qualified,
                        "score": doc_score,
                        "doc_count": 1
                    }

        # Sort by score descending
        sorted_contributors = sorted(
            contributor_scores.values(),
            key=lambda c: c["score"],
            reverse=True
        )

        return sorted_contributors[:15]  # Top 15 contributors

    async def _analyze_cluster(
        self,
        docs: List[Document],
        company_id: UUID
    ) -> ProjectCandidate:
        """Analyze a cluster of documents to create project candidate"""
        # Extract SR&ED-relevant dates (uncertainty start, resolution end)
        start_date, end_date = self._extract_sred_dates(docs)

        # Aggregate contributors with titles and roles
        contributors = self._aggregate_contributors(docs)

        # Extract top team members (names only, for backward compatibility)
        top_team = [c["name"] for c in contributors[:10]]

        # Aggregate SR&ED signals
        total_uncertainty = 0
        total_systematic = 0
        total_failure = 0
        total_advancement = 0

        for doc in docs:
            if doc.sred_signals:
                total_uncertainty += doc.sred_signals.get("uncertainty_keywords", 0)
                total_systematic += doc.sred_signals.get("systematic_keywords", 0)
                total_failure += doc.sred_signals.get("failure_keywords", 0)
                total_advancement += doc.sred_signals.get("advancement_keywords", 0)

        # Calculate aggregate SR&ED score
        sred_score = self._calculate_cluster_sred_score(
            total_uncertainty,
            total_systematic,
            total_failure,
            total_advancement,
            len(docs)
        )

        # Generate project name from metadata
        project_name = self._generate_project_name(docs)

        # Generate summary
        summary = self._generate_cluster_summary(docs, sred_score)

        # Calculate confidence
        date_span = 0
        if start_date and end_date:
            if hasattr(start_date, 'date'):
                start_date = start_date.date() if hasattr(start_date, 'date') else start_date
            if hasattr(end_date, 'date'):
                end_date = end_date.date() if hasattr(end_date, 'date') else end_date
            date_span = (end_date - start_date).days

        confidence = self._calculate_confidence(
            cluster_size=len(docs),
            date_span=date_span,
            team_size=len(top_team),
            sred_score=sred_score
        )

        return ProjectCandidate(
            documents=[doc.id for doc in docs],
            name=project_name,
            start_date=datetime.combine(start_date, datetime.min.time()) if start_date else None,
            end_date=datetime.combine(end_date, datetime.min.time()) if end_date else None,
            team_members=top_team,
            contributors=contributors,  # Structured contributor info with titles/roles
            sred_score=sred_score,
            confidence=confidence,
            signals={
                "uncertainty": total_uncertainty,
                "systematic": total_systematic,
                "failure": total_failure,
                "advancement": total_advancement
            },
            summary=summary
        )

    def _calculate_cluster_sred_score(
        self,
        uncertainty: int,
        systematic: int,
        failure: int,
        advancement: int,
        doc_count: int
    ) -> float:
        """Calculate SR&ED score for entire cluster"""
        if doc_count == 0:
            return 0.0

        # Weighted sum
        score = (
            uncertainty * 3.0 +
            systematic * 2.0 +
            failure * 2.5 +
            advancement * 2.0
        ) / (doc_count * 10)  # Normalize by expected signals per doc

        # Must have minimum signals
        if uncertainty < 3 or systematic < 5:
            score *= 0.5

        return min(score, 1.0)

    def _generate_project_name(self, docs: List[Document]) -> str:
        """Generate descriptive project name from documents"""
        # Check for common project names in metadata
        all_project_names = []
        all_jira_codes = []

        for doc in docs:
            if doc.temporal_metadata:
                names = doc.temporal_metadata.get("project_names", [])
                jira = doc.temporal_metadata.get("jira_codes", [])
                all_project_names.extend(names)
                all_jira_codes.extend(jira)

        # Use most common Jira code if available
        if all_jira_codes:
            code_counter = Counter(all_jira_codes)
            most_common = code_counter.most_common(1)[0][0]
            return f"Project {most_common}"

        # Use most common project name if available
        if all_project_names:
            name_counter = Counter(all_project_names)
            most_common = name_counter.most_common(1)[0][0]
            return most_common

        # Fallback: use document type + date range
        doc_types = [doc.document_type for doc in docs if doc.document_type]
        if doc_types:
            type_counter = Counter(doc_types)
            common_type = type_counter.most_common(1)[0][0]
            return f"{common_type.replace('_', ' ').title()} Project"

        return f"Discovered Project ({len(docs)} docs)"

    def _generate_cluster_summary(
        self,
        docs: List[Document],
        sred_score: float
    ) -> str:
        """Generate summary of the project cluster"""
        doc_count = len(docs)
        doc_types = Counter(doc.document_type for doc in docs if doc.document_type)

        # Build summary
        parts = [f"Project with {doc_count} documents"]

        if doc_types:
            type_str = ", ".join(f"{count} {t}" for t, count in doc_types.most_common(3))
            parts.append(f"including {type_str}")

        if sred_score >= 0.7:
            parts.append("with strong SR&ED eligibility indicators")
        elif sred_score >= 0.4:
            parts.append("with moderate SR&ED eligibility indicators")
        else:
            parts.append("with limited SR&ED indicators")

        return ". ".join(parts) + "."

    def _calculate_confidence(
        self,
        cluster_size: int,
        date_span: int,
        team_size: int,
        sred_score: float
    ) -> float:
        """Calculate confidence that this cluster represents a real project"""
        # Size score (sigmoid)
        size_score = 1 / (1 + np.exp(-(cluster_size - 8) / 4))

        # Date span score (projects typically 1-12 months)
        if 30 <= date_span <= 365:
            span_score = 1.0
        elif date_span < 30:
            span_score = max(date_span / 30.0, 0.3)
        else:
            span_score = max(365.0 / date_span, 0.5)

        # Team score
        team_score = min(team_size / 5.0, 1.0)

        # Weighted combination
        confidence = (
            size_score * 0.3 +
            span_score * 0.2 +
            team_score * 0.2 +
            sred_score * 0.3
        )

        return min(confidence, 1.0)

    def _deduplicate_candidates(
        self,
        candidates: List[ProjectCandidate]
    ) -> List[ProjectCandidate]:
        """
        Merge candidates with the same project name.

        If a project appears multiple times (e.g., from name-based and clustering),
        merge them into a single candidate with combined documents.
        """
        # Normalize names for comparison
        name_to_candidates: Dict[str, List[ProjectCandidate]] = {}

        for candidate in candidates:
            # Normalize the project name
            normalized = project_name_normalizer.normalize(candidate.name)
            if not normalized:
                normalized = candidate.name.upper().strip()

            if normalized not in name_to_candidates:
                name_to_candidates[normalized] = []
            name_to_candidates[normalized].append(candidate)

        # Merge duplicates
        merged: List[ProjectCandidate] = []
        for normalized_name, dupes in name_to_candidates.items():
            if len(dupes) == 1:
                merged.append(dupes[0])
            else:
                # Merge multiple candidates into one
                # Prefer name-based over clustering for discovery_source
                primary = dupes[0]
                for dupe in dupes[1:]:
                    if dupe.discovery_source == "name_based" and primary.discovery_source != "name_based":
                        primary = dupe

                # Combine all document IDs (deduplicated)
                all_doc_ids = set()
                all_variations = set()
                for dupe in dupes:
                    all_doc_ids.update(dupe.documents)
                    all_variations.update(dupe.name_variations)

                # Merge contributors (deduplicate by name, combine scores)
                contributor_map: Dict[str, Dict] = {}
                for dupe in dupes:
                    for contrib in dupe.contributors:
                        name = contrib.get("name", "")
                        if name in contributor_map:
                            # Add scores together
                            contributor_map[name]["score"] = (
                                contributor_map[name].get("score", 0) +
                                contrib.get("score", 0)
                            )
                            contributor_map[name]["doc_count"] = (
                                contributor_map[name].get("doc_count", 0) +
                                contrib.get("doc_count", 0)
                            )
                            # Keep better info
                            if contrib.get("title") and not contributor_map[name].get("title"):
                                contributor_map[name]["title"] = contrib["title"]
                            if contrib.get("is_qualified_personnel"):
                                contributor_map[name]["is_qualified_personnel"] = True
                        else:
                            contributor_map[name] = contrib.copy()

                merged_contributors = sorted(
                    contributor_map.values(),
                    key=lambda c: c.get("score", 0),
                    reverse=True
                )[:15]

                # Use the highest confidence score
                best_confidence = max(d.confidence for d in dupes)
                best_sred_score = max(d.sred_score for d in dupes)

                # Create merged candidate
                merged_candidate = ProjectCandidate(
                    documents=list(all_doc_ids),
                    name=primary.name,
                    start_date=min((d.start_date for d in dupes if d.start_date), default=None),
                    end_date=max((d.end_date for d in dupes if d.end_date), default=None),
                    team_members=list(set(m for d in dupes for m in d.team_members)),
                    contributors=merged_contributors,
                    sred_score=best_sred_score,
                    confidence=best_confidence,
                    signals={
                        "uncertainty": sum(d.signals.get("uncertainty", 0) for d in dupes),
                        "systematic": sum(d.signals.get("systematic", 0) for d in dupes),
                        "failure": sum(d.signals.get("failure", 0) for d in dupes),
                        "advancement": sum(d.signals.get("advancement", 0) for d in dupes),
                    },
                    summary=primary.summary,
                    discovery_source=primary.discovery_source,
                    name_variations=list(all_variations)
                )
                merged.append(merged_candidate)

                logger.info(
                    f"Merged {len(dupes)} duplicate candidates for '{normalized_name}' "
                    f"into single project with {len(all_doc_ids)} documents"
                )

        return merged

    def _categorize_candidates(
        self,
        candidates: List[ProjectCandidate]
    ) -> Dict[str, List[ProjectCandidate]]:
        """Categorize candidates by confidence level"""
        high = []
        medium = []
        low = []

        for candidate in candidates:
            if candidate.confidence >= 0.7:
                high.append(candidate)
            elif candidate.confidence >= 0.4:
                medium.append(candidate)
            else:
                low.append(candidate)

        # Sort each category by SR&ED score
        high.sort(key=lambda c: c.sred_score, reverse=True)
        medium.sort(key=lambda c: c.sred_score, reverse=True)
        low.sort(key=lambda c: c.sred_score, reverse=True)

        return {
            "high_confidence": high,
            "medium_confidence": medium,
            "low_confidence": low
        }

    async def _handle_small_dataset(
        self,
        docs: List[Document],
        company_id: UUID
    ) -> Dict:
        """Handle case where too few documents to cluster"""
        if not docs:
            return {
                "high_confidence": [],
                "medium_confidence": [],
                "low_confidence": [],
                "orphan_document_ids": []
            }

        # Treat all docs as one potential project
        candidate = await self._analyze_cluster(docs, company_id)
        candidate.confidence = min(candidate.confidence, 0.5)  # Cap confidence

        return {
            "high_confidence": [],
            "medium_confidence": [candidate],
            "low_confidence": [],
            "orphan_document_ids": []
        }

    async def save_discovered_projects(
        self,
        claim_id: UUID,
        company_id: UUID,
        candidates: List[ProjectCandidate],
        user_id: Optional[UUID] = None
    ) -> List[Project]:
        """
        Save discovered projects to database and create document tags.

        Args:
            claim_id: UUID of the claim
            company_id: Company ID
            candidates: List of ProjectCandidate objects
            user_id: Optional user who triggered discovery

        Returns:
            List of created Project objects
        """
        created_projects = []

        for candidate in candidates:
            # Create Project record
            project = Project(
                claim_id=claim_id,
                company_id=company_id,
                project_name=candidate.name,
                sred_confidence_score=Decimal(str(round(candidate.sred_score, 2))),
                project_status="discovered",
                discovery_method="ai_clustering",
                ai_suggested=True,
                user_confirmed=False,
                project_start_date=candidate.start_date.date() if candidate.start_date else None,
                project_end_date=candidate.end_date.date() if candidate.end_date else None,
                team_members=candidate.team_members,
                team_size=len(candidate.team_members),
                uncertainty_signal_count=candidate.signals.get("uncertainty", 0),
                systematic_signal_count=candidate.signals.get("systematic", 0),
                failure_signal_count=candidate.signals.get("failure", 0),
                advancement_signal_count=candidate.signals.get("advancement", 0),
                ai_summary=candidate.summary,
                created_by=user_id
            )

            self.db.add(project)
            await self.db.flush()  # Get project.id

            # Create document tags
            for doc_id in candidate.documents:
                tag = DocumentProjectTag(
                    document_id=doc_id,
                    project_id=project.id,
                    tagged_by="ai",
                    confidence_score=Decimal(str(round(candidate.confidence, 2))),
                    created_by=user_id
                )
                self.db.add(tag)

            created_projects.append(project)

        await self.db.commit()

        logger.info(f"Saved {len(created_projects)} projects for claim {claim_id}")
        return created_projects


def get_project_discovery_service(db: AsyncSession) -> ProjectDiscoveryService:
    """Factory function to create ProjectDiscoveryService with database session"""
    return ProjectDiscoveryService(db)
