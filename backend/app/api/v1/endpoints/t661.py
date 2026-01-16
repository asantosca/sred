# app/api/v1/endpoints/t661.py - CRA T661 form drafting endpoints

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.models import User
from app.schemas.t661 import (
    T661DraftRequest, T661DraftResponse, T661_SECTIONS, T661_WORD_LIMITS,
    T661StreamlineRequest, T661StreamlineResponse
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
    the project description boxes of CRA Form T661:
    - Box 242: Scientific or Technological Uncertainties (includes objectives) - 350 words
    - Box 244: Work Performed to Overcome Uncertainties - 700 words
    - Box 246: Advancements Achieved - 350 words

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

    Returns section identifiers, their full names, and CRA word limits for use in draft requests.
    """
    return {
        "sections": [
            {
                "key": key,
                "name": name,
                "word_limit": T661_WORD_LIMITS.get(key, 350)
            }
            for key, name in T661_SECTIONS.items()
        ]
    }


@router.get(
    "/t661-word-limits",
    summary="Get CRA word limits",
    description="Get the CRA word limits for each T661 section."
)
async def get_word_limits(
    current_user: User = Depends(get_current_user)
):
    """
    Get the CRA word limits for each T661 form section.

    These limits are used to determine if a section is over the allowed length.
    """
    return {
        "word_limits": T661_WORD_LIMITS
    }


@router.post(
    "/{claim_id}/t661-streamline",
    response_model=T661StreamlineResponse,
    summary="Streamline T661 section",
    description="Condense a T661 section to fit within CRA word limits while preserving meaning and citations."
)
async def streamline_section(
    claim_id: UUID,
    request: T661StreamlineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Streamline (condense) a T661 section to reduce word count.

    This endpoint uses AI to condense the content while:
    - Preserving all source citations [X]
    - Keeping technical specifics (dates, metrics, technologies)
    - Maintaining factual accuracy
    - Retaining evidence of SR&ED eligibility criteria

    The target word count defaults to the CRA limit for the section if not specified.
    """
    try:
        # Validate section
        if request.section not in T661_SECTIONS:
            raise ValueError(f"Invalid section: {request.section}. Must be one of: {list(T661_SECTIONS.keys())}")

        service = T661DraftService(db)
        result = await service.streamline_section(
            request=request,
            user=current_user
        )

        return result

    except ValueError as e:
        logger.warning(f"T661 streamline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error streamlining T661 section: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to streamline T661 section"
        )
