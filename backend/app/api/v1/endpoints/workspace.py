# app/api/v1/endpoints/workspace.py - Project Discovery Workspace endpoints

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.models import User, Claim, Document
from app.schemas.workspace import (
    WorkspaceResponse, WorkspaceWithHistory,
    WorkspaceUpdateRequest, WorkspaceDiscoverRequest, WorkspaceDiscoverResponse,
    WorkspaceChatRequest, WorkspaceChatResponse,
    WorkspaceParseResponse, ParsedProjectResponse
)
from app.services.workspace_service import WorkspaceService
from app.services.project_discovery_service import ProjectDiscoveryService
from app.core.rate_limit import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/claims/{claim_id}/workspace", response_model=WorkspaceWithHistory)
@limiter.limit(get_rate_limit("default"))
async def get_workspace(
    request: Request,
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get or create the project discovery workspace for a claim.

    Each claim has exactly one project_workspace conversation that contains:
    - Markdown content with discovered projects
    - Chat history for AI-assisted editing
    - Document change detection info

    Returns workspace with chat history.
    """
    try:
        # Verify user has access to the claim
        claim = await _get_claim_with_access(claim_id, current_user, db)

        workspace_service = WorkspaceService(db)
        workspace = await workspace_service.get_or_create_workspace(
            claim_id=claim_id,
            company_id=current_user.company_id,
            user_id=current_user.id
        )

        # Check for document changes
        known_ids = workspace.known_document_ids or []
        changes = await workspace_service.detect_document_changes(
            claim_id=claim_id,
            company_id=current_user.company_id,
            known_document_ids=known_ids
        )

        # Get chat history
        from app.models.models import Message
        messages_query = select(Message).where(
            Message.conversation_id == workspace.id
        ).order_by(Message.created_at)
        result = await db.execute(messages_query)
        messages = result.scalars().all()

        return WorkspaceWithHistory(
            id=workspace.id,
            claim_id=claim_id,
            workspace_md=workspace.workspace_md or "",
            last_discovery_at=workspace.last_discovery_at,
            known_document_ids=known_ids,
            has_document_changes=changes["has_changes"],
            new_document_count=len(changes["new_documents"]),
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
            messages=[{
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at
            } for m in messages]
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting workspace: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get workspace: {str(e)}")


@router.put("/claims/{claim_id}/workspace", response_model=WorkspaceResponse)
@limiter.limit(get_rate_limit("default"))
async def update_workspace(
    request: Request,
    claim_id: UUID,
    update_request: WorkspaceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the workspace markdown content directly.

    This is used for user edits in the markdown editor.
    """
    try:
        # Verify user has access to the claim
        claim = await _get_claim_with_access(claim_id, current_user, db)

        workspace_service = WorkspaceService(db)

        # Get workspace (must exist)
        workspace = await workspace_service.get_or_create_workspace(
            claim_id=claim_id,
            company_id=current_user.company_id,
            user_id=current_user.id
        )

        # Update markdown
        workspace = await workspace_service.update_workspace_markdown(
            workspace_id=workspace.id,
            markdown=update_request.markdown,
            company_id=current_user.company_id
        )

        return WorkspaceResponse(
            id=workspace.id,
            claim_id=claim_id,
            workspace_md=workspace.workspace_md or "",
            last_discovery_at=workspace.last_discovery_at,
            known_document_ids=workspace.known_document_ids or [],
            has_document_changes=False,  # Not checking on update
            new_document_count=0,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating workspace: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update workspace: {str(e)}")


@router.post("/claims/{claim_id}/workspace/discover", response_model=WorkspaceDiscoverResponse)
@limiter.limit(get_rate_limit("chat_message"))
async def run_discovery(
    request: Request,
    claim_id: UUID,
    discover_request: WorkspaceDiscoverRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run project discovery and generate workspace markdown.

    This endpoint:
    1. Analyzes all processed documents for the claim
    2. Discovers potential SR&ED projects using the specified algorithm
    3. Generates markdown with AI narratives for each project
    4. Updates the workspace with the new markdown

    Returns the updated workspace with discovery statistics.
    """
    try:
        # Verify user has access to the claim
        claim = await _get_claim_with_access(claim_id, current_user, db)

        # Run project discovery
        discovery_service = ProjectDiscoveryService(db)
        results = await discovery_service.discover_projects(
            claim_id=claim_id,
            company_id=current_user.company_id,
            user_id=current_user.id,
            min_cluster_size=discover_request.min_cluster_size,
            discovery_mode=discover_request.discovery_mode
        )

        # Combine all candidates
        all_candidates = (
            results["high_confidence"] +
            results["medium_confidence"] +
            results["low_confidence"]
        )

        # Fetch documents for markdown generation
        doc_query = select(Document).where(
            and_(
                Document.claim_id == claim_id,
                Document.company_id == current_user.company_id,
                Document.processing_status.in_(['embedded', 'complete'])
            )
        )
        doc_result = await db.execute(doc_query)
        documents = list(doc_result.scalars().all())

        # Generate workspace markdown
        workspace_service = WorkspaceService(db)
        markdown = await workspace_service.generate_workspace_markdown(
            candidates=all_candidates,
            claim=claim,
            documents=documents,
            generate_narratives=discover_request.generate_narratives
        )

        # Get or create workspace and update it
        workspace = await workspace_service.get_or_create_workspace(
            claim_id=claim_id,
            company_id=current_user.company_id,
            user_id=current_user.id
        )

        # Update workspace with new markdown and document tracking
        from datetime import datetime, timezone
        document_ids = [str(doc.id) for doc in documents]
        workspace.workspace_md = markdown
        workspace.last_discovery_at = datetime.now(timezone.utc)
        workspace.known_document_ids = document_ids
        workspace.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(workspace)

        return WorkspaceDiscoverResponse(
            workspace_id=workspace.id,
            workspace_md=markdown,
            projects_discovered=len(all_candidates),
            high_confidence_count=len(results["high_confidence"]),
            medium_confidence_count=len(results["medium_confidence"]),
            low_confidence_count=len(results["low_confidence"]),
            orphan_count=len(results.get("orphan_document_ids", [])),
            document_ids=document_ids
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error running discovery: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to run discovery: {str(e)}")


@router.post("/claims/{claim_id}/workspace/chat")
@limiter.limit(get_rate_limit("chat_message"))
async def workspace_chat(
    request: Request,
    claim_id: UUID,
    chat_request: WorkspaceChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with AI in the workspace context.

    The AI has access to:
    - Current workspace markdown
    - Project discovery results
    - Claim documents

    The AI can:
    - Answer questions about projects
    - Edit the markdown via <workspace_edit> tags
    - Merge/split projects
    - Adjust dates and narratives

    Supports SSE streaming when stream=true (default).
    """
    try:
        # Verify user has access to the claim
        claim = await _get_claim_with_access(claim_id, current_user, db)

        # Get workspace
        workspace_service = WorkspaceService(db)
        workspace = await workspace_service.get_or_create_workspace(
            claim_id=claim_id,
            company_id=current_user.company_id,
            user_id=current_user.id
        )

        # Import workspace chat service
        from app.services.workspace_chat_service import WorkspaceChatService

        chat_service = WorkspaceChatService(db)

        if chat_request.stream:
            return StreamingResponse(
                chat_service.chat_stream(
                    workspace=workspace,
                    message=chat_request.message,
                    current_user=current_user,
                    claim=claim
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            result = await chat_service.chat(
                workspace=workspace,
                message=chat_request.message,
                current_user=current_user,
                claim=claim
            )
            return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in workspace chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


@router.get("/claims/{claim_id}/workspace/parse", response_model=WorkspaceParseResponse)
@limiter.limit(get_rate_limit("default"))
async def parse_workspace(
    request: Request,
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Parse the workspace markdown into structured project data.

    Useful for:
    - Validating markdown structure
    - Extracting data for T661 form generation
    - Syncing with database Project records
    """
    try:
        # Verify user has access to the claim
        claim = await _get_claim_with_access(claim_id, current_user, db)

        workspace_service = WorkspaceService(db)
        workspace = await workspace_service.get_or_create_workspace(
            claim_id=claim_id,
            company_id=current_user.company_id,
            user_id=current_user.id
        )

        if not workspace.workspace_md:
            return WorkspaceParseResponse(projects=[], parse_errors=[])

        # Parse markdown
        parsed_projects = workspace_service.parse_markdown_to_projects(workspace.workspace_md)

        # Convert to response format
        projects = []
        for p in parsed_projects:
            projects.append(ParsedProjectResponse(
                name=p.name,
                start_date=p.start_date,
                end_date=p.end_date,
                contributors=p.contributors,
                document_count=len(p.documents),
                has_narrative=bool(p.narrative_uncertainty or p.narrative_objective)
            ))

        return WorkspaceParseResponse(projects=projects, parse_errors=[])

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error parsing workspace: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to parse workspace: {str(e)}")


async def _get_claim_with_access(
    claim_id: UUID,
    current_user: User,
    db: AsyncSession
) -> Claim:
    """Verify user has access to the claim and return it."""
    query = select(Claim).where(
        and_(
            Claim.id == claim_id,
            Claim.company_id == current_user.company_id
        )
    )
    result = await db.execute(query)
    claim = result.scalar_one_or_none()

    if not claim:
        raise ValueError("Claim not found or access denied")

    return claim
