# app/services/change_detection_service.py
"""
Change Detection Service

Analyzes incremental document uploads to detect:
1. Additions to existing projects
2. New potential projects
3. Narrative impacts (contradictions, new evidence)
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass, field
from decimal import Decimal

import numpy as np
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Document, Project, DocumentProjectTag,
    DocumentUploadBatch, Claim, ProjectDiscoveryRun
)
from app.services.vector_storage import vector_storage_service
from app.services.sred_signal_detector import sred_signal_detector
from app.services.entity_extractor import entity_extractor

logger = logging.getLogger(__name__)

# Configuration
SIMILARITY_THRESHOLD_HIGH = 0.80  # High confidence match to existing project
SIMILARITY_THRESHOLD_MEDIUM = 0.60  # Medium confidence match
MIN_DOCS_FOR_NEW_PROJECT = 3  # Minimum docs to form a new project cluster


@dataclass
class ProjectAddition:
    """Documents that should be added to an existing project"""
    project_id: UUID
    project_name: str
    document_ids: List[UUID] = field(default_factory=list)
    confidence: str = "medium"  # high, medium, low
    average_similarity: float = 0.0
    summary: str = ""


@dataclass
class NewProjectCandidate:
    """A new project discovered from new documents"""
    name: str
    document_ids: List[UUID] = field(default_factory=list)
    confidence: float = 0.0
    sred_score: float = 0.0
    summary: str = ""


@dataclass
class NarrativeImpact:
    """Impact on an existing project's narrative"""
    project_id: UUID
    project_name: str
    severity: str  # high, medium, low
    impact_type: str  # contradiction, enhancement, gap, new_evidence
    description: str
    document_ids: List[UUID] = field(default_factory=list)
    affected_line: Optional[int] = None  # T661 line number (242, 244, 246)


@dataclass
class ChangeAnalysisResult:
    """Complete result of change detection analysis"""
    batch_id: UUID
    total_new_documents: int
    additions_to_existing: List[ProjectAddition] = field(default_factory=list)
    new_projects_discovered: List[NewProjectCandidate] = field(default_factory=list)
    narrative_impacts: List[NarrativeImpact] = field(default_factory=list)
    unassigned_document_ids: List[UUID] = field(default_factory=list)


