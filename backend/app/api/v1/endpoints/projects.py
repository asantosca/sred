# app/api/v1/endpoints/projects.py
"""
Project Discovery API endpoints.

Provides endpoints for:
- Running project discovery
- Managing discovered projects
- Document-project associations
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.models import (
    User, Project, Document, DocumentProjectTag,
    Claim, ProjectDiscoveryRun
)
from app.schemas.project import (
    DiscoverProjectsRequest, DiscoverProjectsResponse,
    ProjectListResponse, ProjectSummary,
    ProjectDetailResponse, ProjectDetail,
    UpdateProjectRequest, GenericResponse,
    ProjectDocumentsResponse, ProjectDocument,
    AddDocumentsRequest, SaveProjectsRequest, SaveProjectsResponse,
    DiscoveredProjectCandidate,
    AnalyzeBatchRequest, ChangeAnalysisResponse,
    ProjectAdditionResponse, NewProjectCandidateResponse,
    NarrativeImpactResponse, ApplyAdditionsRequest, ApplyAdditionsResponse
)
from app.services.project_discovery_service import (
    get_project_discovery_service, ProjectCandidate
)
from app.services.change_detection_service import (
    get_change_detection_service, ProjectAddition
)
from app.core.rate_limit import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/discover", response_model=DiscoverProjectsResponse)
@limiter.limit(get_rate_limit("analysis"))
async def discover_projects(
    request: Request,
    payload: DiscoverProjectsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run project discovery algorithm on a claim's documents.

    Uses HDBSCAN clustering with temporal, semantic, and team features
    to identify potential SR&ED projects.
    """
    try:
        # Verify user has access to the claim
        claim_query = select(Claim).where(
            and_(
                Claim.id == payload.claim_id,
                Claim.company_id == current_user.company_id
            )
        )
        result = await db.execute(claim_query)
        claim = result.scalar_one_or_none()

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        # Run discovery
        service = get_project_discovery_service(db)
        categorized = await service.discover_projects(
            claim_id=payload.claim_id,
            company_id=current_user.company_id,
            user_id=current_user.id,
            min_cluster_size=payload.min_cluster_size,
            backfill_signals=payload.backfill_signals,
            discovery_mode=payload.discovery_mode,
            fuzzy_matching=payload.fuzzy_matching,
            fuzzy_threshold=payload.fuzzy_threshold
        )

        # Get discovery run for run_id
        run_query = select(ProjectDiscoveryRun).where(
            ProjectDiscoveryRun.claim_id == payload.claim_id
        ).order_by(ProjectDiscoveryRun.created_at.desc()).limit(1)
        run_result = await db.execute(run_query)
        run = run_result.scalar_one_or_none()

        # Convert candidates to response format
        def to_response(candidate: ProjectCandidate) -> DiscoveredProjectCandidate:
            # Convert contributor dicts to ContributorInfo objects
            from app.schemas.project import ContributorInfo
            contributors = [
                ContributorInfo(
                    name=c.get("name", ""),
                    title=c.get("title"),
                    role_type=c.get("role_type", "unknown"),
                    is_qualified_personnel=c.get("is_qualified_personnel", False),
                    score=c.get("score"),
                    doc_count=c.get("doc_count")
                )
                for c in candidate.contributors
            ]

            return DiscoveredProjectCandidate(
                name=candidate.name,
                document_count=len(candidate.documents),
                document_ids=candidate.documents,
                start_date=candidate.start_date,
                end_date=candidate.end_date,
                team_members=candidate.team_members,
                contributors=contributors,
                sred_score=candidate.sred_score,
                confidence=candidate.confidence,
                signals=candidate.signals,
                summary=candidate.summary,
                discovery_source=candidate.discovery_source,
                name_variations=candidate.name_variations
            )

        return DiscoverProjectsResponse(
            success=True,
            run_id=run.id if run else None,
            total_documents=run.total_documents_analyzed if run else 0,
            high_confidence=[to_response(c) for c in categorized["high_confidence"]],
            medium_confidence=[to_response(c) for c in categorized["medium_confidence"]],
            low_confidence=[to_response(c) for c in categorized["low_confidence"]],
            orphan_document_ids=categorized.get("orphan_document_ids", [])
        )

    except RuntimeError as e:
        # Clustering libraries not available
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Project discovery failed")


