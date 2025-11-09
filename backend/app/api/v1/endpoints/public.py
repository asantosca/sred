# app/api/v1/endpoints/public.py - Public endpoints (no authentication required)

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import logging

from app.db.session import get_db
from app.schemas.waitlist import WaitlistSignupCreate, WaitlistSignupResponse
from app.models.models import WaitlistSignup
from app.core.rate_limit import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/waitlist", response_model=WaitlistSignupResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("public_waitlist"))
async def create_waitlist_signup(
    request: Request,
    signup: WaitlistSignupCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint for waitlist signup from marketing site.

    No authentication required.
    Rate limited to prevent spam.
    """
    try:
        # Check if email already exists
        result = await db.execute(
            select(WaitlistSignup).where(WaitlistSignup.email == signup.email)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already on the waitlist"
            )

        # Create new waitlist signup
        db_signup = WaitlistSignup(
            email=signup.email,
            full_name=signup.full_name,
            company_name=signup.company_name,
            phone=signup.phone,
            message=signup.message,
            source=signup.source,
            utm_source=signup.utm_source,
            utm_medium=signup.utm_medium,
            utm_campaign=signup.utm_campaign,
        )

        db.add(db_signup)
        await db.commit()
        await db.refresh(db_signup)

        logger.info(f"New waitlist signup: {signup.email} from {signup.source}")

        return db_signup

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during waitlist signup: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating waitlist signup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process signup. Please try again."
        )
