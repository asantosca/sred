# app/api/v1/endpoints/t661.py - CRA T661 form drafting endpoints

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.models import User
from app.schemas.t661 import (
    T661DraftRequest, T661DraftResponse, T661_SECTIONS
)
from app.services.t661_service import T661DraftService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/{claim_id}/t661-draft",
    response_model=T661DraftResponse,
    summary="Generate T661 form draft",
    description="Generate draft responses for CRA T661 form sections based on uploaded project documents."
)
async def generate_t661_draft(
    claim_id: UUID,
    request: T661DraftRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate draft T661 form sections for an SR&ED claim.

    This endpoint analyzes project documents and generates draft responses for
    the technical sections of CRA Form T661:
    - Part 3: Scientific or Technological Objectives
    - Part 4: Technological Uncertainties
    - Part 5: Work Done to Address Uncertainties
    - Part 6: Conclusions

    The drafts are generated based on evidence found in uploaded documents
    and should be reviewed and edited by the consultant before submission.
    """
    try:
        if request is None:
            request = T661DraftRequest()

        service = T661DraftService(db)
        draft = await service.generate_draft(
            claim_id=claim_id,
            user=current_user,
            request=request
        )

        return T661DraftResponse(
            success=True,
            draft=draft
        )

    except ValueError as e:
        logger.warning(f"T661 draft generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating T661 draft: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate T661 draft"
        )


@router.get(
    "/t661-sections",
    summary="Get T661 section definitions",
    description="Get the list of T661 sections that can be drafted."
)
async def get_t661_sections(
    current_user: User = Depends(get_current_user)
):
    """
    Get the list of T661 form sections that can be drafted.

    Returns section identifiers and their full names for use in draft requests.
    """
    return {
        "sections": [
            {"key": key, "name": name}
            for key, name in T661_SECTIONS.items()
        ]
    }
