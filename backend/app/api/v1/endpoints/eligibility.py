# app/api/v1/endpoints/eligibility.py - SR&ED eligibility report endpoints

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.models import User
from app.schemas.eligibility import (
    EligibilityReportRequest, EligibilityReportResponse
)
from app.services.eligibility_report_service import EligibilityReportService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/{claim_id}/eligibility-report",
    response_model=EligibilityReportResponse,
    summary="Generate SR&ED eligibility report",
    description="Generate a comprehensive SR&ED eligibility assessment report for a claim based on uploaded documents."
)
async def generate_eligibility_report(
    claim_id: UUID,
    request: EligibilityReportRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate an SR&ED eligibility report for a claim.

    This endpoint analyzes all documents associated with the claim and generates
    a comprehensive eligibility assessment including:
    - Five-question test scores
    - Documentation gap analysis
    - Risk assessment
    - Recommendations for strengthening the claim

    Requires at least one document to be uploaded to the claim.
    """
    try:
        service = EligibilityReportService(db)
        report = await service.generate_report(
            claim_id=claim_id,
            user=current_user,
            request=request
        )

        return EligibilityReportResponse(
            success=True,
            report=report
        )

    except ValueError as e:
        logger.warning(f"Eligibility report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating eligibility report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate eligibility report"
        )