@router.post("/save", response_model=SaveProjectsResponse)
@limiter.limit(get_rate_limit("analysis"))
async def save_discovered_projects(
    request: Request,
    payload: SaveProjectsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save discovered project candidates to the database.

    Call this after discovery to persist the projects you want to keep.
    """
    try:
        # Verify user has access to the claim
        claim_query = select(Claim).where(
            and_(
                Claim.id == payload.claim_id,
                Claim.company_id == current_user.company_id
            )
        )
        result = await db.execute(claim_query)
        claim = result.scalar_one_or_none()

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        # Convert request candidates to internal format
        candidates = []
        for c in payload.candidates:
            candidate = ProjectCandidate(
                documents=c.document_ids,
                name=c.name,
                start_date=c.start_date,
                end_date=c.end_date,
                team_members=c.team_members,
                sred_score=c.sred_score,
                confidence=c.confidence,
                signals=c.signals,
                summary=c.summary,
                discovery_source=c.discovery_source,
                name_variations=c.name_variations
            )
            candidates.append(candidate)

        # Save projects
        service = get_project_discovery_service(db)
        created = await service.save_discovered_projects(
            claim_id=payload.claim_id,
            company_id=current_user.company_id,
            candidates=candidates,
            user_id=current_user.id
        )

        return SaveProjectsResponse(
            success=True,
            projects_created=len(created),
            project_ids=[p.id for p in created],
            message=f"Created {len(created)} projects"
        )

    except Exception as e:
        logger.error(f"Failed to save projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save projects")


@router.get("/claim/{claim_id}", response_model=ProjectListResponse)
async def list_projects_for_claim(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all projects for a claim"""
    try:
        # Verify claim access
        claim_query = select(Claim).where(
            and_(
                Claim.id == claim_id,
                Claim.company_id == current_user.company_id
            )
        )
        result = await db.execute(claim_query)
        claim = result.scalar_one_or_none()

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        # Get projects with document counts
        projects_query = (
            select(
                Project,
                func.count(DocumentProjectTag.id).label("doc_count")
            )
            .outerjoin(DocumentProjectTag, Project.id == DocumentProjectTag.project_id)
            .where(
                and_(
                    Project.claim_id == claim_id,
                    Project.company_id == current_user.company_id
                )
            )
            .group_by(Project.id)
            .order_by(Project.created_at.desc())
        )
        result = await db.execute(projects_query)
        rows = result.all()

        projects = []
        for project, doc_count in rows:
            projects.append(ProjectSummary(
                id=project.id,
                project_name=project.project_name,
                project_code=project.project_code,
                project_status=project.project_status,
                sred_confidence_score=float(project.sred_confidence_score) if project.sred_confidence_score else None,
                document_count=doc_count or 0,
                project_start_date=project.project_start_date,
                project_end_date=project.project_end_date,
                discovery_method=project.discovery_method,
                ai_suggested=project.ai_suggested,
                user_confirmed=project.user_confirmed,
                created_at=project.created_at
            ))

        return ProjectListResponse(
            success=True,
            projects=projects,
            total=len(projects)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list projects")


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get project details"""
    try:
        # Get project with document count
        query = (
            select(
                Project,
                func.count(DocumentProjectTag.id).label("doc_count")
            )
            .outerjoin(DocumentProjectTag, Project.id == DocumentProjectTag.project_id)
            .where(
                and_(
                    Project.id == project_id,
                    Project.company_id == current_user.company_id
                )
            )
            .group_by(Project.id)
        )
        result = await db.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        project, doc_count = row

        return ProjectDetailResponse(
            success=True,
            project=ProjectDetail(
                id=project.id,
                claim_id=project.claim_id,
                company_id=project.company_id,
                project_name=project.project_name,
                project_code=project.project_code,
                project_status=project.project_status,
                sred_confidence_score=float(project.sred_confidence_score) if project.sred_confidence_score else None,
                discovery_method=project.discovery_method,
                ai_suggested=project.ai_suggested,
                user_confirmed=project.user_confirmed,
                project_start_date=project.project_start_date,
                project_end_date=project.project_end_date,
                team_members=project.team_members,
                team_size=project.team_size,
                estimated_spend=float(project.estimated_spend) if project.estimated_spend else None,
                eligible_expenditures=float(project.eligible_expenditures) if project.eligible_expenditures else None,
                uncertainty_signal_count=project.uncertainty_signal_count or 0,
                systematic_signal_count=project.systematic_signal_count or 0,
                failure_signal_count=project.failure_signal_count or 0,
                advancement_signal_count=project.advancement_signal_count or 0,
                ai_summary=project.ai_summary,
                uncertainty_summary=project.uncertainty_summary,
                work_summary=project.work_summary,
                advancement_summary=project.advancement_summary,
                narrative_status=project.narrative_status or "not_started",
                narrative_line_242=project.narrative_line_242,
                narrative_line_244=project.narrative_line_244,
                narrative_line_246=project.narrative_line_246,
                narrative_word_count_242=project.narrative_word_count_242,
                narrative_word_count_244=project.narrative_word_count_244,
                narrative_word_count_246=project.narrative_word_count_246,
                document_count=doc_count or 0,
                created_at=project.created_at,
                updated_at=project.updated_at
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get project")


@router.patch("/{project_id}", response_model=ProjectDetailResponse)
async def update_project(
    project_id: UUID,
    payload: UpdateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update project details"""
    try:
        # Get project
        query = select(Project).where(
            and_(
                Project.id == project_id,
                Project.company_id == current_user.company_id
            )
        )
        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Update fields
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(project, field):
                setattr(project, field, value)

        project.updated_by = current_user.id

        # Update word counts if narratives changed
        if payload.narrative_line_242 is not None:
            project.narrative_word_count_242 = len(payload.narrative_line_242.split())
        if payload.narrative_line_244 is not None:
            project.narrative_word_count_244 = len(payload.narrative_line_244.split())
        if payload.narrative_line_246 is not None:
            project.narrative_word_count_246 = len(payload.narrative_line_246.split())

        await db.commit()
        await db.refresh(project)

        # Get updated project with doc count
        return await get_project(project_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update project")


@router.post("/{project_id}/approve", response_model=GenericResponse)
async def approve_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a discovered project"""
    try:
        query = select(Project).where(
            and_(
                Project.id == project_id,
                Project.company_id == current_user.company_id
            )
        )
        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project.project_status = "approved"
        project.user_confirmed = True
        project.updated_by = current_user.id

        await db.commit()

        return GenericResponse(success=True, message="Project approved")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to approve project")


@router.post("/{project_id}/reject", response_model=GenericResponse)
async def reject_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject a discovered project"""
    try:
        query = select(Project).where(
            and_(
                Project.id == project_id,
                Project.company_id == current_user.company_id
            )
        )
        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project.project_status = "rejected"
        project.user_confirmed = True
        project.updated_by = current_user.id

        await db.commit()

        return GenericResponse(success=True, message="Project rejected")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reject project")


@router.delete("/{project_id}", response_model=GenericResponse)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a project and all its document tags"""
    try:
        query = select(Project).where(
            and_(
                Project.id == project_id,
                Project.company_id == current_user.company_id
            )
        )
        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Delete document tags first (cascade should handle this, but be explicit)
        await db.execute(
            delete(DocumentProjectTag).where(DocumentProjectTag.project_id == project_id)
        )

        # Delete the project
        await db.delete(project)
        await db.commit()

        return GenericResponse(success=True, message="Project deleted")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete project")


@router.get("/{project_id}/documents", response_model=ProjectDocumentsResponse)
async def list_project_documents(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all documents associated with a project"""
    try:
        # Verify project access
        project_query = select(Project).where(
            and_(
                Project.id == project_id,
                Project.company_id == current_user.company_id
            )
        )
        result = await db.execute(project_query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get tagged documents
        docs_query = (
            select(Document, DocumentProjectTag)
            .join(DocumentProjectTag, Document.id == DocumentProjectTag.document_id)
            .where(DocumentProjectTag.project_id == project_id)
            .order_by(Document.document_date.desc().nullslast())
        )
        result = await db.execute(docs_query)
        rows = result.all()

        documents = []
        for doc, tag in rows:
            sred_score = None
            if doc.sred_signals:
                sred_score = doc.sred_signals.get("score")

            documents.append(ProjectDocument(
                document_id=doc.id,
                filename=doc.filename,
                document_title=doc.document_title,
                document_type=doc.document_type,
                document_date=doc.document_date,
                sred_score=sred_score,
                tag_confidence=float(tag.confidence_score) if tag.confidence_score else None,
                tagged_by=tag.tagged_by
            ))

        return ProjectDocumentsResponse(
            success=True,
            documents=documents,
            total=len(documents)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list project documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.post("/{project_id}/documents/add", response_model=GenericResponse)
async def add_documents_to_project(
    project_id: UUID,
    payload: AddDocumentsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add documents to a project"""
    try:
        # Verify project access
        project_query = select(Project).where(
            and_(
                Project.id == project_id,
                Project.company_id == current_user.company_id
            )
        )
        result = await db.execute(project_query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Add tags for each document
        added = 0
        for doc_id in payload.document_ids:
            # Verify document exists and belongs to same company
            doc_query = select(Document).where(
                and_(
                    Document.id == doc_id,
                    Document.company_id == current_user.company_id
                )
            )
            doc_result = await db.execute(doc_query)
            doc = doc_result.scalar_one_or_none()

            if not doc:
                continue

            # Check if already tagged
            existing_query = select(DocumentProjectTag).where(
                and_(
                    DocumentProjectTag.document_id == doc_id,
                    DocumentProjectTag.project_id == project_id
                )
            )
            existing = await db.execute(existing_query)
            if existing.scalar_one_or_none():
                continue

            # Create tag
            tag = DocumentProjectTag(
                document_id=doc_id,
                project_id=project_id,
                tagged_by="user",
                created_by=current_user.id
            )
            db.add(tag)
            added += 1

        await db.commit()

        return GenericResponse(
            success=True,
            message=f"Added {added} documents to project"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add documents")


@router.delete("/{project_id}/documents/{document_id}", response_model=GenericResponse)
async def remove_document_from_project(
    project_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a document from a project"""
    try:
        # Verify project access
        project_query = select(Project).where(
            and_(
                Project.id == project_id,
                Project.company_id == current_user.company_id
            )
        )
        result = await db.execute(project_query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Find and delete the tag
        tag_query = select(DocumentProjectTag).where(
            and_(
                DocumentProjectTag.project_id == project_id,
                DocumentProjectTag.document_id == document_id
            )
        )
        result = await db.execute(tag_query)
        tag = result.scalar_one_or_none()

        if not tag:
            raise HTTPException(status_code=404, detail="Document not in project")

        await db.delete(tag)
        await db.commit()

        return GenericResponse(success=True, message="Document removed from project")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove document")


# ============== Change Detection Endpoints ==============

@router.post("/analyze-batch", response_model=ChangeAnalysisResponse)
@limiter.limit(get_rate_limit("analysis"))
async def analyze_new_documents(
    request: Request,
    payload: AnalyzeBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze new documents to detect impact on existing projects.

    Returns:
    - Documents that should be added to existing projects
    - New potential projects discovered
    - Narrative impacts (contradictions, enhancements)
    - Unassigned documents
    """
    try:
        # Verify user has access to the claim
        claim_query = select(Claim).where(
            and_(
                Claim.id == payload.claim_id,
                Claim.company_id == current_user.company_id
            )
        )
        result = await db.execute(claim_query)
        claim = result.scalar_one_or_none()

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        if not payload.document_ids and not payload.batch_id:
            raise HTTPException(
                status_code=400,
                detail="Either document_ids or batch_id must be provided"
            )

        # Run change detection
        service = get_change_detection_service(db)
        analysis = await service.analyze_batch_impact(
            claim_id=payload.claim_id,
            company_id=current_user.company_id,
            batch_id=payload.batch_id,
            new_document_ids=payload.document_ids
        )

        # Convert to response format
        additions = [
            ProjectAdditionResponse(
                project_id=a.project_id,
                project_name=a.project_name,
                document_ids=a.document_ids,
                document_count=len(a.document_ids),
                confidence=a.confidence,
                average_similarity=a.average_similarity,
                summary=a.summary
            )
            for a in analysis.additions_to_existing
        ]

        new_projects = [
            NewProjectCandidateResponse(
                name=p.name,
                document_ids=p.document_ids,
                document_count=len(p.document_ids),
                confidence=p.confidence,
                sred_score=p.sred_score,
                summary=p.summary
            )
            for p in analysis.new_projects_discovered
        ]

        impacts = [
            NarrativeImpactResponse(
                project_id=i.project_id,
                project_name=i.project_name,
                severity=i.severity,
                impact_type=i.impact_type,
                description=i.description,
                document_ids=i.document_ids,
                affected_line=i.affected_line
            )
            for i in analysis.narrative_impacts
        ]

        return ChangeAnalysisResponse(
            success=True,
            batch_id=analysis.batch_id,
            total_new_documents=analysis.total_new_documents,
            additions_to_existing=additions,
            new_projects_discovered=new_projects,
            narrative_impacts=impacts,
            unassigned_count=len(analysis.unassigned_document_ids),
            unassigned_document_ids=analysis.unassigned_document_ids
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Change detection failed")


@router.post("/apply-additions", response_model=ApplyAdditionsResponse)
@limiter.limit(get_rate_limit("analysis"))
async def apply_document_additions(
    request: Request,
    payload: ApplyAdditionsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Apply recommended document additions to existing projects.

    Takes the additions from analyze-batch and creates the document-project tags.
    """
    try:
        # Convert response format back to internal format
        additions = [
            ProjectAddition(
                project_id=a.project_id,
                project_name=a.project_name,
                document_ids=a.document_ids,
                confidence=a.confidence,
                average_similarity=a.average_similarity,
                summary=a.summary
            )
            for a in payload.additions
        ]

        # Verify all projects belong to user's company
        for addition in additions:
            project_query = select(Project).where(
                and_(
                    Project.id == addition.project_id,
                    Project.company_id == current_user.company_id
                )
            )
            result = await db.execute(project_query)
            project = result.scalar_one_or_none()

            if not project:
                raise HTTPException(
                    status_code=404,
                    detail=f"Project {addition.project_id} not found"
                )

        # Apply additions
        service = get_change_detection_service(db)
        tags_created = await service.apply_additions(
            additions=additions,
            user_id=current_user.id
        )

        return ApplyAdditionsResponse(
            success=True,
            tags_created=tags_created,
            message=f"Applied {tags_created} document tags to {len(additions)} projects"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply additions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to apply additions")