class ChangeDetectionService:
    """
    Analyzes incremental document uploads to detect changes
    and impacts on existing projects.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_upload_batch(
        self,
        claim_id: UUID,
        document_ids: List[UUID],
        user_id: Optional[UUID] = None
    ) -> DocumentUploadBatch:
        """
        Create a new upload batch record for tracking.

        Args:
            claim_id: Claim UUID
            document_ids: List of new document UUIDs
            user_id: User who uploaded

        Returns:
            Created DocumentUploadBatch
        """
        # Get batch number
        batch_count_query = (
            select(func.count(DocumentUploadBatch.id))
            .where(DocumentUploadBatch.claim_id == claim_id)
        )
        result = await self.db.execute(batch_count_query)
        current_count = result.scalar() or 0

        # Get total size of documents
        size_query = (
            select(func.sum(Document.file_size_bytes))
            .where(Document.id.in_(document_ids))
        )
        size_result = await self.db.execute(size_query)
        total_size = size_result.scalar() or 0

        batch = DocumentUploadBatch(
            claim_id=claim_id,
            batch_number=current_count + 1,
            document_count=len(document_ids),
            total_size_bytes=total_size,
            analyzed=False,
            created_by=user_id
        )

        self.db.add(batch)
        await self.db.flush()

        # Update documents with batch ID
        for doc_id in document_ids:
            doc_query = select(Document).where(Document.id == doc_id)
            doc_result = await self.db.execute(doc_query)
            doc = doc_result.scalar()
            if doc:
                doc.upload_batch_id = batch.id

        await self.db.commit()

        logger.info(
            f"Created upload batch {batch.batch_number} for claim {claim_id} "
            f"with {len(document_ids)} documents"
        )

        return batch

    async def analyze_batch_impact(
        self,
        claim_id: UUID,
        company_id: UUID,
        batch_id: Optional[UUID] = None,
        new_document_ids: Optional[List[UUID]] = None
    ) -> ChangeAnalysisResult:
        """
        Analyze impact of new documents on existing projects.

        Args:
            claim_id: Claim UUID
            company_id: Company ID for tenant isolation
            batch_id: Optional batch ID (will use new_document_ids if not provided)
            new_document_ids: Optional list of new document IDs

        Returns:
            ChangeAnalysisResult with additions, new projects, and impacts
        """
        # Get documents to analyze
        if batch_id:
            docs_query = (
                select(Document)
                .where(
                    and_(
                        Document.upload_batch_id == batch_id,
                        Document.processing_status == 'complete'
                    )
                )
            )
            docs_result = await self.db.execute(docs_query)
            new_docs = list(docs_result.scalars().all())
            new_doc_ids = [d.id for d in new_docs]
        elif new_document_ids:
            docs_query = (
                select(Document)
                .where(Document.id.in_(new_document_ids))
            )
            docs_result = await self.db.execute(docs_query)
            new_docs = list(docs_result.scalars().all())
            new_doc_ids = new_document_ids
            batch_id = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder
        else:
            raise ValueError("Either batch_id or new_document_ids must be provided")

        if not new_docs:
            logger.warning(f"No completed documents found for analysis")
            return ChangeAnalysisResult(
                batch_id=batch_id,
                total_new_documents=0
            )

        # Get existing approved/discovered projects
        projects_query = (
            select(Project)
            .where(
                and_(
                    Project.claim_id == claim_id,
                    Project.company_id == company_id,
                    Project.project_status.in_(['approved', 'discovered'])
                )
            )
        )
        projects_result = await self.db.execute(projects_query)
        existing_projects = list(projects_result.scalars().all())

        # Analyze additions to existing projects
        additions, remaining_docs = await self._find_additions_to_existing(
            new_docs, existing_projects, company_id
        )

        # Check for narrative impacts
        narrative_impacts = await self._detect_narrative_impacts(
            new_docs, existing_projects, company_id
        )

        # Discover new projects from remaining documents
        new_projects = await self._discover_new_projects(
            remaining_docs, company_id
        )

        # Calculate unassigned documents
        assigned_to_existing = set()
        for addition in additions:
            assigned_to_existing.update(addition.document_ids)

        assigned_to_new = set()
        for new_proj in new_projects:
            assigned_to_new.update(new_proj.document_ids)

        all_assigned = assigned_to_existing | assigned_to_new
        unassigned = [doc.id for doc in new_docs if doc.id not in all_assigned]

        # Update batch with analysis results
        if batch_id and batch_id != UUID('00000000-0000-0000-0000-000000000000'):
            await self._update_batch_analysis(
                batch_id, additions, new_projects, narrative_impacts
            )

        result = ChangeAnalysisResult(
            batch_id=batch_id,
            total_new_documents=len(new_docs),
            additions_to_existing=additions,
            new_projects_discovered=new_projects,
            narrative_impacts=narrative_impacts,
            unassigned_document_ids=unassigned
        )

        logger.info(
            f"Change analysis complete: {len(additions)} additions to existing, "
            f"{len(new_projects)} new projects, {len(narrative_impacts)} narrative impacts, "
            f"{len(unassigned)} unassigned"
        )

        return result

    async def _find_additions_to_existing(
        self,
        new_docs: List[Document],
        existing_projects: List[Project],
        company_id: UUID
    ) -> Tuple[List[ProjectAddition], List[Document]]:
        """
        Find which new documents should be added to existing projects.

        Uses semantic similarity between new document embeddings and
        existing project document embeddings.

        Returns:
            (list of ProjectAddition, list of remaining unmatched documents)
        """
        if not existing_projects:
            return [], new_docs

        additions = []
        remaining_docs = []

        # Get embeddings for existing project documents
        project_embeddings: Dict[UUID, np.ndarray] = {}
        for project in existing_projects:
            # Get document IDs for this project
            tags_query = (
                select(DocumentProjectTag.document_id)
                .where(DocumentProjectTag.project_id == project.id)
            )
            tags_result = await self.db.execute(tags_query)
            doc_ids = [r[0] for r in tags_result.fetchall()]

            if not doc_ids:
                continue

            # Get average embedding for project
            project_emb = await self._get_project_embedding(doc_ids, company_id)
            if project_emb is not None:
                project_embeddings[project.id] = project_emb

        if not project_embeddings:
            return [], new_docs

        # For each new document, find best matching project
        doc_assignments: Dict[UUID, List[Tuple[Document, float]]] = {
            p.id: [] for p in existing_projects
        }

        for doc in new_docs:
            # Get document embedding
            doc_emb = await self._get_document_embedding(doc.id, company_id)
            if doc_emb is None:
                remaining_docs.append(doc)
                continue

            # Find best matching project
            best_project_id = None
            best_similarity = 0.0

            for proj_id, proj_emb in project_embeddings.items():
                similarity = self._cosine_similarity(doc_emb, proj_emb)
                if similarity > best_similarity and similarity >= SIMILARITY_THRESHOLD_MEDIUM:
                    best_similarity = similarity
                    best_project_id = proj_id

            if best_project_id:
                doc_assignments[best_project_id].append((doc, best_similarity))
            else:
                remaining_docs.append(doc)

        # Create ProjectAddition objects
        for project in existing_projects:
            assigned = doc_assignments.get(project.id, [])
            if not assigned:
                continue

            doc_ids = [d.id for d, _ in assigned]
            similarities = [s for _, s in assigned]
            avg_sim = sum(similarities) / len(similarities)

            # Determine confidence level
            if avg_sim >= SIMILARITY_THRESHOLD_HIGH:
                confidence = "high"
            elif avg_sim >= SIMILARITY_THRESHOLD_MEDIUM:
                confidence = "medium"
            else:
                confidence = "low"

            additions.append(ProjectAddition(
                project_id=project.id,
                project_name=project.project_name,
                document_ids=doc_ids,
                confidence=confidence,
                average_similarity=avg_sim,
                summary=f"Found {len(doc_ids)} documents with {avg_sim:.0%} average similarity"
            ))

        return additions, remaining_docs

    async def _detect_narrative_impacts(
        self,
        new_docs: List[Document],
        existing_projects: List[Project],
        company_id: UUID
    ) -> List[NarrativeImpact]:
        """
        Detect potential impacts on existing narratives.

        Looks for:
        - Contradictions to existing narrative claims
        - New evidence that strengthens narratives
        - Gaps that need to be addressed
        """
        impacts = []

        # Only check projects that have narratives
        projects_with_narratives = [
            p for p in existing_projects
            if p.narrative_line_242 or p.narrative_line_244 or p.narrative_line_246
        ]

        if not projects_with_narratives:
            return impacts

        for project in projects_with_narratives:
            # Find new documents that match this project
            tags_query = (
                select(DocumentProjectTag)
                .where(
                    and_(
                        DocumentProjectTag.project_id == project.id,
                        DocumentProjectTag.document_id.in_([d.id for d in new_docs])
                    )
                )
            )
            tags_result = await self.db.execute(tags_query)
            new_doc_tags = list(tags_result.scalars().all())

            if not new_doc_tags:
                # Check if any new docs have high similarity to this project
                matching_docs = await self._find_matching_docs_for_project(
                    new_docs, project.id, company_id
                )
                if not matching_docs:
                    continue
                new_doc_ids = matching_docs
            else:
                new_doc_ids = [t.document_id for t in new_doc_tags]

            # Get the new documents
            new_project_docs_query = (
                select(Document)
                .where(Document.id.in_(new_doc_ids))
            )
            new_project_docs_result = await self.db.execute(new_project_docs_query)
            new_project_docs = list(new_project_docs_result.scalars().all())

            # Analyze for potential impacts
            for doc in new_project_docs:
                if not doc.extracted_text:
                    continue

                text_lower = doc.extracted_text.lower()

                # Check for contradiction indicators
                contradiction_phrases = [
                    "actually", "in fact", "contrary to",
                    "we borrowed", "we adapted", "based on",
                    "open source", "third party", "existing solution"
                ]

                has_contradiction_indicator = any(
                    phrase in text_lower for phrase in contradiction_phrases
                )

                # Check if doc mentions routine work (potential contradiction)
                routine_phrases = [
                    "standard approach", "routine implementation",
                    "well-known", "common practice", "straightforward"
                ]
                has_routine_indicator = any(
                    phrase in text_lower for phrase in routine_phrases
                )

                if has_contradiction_indicator and project.narrative_line_246:
                    # Potential contradiction to advancement claims
                    impacts.append(NarrativeImpact(
                        project_id=project.id,
                        project_name=project.project_name,
                        severity="high" if "open source" in text_lower or "adapted" in text_lower else "medium",
                        impact_type="contradiction",
                        description=(
                            f"Document '{doc.document_title}' may contain information "
                            f"that contradicts advancement claims in the narrative. "
                            f"Review recommended."
                        ),
                        document_ids=[doc.id],
                        affected_line=246
                    ))

                elif has_routine_indicator and project.narrative_line_242:
                    # Potential contradiction to uncertainty claims
                    impacts.append(NarrativeImpact(
                        project_id=project.id,
                        project_name=project.project_name,
                        severity="medium",
                        impact_type="contradiction",
                        description=(
                            f"Document '{doc.document_title}' contains phrases suggesting "
                            f"routine work, which may conflict with uncertainty claims."
                        ),
                        document_ids=[doc.id],
                        affected_line=242
                    ))

                # Check for new evidence (positive impact)
                elif doc.sred_signals and doc.sred_signals.get('score', 0) > 0.6:
                    impacts.append(NarrativeImpact(
                        project_id=project.id,
                        project_name=project.project_name,
                        severity="low",
                        impact_type="enhancement",
                        description=(
                            f"Document '{doc.document_title}' provides additional "
                            f"SR&ED evidence that could strengthen the narrative."
                        ),
                        document_ids=[doc.id],
                        affected_line=None
                    ))

        return impacts

    async def _discover_new_projects(
        self,
        remaining_docs: List[Document],
        company_id: UUID
    ) -> List[NewProjectCandidate]:
        """
        Discover new potential projects from unassigned documents.

        Uses simplified clustering when enough documents are available.
        """
        if len(remaining_docs) < MIN_DOCS_FOR_NEW_PROJECT:
            return []

        try:
            from sklearn.cluster import AgglomerativeClustering
        except ImportError:
            logger.warning("sklearn not available for clustering")
            return []

        # Get embeddings for remaining documents
        doc_embeddings = []
        valid_docs = []

        for doc in remaining_docs:
            emb = await self._get_document_embedding(doc.id, company_id)
            if emb is not None:
                doc_embeddings.append(emb[:50])  # Use first 50 dims
                valid_docs.append(doc)

        if len(valid_docs) < MIN_DOCS_FOR_NEW_PROJECT:
            return []

        # Cluster documents
        X = np.array(doc_embeddings)

        # Use agglomerative clustering with distance threshold
        n_clusters = max(1, len(valid_docs) // 5)  # Roughly 5 docs per cluster
        clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        labels = clusterer.fit_predict(X)

        # Group documents by cluster
        clusters: Dict[int, List[Document]] = {}
        for doc, label in zip(valid_docs, labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(doc)

        # Create candidates from clusters with enough documents
        candidates = []
        for label, cluster_docs in clusters.items():
            if len(cluster_docs) < MIN_DOCS_FOR_NEW_PROJECT:
                continue

            # Calculate SR&ED score for cluster
            total_score = 0.0
            doc_with_signals = 0
            for doc in cluster_docs:
                if doc.sred_signals and 'score' in doc.sred_signals:
                    total_score += doc.sred_signals['score']
                    doc_with_signals += 1

            avg_sred_score = total_score / doc_with_signals if doc_with_signals > 0 else 0.3

            # Generate project name from metadata
            name = self._generate_cluster_name(cluster_docs)

            candidates.append(NewProjectCandidate(
                name=name,
                document_ids=[d.id for d in cluster_docs],
                confidence=avg_sred_score,
                sred_score=avg_sred_score,
                summary=f"New project with {len(cluster_docs)} documents, SR&ED score {avg_sred_score:.2f}"
            ))

        return candidates

    def _generate_cluster_name(self, docs: List[Document]) -> str:
        """Generate a name for a document cluster"""
        # Try to extract project names from metadata
        project_names = []
        jira_codes = []

        for doc in docs:
            if doc.temporal_metadata:
                names = doc.temporal_metadata.get('project_names', [])
                jira = doc.temporal_metadata.get('jira_codes', [])
                project_names.extend(names)
                jira_codes.extend(jira)

        if jira_codes:
            from collections import Counter
            most_common = Counter(jira_codes).most_common(1)[0][0]
            return f"Project {most_common}"

        if project_names:
            from collections import Counter
            most_common = Counter(project_names).most_common(1)[0][0]
            return most_common

        # Fallback based on document types
        doc_types = [d.document_type for d in docs if d.document_type]
        if doc_types:
            from collections import Counter
            common_type = Counter(doc_types).most_common(1)[0][0]
            return f"New {common_type.replace('_', ' ').title()} Project"

        return f"New Project ({len(docs)} documents)"

    async def _get_project_embedding(
        self,
        document_ids: List[UUID],
        company_id: UUID
    ) -> Optional[np.ndarray]:
        """Get average embedding for a set of documents"""
        embeddings = []
        for doc_id in document_ids[:10]:  # Limit to first 10 docs for efficiency
            emb = await self._get_document_embedding(doc_id, company_id)
            if emb is not None:
                embeddings.append(emb)

        if not embeddings:
            return None

        return np.mean(embeddings, axis=0)

    async def _get_document_embedding(
        self,
        document_id: UUID,
        company_id: UUID
    ) -> Optional[np.ndarray]:
        """Get average embedding for a document's chunks"""
        try:
            embeddings_data = await vector_storage_service.get_embeddings(
                document_id=document_id,
                company_id=company_id
            )

            if not embeddings_data:
                return None

            # Average first 3 chunks
            embeddings = [np.array(e["embedding"]) for e in embeddings_data[:3]]
            return np.mean(embeddings, axis=0)

        except Exception as e:
            logger.warning(f"Error getting embedding for doc {document_id}: {e}")
            return None

    async def _find_matching_docs_for_project(
        self,
        new_docs: List[Document],
        project_id: UUID,
        company_id: UUID
    ) -> List[UUID]:
        """Find documents from new_docs that match a project"""
        # Get project embedding
        tags_query = (
            select(DocumentProjectTag.document_id)
            .where(DocumentProjectTag.project_id == project_id)
        )
        tags_result = await self.db.execute(tags_query)
        existing_doc_ids = [r[0] for r in tags_result.fetchall()]

        if not existing_doc_ids:
            return []

        project_emb = await self._get_project_embedding(existing_doc_ids, company_id)
        if project_emb is None:
            return []

        matching = []
        for doc in new_docs:
            doc_emb = await self._get_document_embedding(doc.id, company_id)
            if doc_emb is None:
                continue

            similarity = self._cosine_similarity(doc_emb, project_emb)
            if similarity >= SIMILARITY_THRESHOLD_MEDIUM:
                matching.append(doc.id)

        return matching

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    async def _update_batch_analysis(
        self,
        batch_id: UUID,
        additions: List[ProjectAddition],
        new_projects: List[NewProjectCandidate],
        impacts: List[NarrativeImpact]
    ) -> None:
        """Update batch record with analysis results"""
        batch_query = select(DocumentUploadBatch).where(DocumentUploadBatch.id == batch_id)
        batch_result = await self.db.execute(batch_query)
        batch = batch_result.scalar()

        if batch:
            batch.analyzed = True
            batch.impact_summary = {
                "additions_count": len(additions),
                "additions": [
                    {
                        "project_id": str(a.project_id),
                        "project_name": a.project_name,
                        "document_count": len(a.document_ids),
                        "confidence": a.confidence
                    }
                    for a in additions
                ],
                "new_projects_count": len(new_projects),
                "new_projects": [
                    {
                        "name": p.name,
                        "document_count": len(p.document_ids),
                        "confidence": p.confidence
                    }
                    for p in new_projects
                ],
                "narrative_impacts_count": len(impacts),
                "narrative_impacts": [
                    {
                        "project_id": str(i.project_id),
                        "project_name": i.project_name,
                        "severity": i.severity,
                        "type": i.impact_type
                    }
                    for i in impacts
                ]
            }
            await self.db.commit()

    async def apply_additions(
        self,
        additions: List[ProjectAddition],
        user_id: Optional[UUID] = None
    ) -> int:
        """
        Apply document additions to existing projects.

        Args:
            additions: List of ProjectAddition objects
            user_id: User making the addition

        Returns:
            Number of tags created
        """
        tags_created = 0

        for addition in additions:
            for doc_id in addition.document_ids:
                # Check if tag already exists
                existing_query = (
                    select(DocumentProjectTag)
                    .where(
                        and_(
                            DocumentProjectTag.document_id == doc_id,
                            DocumentProjectTag.project_id == addition.project_id
                        )
                    )
                )
                existing_result = await self.db.execute(existing_query)
                if existing_result.scalar():
                    continue

                tag = DocumentProjectTag(
                    document_id=doc_id,
                    project_id=addition.project_id,
                    tagged_by='ai',
                    confidence_score=Decimal(str(round(addition.average_similarity, 2))),
                    created_by=user_id
                )
                self.db.add(tag)
                tags_created += 1

        await self.db.commit()
        logger.info(f"Applied {tags_created} document tags from {len(additions)} additions")

        return tags_created


def get_change_detection_service(db: AsyncSession) -> ChangeDetectionService:
    """Factory function to create ChangeDetectionService"""
    return ChangeDetectionService(db)
