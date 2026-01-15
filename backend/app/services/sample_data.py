# app/services/sample_data.py - Service for creating sample data for new users

import logging
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Claim as Matter, ClaimAccess as MatterAccess, Document, Conversation, Message

logger = logging.getLogger(__name__)


class SampleDataService:
    """Service for creating sample/welcome data for new users"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_welcome_data(self, user_id: UUID, company_id: UUID) -> dict:
        """
        Create welcome sample data for a newly activated user.

        Creates:
        - A "Welcome to BC Legal Tech" matter
        - Matter access for the user
        - A welcome conversation with helpful tips

        Returns dict with created resource IDs.
        """
        try:
            # Create welcome claim
            welcome_matter = Matter(
                company_id=company_id,
                claim_number="WELCOME-001",
                company_name="Sample Client Company",
                project_type="Onboarding",
                claim_status="active",
                description=(
                    "Welcome to PwC SR&ED Intelligence! This sample claim demonstrates how "
                    "claims work. You can upload documents, ask questions, and organize "
                    "your SR&ED work. Feel free to archive or delete this claim once "
                    "you're familiar with the platform."
                ),
                opened_date=date.today(),
                lead_consultant_user_id=user_id,
                created_by=user_id,
                updated_by=user_id,
            )
            self.db.add(welcome_matter)
            await self.db.flush()  # Get the matter ID

            # Grant full access to the user
            matter_access = MatterAccess(
                matter_id=welcome_matter.id,
                user_id=user_id,
                access_role="lead_attorney",
                can_upload=True,
                can_edit=True,
                can_delete=True,
                granted_by=user_id,
            )
            self.db.add(matter_access)

            # Create a welcome conversation with tips
            welcome_conversation = Conversation(
                user_id=user_id,
                company_id=company_id,
                matter_id=welcome_matter.id,
                title="Getting Started with BC Legal Tech",
                is_pinned=True,
                is_archived=False,
            )
            self.db.add(welcome_conversation)
            await self.db.flush()

            # Add welcome messages
            user_message = Message(
                conversation_id=welcome_conversation.id,
                role="user",
                content="How do I get started with BC Legal Tech?",
            )
            self.db.add(user_message)

            assistant_message = Message(
                conversation_id=welcome_conversation.id,
                role="assistant",
                content="""Welcome to BC Legal Tech! Here's how to get started:

**1. Upload Documents**
Go to the Documents page and upload your legal documents (PDFs, Word docs, etc.). Our AI will automatically extract and index the content for semantic search.

**2. Organize with Matters**
Create matters to organize documents by case or client. Each matter can have its own set of documents and conversations.

**3. Ask Questions**
Use the Chat feature to ask questions about your documents. The AI will search through your uploaded documents and provide answers with source citations.

**4. Scope Conversations to Matters**
When starting a new chat, you can select a specific matter to focus the AI's responses on documents within that matter.

**Tips:**
- Click on source citations to see the exact document passages
- Use the thumbs up/down to provide feedback on AI responses
- Pin important conversations for quick access

Feel free to explore! You can delete this welcome conversation and matter once you're comfortable with the platform.""",
            )
            self.db.add(assistant_message)

            await self.db.commit()

            logger.info(
                f"Created welcome data for user {user_id}: "
                f"matter={welcome_matter.id}, conversation={welcome_conversation.id}"
            )

            return {
                "matter_id": str(welcome_matter.id),
                "conversation_id": str(welcome_conversation.id),
            }

        except Exception as e:
            logger.error(f"Failed to create welcome data for user {user_id}: {e}")
            await self.db.rollback()
            # Don't raise - welcome data is nice-to-have, not critical
            return {}
