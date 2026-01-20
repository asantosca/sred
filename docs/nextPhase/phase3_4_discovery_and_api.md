# Phase 3 & 4: Project Discovery Algorithm + API Integration

## Overview

Build the core project discovery service that automatically clusters documents into potential SR&ED projects, then expose via FastAPI endpoints.

## Phase 3: Project Discovery Algorithm

### File Location

Create: `backend/app/services/project_discovery_service.py`

### Implementation

```python
# backend/app/services/project_discovery_service.py

from typing import List, Dict, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from sklearn.cluster import DBSCAN, HDBSCAN
from sklearn.preprocessing import StandardScaler
from collections import defaultdict, Counter

from app.models.models import (
    Document, Project, ProjectDiscoveryRun, 
    DocumentProjectTag, Claim
)
from app.services.embeddings import EmbeddingsService
from app.core.database import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class ProjectCandidate:
    """Discovered project candidate"""
    documents: List[UUID]
    name: str
    start_date: datetime
    end_date: datetime
    team_members: List[str]
    sred_score: float
    confidence: float
    signals: Dict[str, int]
    summary: str


class ProjectDiscoveryService:
    """
    Automatically discover SR&ED projects from unorganized documents.
    
    Uses multi-dimensional clustering:
    1. Temporal clustering (when work happened)
    2. Semantic clustering (what work was about)
    3. Team clustering (who did the work)
    """
    
    def __init__(self, embeddings_service: EmbeddingsService):
        self.embeddings_service = embeddings_service
    
    async def discover_projects(
        self,
        claim_id: UUID,
        db: AsyncSession
    ) -> Dict[str, List[ProjectCandidate]]:
        """
        Main entry point: discover projects for a claim.
        
        Returns:
            {
                "high_confidence": [ProjectCandidate, ...],
                "medium_confidence": [...],
                "low_confidence": [...]
            }
        """
        # Start discovery run tracking
        run = ProjectDiscoveryRun(
            claim_id=claim_id,
            status="running",
            discovery_algorithm="temporal_semantic_team_clustering"
        )
        db.add(run)
        await db.flush()
        
        start_time = datetime.utcnow()
        
        try:
            # 1. Fetch all documents for this claim
            docs = await self._fetch_documents(claim_id, db)
            
            if len(docs) < 5:
                # Too few documents to cluster meaningfully
                return self._handle_small_dataset(docs, db)
            
            # 2. Perform multi-dimensional clustering
            clusters = await self._cluster_documents(docs, db)
            
            # 3. Score each cluster for SR&ED likelihood
            candidates = []
            for cluster_docs in clusters:
                candidate = await self._analyze_cluster(cluster_docs, db)
                candidates.append(candidate)
            
            # 4. Rank and categorize
            categorized = self._categorize_candidates(candidates)
            
            # 5. Save discovery run results
            run.status = "completed"
            run.total_documents_analyzed = len(docs)
            run.projects_discovered = len(candidates)
            run.high_confidence_count = len(categorized["high_confidence"])
            run.medium_confidence_count = len(categorized["medium_confidence"])
            run.low_confidence_count = len(categorized["low_confidence"])
            run.execution_time_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            await db.commit()
            
            return categorized
            
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            await db.commit()
            raise
    
    async def _fetch_documents(
        self,
        claim_id: UUID,
        db: AsyncSession
    ) -> List[Document]:
        """Fetch all processed documents for claim"""
        query = select(Document).where(
            and_(
                Document.claim_id == claim_id,
                Document.processing_status == "complete",
                Document.indexed_for_search == True
            )
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _cluster_documents(
        self,
        docs: List[Document],
        db: AsyncSession
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
        for doc in docs:
            temporal_features = self._extract_temporal_features(doc)
            semantic_features = await self._extract_semantic_features(doc, db)
            team_features = self._extract_team_features(doc)
            
            # Concatenate all features
            combined = np.concatenate([
                temporal_features,
                semantic_features,
                team_features
            ])
            features.append(combined)
        
        # Convert to numpy array
        X = np.array(features)
        
        # Normalize features
        scaler = StandardScaler()
        X_normalized = scaler.fit_transform(X)
        
        # Apply HDBSCAN (better for variable cluster sizes)
        clusterer = HDBSCAN(
            min_cluster_size=3,  # Minimum 3 documents per project
            min_samples=2,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        
        cluster_labels = clusterer.fit_predict(X_normalized)
        
        # Group documents by cluster
        clusters = defaultdict(list)
        for doc, label in zip(docs, cluster_labels):
            if label != -1:  # -1 = noise (unclustered)
                clusters[label].append(doc)
        
        # Return as list of document lists
        return list(clusters.values())
    
    def _extract_temporal_features(self, doc: Document) -> np.ndarray:
        """
        Extract temporal features from document.
        
        Features:
        - Document date as days since epoch
        - Month (cyclical encoding)
        - Day of week (cyclical encoding)
        """
        if not doc.document_date:
            # Use upload date if no document date
            date = doc.created_at
        else:
            date = datetime.combine(doc.document_date, datetime.min.time())
        
        # Days since epoch (normalized)
        days_since_epoch = (date - datetime(1970, 1, 1)).days / 365.0
        
        # Cyclical month encoding (sin/cos)
        month = date.month
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)
        
        # Cyclical day of week encoding
        dow = date.weekday()
        dow_sin = np.sin(2 * np.pi * dow / 7)
        dow_cos = np.cos(2 * np.pi * dow / 7)
        
        return np.array([days_since_epoch, month_sin, month_cos, dow_sin, dow_cos])
    
    async def _extract_semantic_features(
        self,
        doc: Document,
        db: AsyncSession
    ) -> np.ndarray:
        """
        Get document's semantic embedding.
        
        Options:
        1. Use average of chunk embeddings (if exists)
        2. Generate new embedding for document title/summary
        """
        # Fetch first few chunks' embeddings and average them
        query = select(DocumentChunk.embedding).where(
            DocumentChunk.document_id == doc.id
        ).limit(5)  # First 5 chunks
        
        result = await db.execute(query)
        embeddings = result.scalars().all()
        
        if embeddings:
            # Average the embeddings
            avg_embedding = np.mean([np.array(emb) for emb in embeddings], axis=0)
            return avg_embedding
        else:
            # Fallback: generate from title or return zeros
            if doc.document_title:
                embedding = await self.embeddings_service.get_embedding(doc.document_title)
                return np.array(embedding)
            else:
                # Return zero vector (1536 dimensions for text-embedding-3-small)
                return np.zeros(1536)
    
    def _extract_team_features(self, doc: Document) -> np.ndarray:
        """
        Encode team membership as features.
        
        Simple approach: one-hot encoding of top team members.
        Better approach: use entity embeddings.
        
        For simplicity, we'll use a hash-based approach.
        """
        team_members = doc.temporal_metadata.get("team_members", []) if doc.temporal_metadata else []
        
        # Create feature vector based on team member presence
        # Use 10 hash buckets to represent team composition
        team_vector = np.zeros(10)
        
        for member in team_members:
            # Hash member name to bucket
            bucket = hash(member) % 10
            team_vector[bucket] = 1
        
        return team_vector
    
    async def _analyze_cluster(
        self,
        docs: List[Document],
        db: AsyncSession
    ) -> ProjectCandidate:
        """
        Analyze a cluster of documents to create project candidate.
        """
        # Aggregate temporal info
        dates = [
            d.document_date or d.created_at.date() 
            for d in docs if d.document_date or d.created_at
        ]
        start_date = min(dates) if dates else None
        end_date = max(dates) if dates else None
        
        # Aggregate team info
        all_team_members = []
        for doc in docs:
            members = doc.temporal_metadata.get("team_members", []) if doc.temporal_metadata else []
            all_team_members.extend(members)
        
        # Count frequency
        team_counter = Counter(all_team_members)
        top_team = [name for name, _ in team_counter.most_common(10)]
        
        # Aggregate SR&ED signals
        total_uncertainty = sum(
            doc.sred_signals.get("uncertainty_keywords", 0) 
            for doc in docs if doc.sred_signals
        )
        total_systematic = sum(
            doc.sred_signals.get("systematic_keywords", 0) 
            for doc in docs if doc.sred_signals
        )
        total_failure = sum(
            doc.sred_signals.get("failure_keywords", 0) 
            for doc in docs if doc.sred_signals
        )
        total_advancement = sum(
            doc.sred_signals.get("novel_keywords", 0) 
            for doc in docs if doc.sred_signals
        )
        
        # Calculate aggregate SR&ED score
        sred_score = self._calculate_cluster_sred_score(
            total_uncertainty,
            total_systematic,
            total_failure,
            total_advancement,
            len(docs)
        )
        
        # Generate project name
        project_name = await self._generate_project_name(docs, db)
        
        # Generate summary
        summary = await self._generate_cluster_summary(docs, db)
        
        # Calculate confidence (how confident are we this is a real project?)
        confidence = self._calculate_confidence(
            cluster_size=len(docs),
            date_span=(end_date - start_date).days if start_date and end_date else 0,
            team_size=len(top_team),
            sred_score=sred_score
        )
        
        return ProjectCandidate(
            documents=[doc.id for doc in docs],
            name=project_name,
            start_date=start_date,
            end_date=end_date,
            team_members=top_team,
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
    
    async def _generate_project_name(
        self,
        docs: List[Document],
        db: AsyncSession
    ) -> str:
        """
        Generate descriptive project name from documents.
        
        Strategy:
        1. Look for common project names in metadata
        2. Use AI to generate from document titles
        3. Fallback to generic name
        """
        # Check for common project names in metadata
        all_project_names = []
        for doc in docs:
            names = doc.temporal_metadata.get("project_names", []) if doc.temporal_metadata else []
            all_project_names.extend(names)
        
        if all_project_names:
            # Use most common project name
            name_counter = Counter(all_project_names)
            most_common = name_counter.most_common(1)[0][0]
            return most_common
        
        # Fallback: use AI to generate from titles
        titles = [doc.document_title for doc in docs[:5] if doc.document_title]
        if titles:
            # Call Claude API to generate name
            prompt = f"""
            Based on these document titles, generate a concise project name (max 4 words):
            
            {chr(10).join(f"- {t}" for t in titles)}
            
            Return only the project name, nothing else.
            """
            
            # (Assume anthropic client is available)
            from anthropic import Anthropic
            client = Anthropic()  # Uses ANTHROPIC_API_KEY env var
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
        
        # Ultimate fallback
        return f"Project {docs[0].id.hex[:8]}"
    
    async def _generate_cluster_summary(
        self,
        docs: List[Document],
        db: AsyncSession
    ) -> str:
        """
        Generate AI summary of what this project is about and why it's SR&ED eligible.
        """
        # Get representative chunks from cluster
        sample_docs = docs[:3]  # First 3 docs
        
        context_parts = []
        for doc in sample_docs:
            if doc.ai_summary:
                context_parts.append(f"Document: {doc.filename}\n{doc.ai_summary}")
            elif doc.extracted_text:
                # Use first 500 chars
                context_parts.append(f"Document: {doc.filename}\n{doc.extracted_text[:500]}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""
        Analyze these documents from a potential SR&ED project:
        
        {context}
        
        Write a 2-3 sentence summary that explains:
        1. What technological uncertainty they faced
        2. What work they performed
        3. Why this appears eligible for SR&ED
        
        Be specific and reference the evidence.
        """
        
        from anthropic import Anthropic
        client = Anthropic()
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text.strip()
    
    def _calculate_confidence(
        self,
        cluster_size: int,
        date_span: int,
        team_size: int,
        sred_score: float
    ) -> float:
        """
        Calculate confidence that this cluster represents a real project.
        
        Factors:
        - Cluster size (more docs = more confident)
        - Date span (projects should span time)
        - Team size (consistent team = real project)
        - SR&ED score (higher = more likely eligible)
        """
        # Size score (sigmoid)
        size_score = 1 / (1 + np.exp(-(cluster_size - 10) / 5))
        
        # Date span score (projects typically 1-12 months)
        if 30 <= date_span <= 365:
            span_score = 1.0
        elif date_span < 30:
            span_score = date_span / 30.0
        else:
            span_score = 365.0 / date_span
        
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
    
    def _categorize_candidates(
        self,
        candidates: List[ProjectCandidate]
    ) -> Dict[str, List[ProjectCandidate]]:
        """Categorize candidates by confidence"""
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
    
    def _handle_small_dataset(
        self,
        docs: List[Document],
        db: AsyncSession
    ) -> Dict[str, List[ProjectCandidate]]:
        """Handle case where too few documents to cluster"""
        # Treat all docs as one potential project
        if len(docs) == 0:
            return {
                "high_confidence": [],
                "medium_confidence": [],
                "low_confidence": []
            }
        
        # Create single candidate
        candidate = await self._analyze_cluster(docs, db)
        
        # Low confidence since we couldn't cluster
        candidate.confidence = min(candidate.confidence, 0.5)
        
        return {
            "high_confidence": [],
            "medium_confidence": [candidate],
            "low_confidence": []
        }
    
    async def save_discovered_projects(
        self,
        claim_id: UUID,
        candidates: List[ProjectCandidate],
        db: AsyncSession
    ) -> List[Project]:
        """
        Save discovered projects to database and create document tags.
        """
        created_projects = []
        
        for candidate in candidates:
            # Create Project record
            project = Project(
                claim_id=claim_id,
                company_id=(await db.get(Claim, claim_id)).company_id,
                project_name=candidate.name,
                sred_confidence_score=candidate.sred_score,
                project_status="discovered",
                discovery_method="ai_clustering",
                ai_suggested=True,
                user_confirmed=False,
                project_start_date=candidate.start_date,
                project_end_date=candidate.end_date,
                team_members=candidate.team_members,
                uncertainty_signal_count=candidate.signals["uncertainty"],
                systematic_signal_count=candidate.signals["systematic"],
                failure_signal_count=candidate.signals["failure"],
                advancement_signal_count=candidate.signals["advancement"],
                ai_summary=candidate.summary
            )
            
            db.add(project)
            await db.flush()  # Get project.id
            
            # Create document tags
            for doc_id in candidate.documents:
                tag = DocumentProjectTag(
                    document_id=doc_id,
                    project_id=project.id,
                    tagged_by="ai",
                    confidence_score=candidate.confidence
                )
                db.add(tag)
            
            created_projects.append(project)
        
        await db.commit()
        return created_projects
```

## Phase 4: FastAPI Endpoints

### File Location

Create: `backend/app/api/v1/endpoints/projects.py`

### Implementation

```python
# backend/app/api/v1/endpoints/projects.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, Project, Claim, DocumentProjectTag
from app.schemas.project import (
    ProjectResponse, ProjectCreate, ProjectUpdate,
    ProjectDiscoveryResponse, ProjectListResponse
)
from app.services.project_discovery_service import ProjectDiscoveryService
from app.services.embeddings import EmbeddingsService
from sqlalchemy import select, and_

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/discover")
async def discover_projects(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run project discovery for a claim.
    
    This automatically clusters documents and identifies potential SR&ED projects.
    """
    # Verify claim exists and user has access
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # TODO: Check user permissions (company_id match)
    
    # Run discovery
    embeddings_service = EmbeddingsService()
    discovery_service = ProjectDiscoveryService(embeddings_service)
    
    results = await discovery_service.discover_projects(claim_id, db)
    
    # Save projects
    all_candidates = (
        results["high_confidence"] +
        results["medium_confidence"] +
        results["low_confidence"]
    )
    
    saved_projects = await discovery_service.save_discovered_projects(
        claim_id,
        all_candidates,
        db
    )
    
    return {
        "status": "completed",
        "claim_id": str(claim_id),
        "projects_discovered": len(saved_projects),
        "high_confidence": len(results["high_confidence"]),
        "medium_confidence": len(results["medium_confidence"]),
        "low_confidence": len(results["low_confidence"]),
        "projects": [
            ProjectResponse.from_orm(p) for p in saved_projects
        ]
    }


@router.get("/claim/{claim_id}")
async def list_projects_for_claim(
    claim_id: UUID,
    status: str = None,  # Filter by status
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all projects for a claim"""
    query = select(Project).where(Project.claim_id == claim_id)
    
    if status:
        query = query.where(Project.project_status == status)
    
    query = query.order_by(Project.sred_confidence_score.desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return {
        "claim_id": str(claim_id),
        "total_projects": len(projects),
        "projects": [ProjectResponse.from_orm(p) for p in projects]
    }


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project details"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get document count
    doc_count_query = select(func.count(DocumentProjectTag.id)).where(
        DocumentProjectTag.project_id == project_id
    )
    result = await db.execute(doc_count_query)
    doc_count = result.scalar()
    
    response = ProjectResponse.from_orm(project)
    response.document_count = doc_count
    
    return response


@router.patch("/{project_id}")
async def update_project(
    project_id: UUID,
    updates: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project (name, status, etc.)"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Apply updates
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    project.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse.from_orm(project)


@router.post("/{project_id}/approve")
async def approve_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve AI-discovered project"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.project_status = "approved"
    project.user_confirmed = True
    project.updated_by = current_user.id
    
    await db.commit()
    
    return {"status": "approved", "project_id": str(project_id)}


@router.post("/{project_id}/reject")
async def reject_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject AI-discovered project"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.project_status = "rejected"
    project.updated_by = current_user.id
    
    await db.commit()
    
    return {"status": "rejected", "project_id": str(project_id)}


@router.post("/{project_id}/documents/add")
async def add_documents_to_project(
    project_id: UUID,
    document_ids: List[UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually add documents to project"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create tags
    added = 0
    for doc_id in document_ids:
        # Check if tag already exists
        existing = await db.execute(
            select(DocumentProjectTag).where(
                and_(
                    DocumentProjectTag.document_id == doc_id,
                    DocumentProjectTag.project_id == project_id
                )
            )
        )
        if existing.scalar():
            continue  # Already tagged
        
        tag = DocumentProjectTag(
            document_id=doc_id,
            project_id=project_id,
            tagged_by="user",
            created_by=current_user.id
        )
        db.add(tag)
        added += 1
    
    await db.commit()
    
    return {"documents_added": added}


@router.delete("/{project_id}/documents/{document_id}")
async def remove_document_from_project(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove document from project"""
    # Find and delete tag
    tag_query = select(DocumentProjectTag).where(
        and_(
            DocumentProjectTag.document_id == document_id,
            DocumentProjectTag.project_id == project_id
        )
    )
    result = await db.execute(tag_query)
    tag = result.scalar()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Document not in project")
    
    await db.delete(tag)
    await db.commit()
    
    return {"status": "removed"}


@router.get("/{project_id}/documents")
async def list_project_documents(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all documents in a project"""
    # Join tags and documents
    query = (
        select(Document, DocumentProjectTag.confidence_score, DocumentProjectTag.tagged_by)
        .join(DocumentProjectTag, Document.id == DocumentProjectTag.document_id)
        .where(DocumentProjectTag.project_id == project_id)
        .order_by(DocumentProjectTag.confidence_score.desc().nullslast())
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    documents = []
    for doc, confidence, tagged_by in rows:
        doc_dict = DocumentResponse.from_orm(doc).dict()
        doc_dict["tag_confidence"] = float(confidence) if confidence else None
        doc_dict["tagged_by"] = tagged_by
        documents.append(doc_dict)
    
    return {
        "project_id": str(project_id),
        "total_documents": len(documents),
        "documents": documents
    }


# Include in main API router
# backend/app/api/v1/api.py
from app.api.v1.endpoints import projects

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/v1")
```

## Pydantic Schemas

Create: `backend/app/schemas/project.py`

```python
from pydantic import BaseModel, UUID4
from datetime import datetime, date
from typing import List, Optional, Dict

class ProjectBase(BaseModel):
    project_name: str
    project_code: Optional[str] = None
    project_start_date: Optional[date] = None
    project_end_date: Optional[date] = None


class ProjectCreate(ProjectBase):
    claim_id: UUID4


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_status: Optional[str] = None
    narrative_line_242: Optional[str] = None
    narrative_line_244: Optional[str] = None
    narrative_line_246: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: UUID4
    claim_id: UUID4
    company_id: UUID4
    sred_confidence_score: Optional[float] = None
    project_status: str
    ai_suggested: bool
    user_confirmed: bool
    team_members: Optional[List[str]] = []
    uncertainty_signal_count: int = 0
    systematic_signal_count: int = 0
    failure_signal_count: int = 0
    advancement_signal_count: int = 0
    ai_summary: Optional[str] = None
    narrative_status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

## Testing

```python
# backend/tests/test_project_discovery.py

import pytest
from app.services.project_discovery_service import ProjectDiscoveryService
from app.models.models import Document, Claim

@pytest.mark.asyncio
async def test_project_discovery(db_session):
    # Create test claim
    claim = Claim(company_id=..., fiscal_year_end=...)
    db_session.add(claim)
    
    # Create test documents with different temporal/semantic features
    # ... (create 20+ documents across 3 "projects")
    
    # Run discovery
    service = ProjectDiscoveryService(embeddings_service)
    results = await service.discover_projects(claim.id, db_session)
    
    # Should discover ~3 projects
    assert len(results["high_confidence"]) >= 2
    assert len(results["high_confidence"]) <= 4
```

## Deployment Checklist

1. ✅ Run Phase 1 migration (database schema)
2. ✅ Deploy Phase 2 (SR&ED detection)
3. ✅ Install sklearn: `pip install scikit-learn hdbscan`
4. ✅ Test discovery on sample claim
5. ✅ Add API endpoints to router
6. ✅ Update frontend to call `/projects/discover`

## Next: Frontend Integration

See Phase 5 document for React components to consume these APIs.
