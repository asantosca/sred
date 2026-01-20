# app/services/workspace_chat_service.py
"""
Workspace Chat Service

Handles AI chat in the workspace context with ability to edit markdown.
The AI can:
- Answer questions about discovered projects
- Edit the workspace markdown via <workspace_edit> tags
- Merge/split projects
- Adjust dates, contributors, narratives
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, AsyncGenerator, Any
from uuid import UUID

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Conversation, Message, User, Claim, Document
from app.schemas.workspace import WorkspaceChatResponse
from app.services.usage_logging import usage_logging_service

logger = logging.getLogger(__name__)


class WorkspaceChatService:
    """Service for AI chat in workspace context with markdown editing"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def chat(
        self,
        workspace: Conversation,
        message: str,
        current_user: User,
        claim: Claim
    ) -> WorkspaceChatResponse:
        """
        Process a chat message and return response (non-streaming).

        The AI may include <workspace_edit> tags to modify the markdown.
        """
        # Get conversation history
        history = await self._get_conversation_history(workspace.id)

        # Build system prompt with workspace context
        system_prompt = self._build_system_prompt(workspace, claim)

        # Save user message
        user_message = await self._save_message(
            conversation_id=workspace.id,
            role="user",
            content=message
        )

        # Call Claude API
        try:
            messages = self._format_history_for_claude(history) + [
                {"role": "user", "content": message}
            ]

            response = await self.anthropic.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=settings.ANTHROPIC_MAX_TOKENS,
                system=system_prompt,
                messages=messages
            )

            raw_content = response.content[0].text

            # Log usage
            await usage_logging_service.log_usage(
                service="claude_chat",
                operation="workspace_chat",
                company_id=current_user.company_id,
                user_id=current_user.id,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                model_name=settings.ANTHROPIC_MODEL,
                conversation_id=workspace.id,
                db=self.db
            )

        except Exception as e:
            logger.error(f"Claude API error in workspace chat: {e}", exc_info=True)
            raise Exception(f"Failed to generate response: {str(e)}")

        # Parse and apply any workspace edits
        clean_content, workspace_was_edited = await self._apply_workspace_edits(
            workspace, raw_content
        )

        # Save assistant message
        assistant_message = await self._save_message(
            conversation_id=workspace.id,
            role="assistant",
            content=clean_content,
            model_name=settings.ANTHROPIC_MODEL,
            token_count=response.usage.output_tokens
        )

        return WorkspaceChatResponse(
            message_id=assistant_message.id,
            content=clean_content,
            workspace_md=workspace.workspace_md or "",
            workspace_was_edited=workspace_was_edited
        )

    async def chat_stream(
        self,
        workspace: Conversation,
        message: str,
        current_user: User,
        claim: Claim
    ) -> AsyncGenerator[str, None]:
        """
        Process a chat message and stream the response via SSE.

        Yields SSE-formatted chunks. Workspace edits are applied at the end.
        """
        # Get conversation history
        history = await self._get_conversation_history(workspace.id)

        # Build system prompt
        system_prompt = self._build_system_prompt(workspace, claim)

        # Save user message
        user_message = await self._save_message(
            conversation_id=workspace.id,
            role="user",
            content=message
        )

        # Stream Claude response
        full_content = ""
        formatted_messages = self._format_history_for_claude(history) + [
            {"role": "user", "content": message}
        ]

        try:
            async with self.anthropic.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=settings.ANTHROPIC_MAX_TOKENS,
                system=system_prompt,
                messages=formatted_messages
            ) as stream:
                async for text in stream.text_stream:
                    full_content += text
                    yield f"data: {self._format_sse_chunk('content', text)}\n\n"

            # Get final message with usage
            final_message = await stream.get_final_message()

            # Log usage
            await usage_logging_service.log_usage(
                service="claude_chat",
                operation="workspace_chat_stream",
                company_id=current_user.company_id,
                user_id=current_user.id,
                input_tokens=final_message.usage.input_tokens,
                output_tokens=final_message.usage.output_tokens,
                model_name=settings.ANTHROPIC_MODEL,
                conversation_id=workspace.id,
                db=self.db
            )

        except Exception as e:
            logger.error(f"Streaming error in workspace chat: {e}", exc_info=True)
            yield f"data: {self._format_sse_chunk('error', str(e))}\n\n"
            return

        # Parse and apply workspace edits
        clean_content, workspace_was_edited = await self._apply_workspace_edits(
            workspace, full_content
        )

        # Save assistant message
        assistant_message = await self._save_message(
            conversation_id=workspace.id,
            role="assistant",
            content=clean_content,
            model_name=settings.ANTHROPIC_MODEL,
            token_count=final_message.usage.output_tokens
        )

        # Send workspace update if edited
        if workspace_was_edited:
            yield f"data: {self._format_sse_chunk('workspace_update', workspace.workspace_md)}\n\n"

        # Send done signal
        yield f"data: {self._format_sse_chunk('done', {'message_id': str(assistant_message.id), 'workspace_was_edited': workspace_was_edited})}\n\n"

    def _build_system_prompt(self, workspace: Conversation, claim: Claim) -> str:
        """Build system prompt with workspace context."""
        workspace_md = workspace.workspace_md or "*No projects discovered yet*"

        return f"""You are an SR&ED (Scientific Research and Experimental Development) project analyst helping to refine discovered projects in a collaborative workspace.

## Current Workspace

The user is working on claim: **{claim.company_name}** (FY {claim.fiscal_year_end.year if claim.fiscal_year_end else 'N/A'})

Current workspace markdown:
<workspace>
{workspace_md}
</workspace>

## Your Capabilities

1. **Answer Questions**: Explain project details, SR&ED eligibility, narrative structure
2. **Edit Workspace**: Modify the markdown by including edits in your response

## How to Edit the Workspace

When the user asks you to make changes (merge projects, edit narratives, adjust dates, etc.), include your edits using this format:

<workspace_edit>
[Full replacement markdown for the entire workspace]
</workspace_edit>

Rules for workspace edits:
- Include the ENTIRE workspace markdown in the edit tag, not just the changed section
- Preserve all projects unless the user explicitly asks to remove one
- Keep the document links in format: [filename](doc:uuid)
- Maintain the structure: ## Project N: Name, ### Dates, ### Contributors, ### Documents, ### Narrative
- After the edit tag, explain what you changed in plain text

## Common Editing Tasks

- **Merge projects**: Combine two projects into one, merging their documents and updating the narrative
- **Split project**: Divide one project into multiple projects
- **Edit narrative**: Rewrite the Why/Goal/How/Outcome sections
- **Adjust dates**: Update start/end dates with context
- **Add/remove contributors**: Modify the contributor list
- **Rename project**: Change the project name

## Guidelines

- Be concise and professional
- When editing, make targeted changes while preserving the rest
- If unsure about an edit, ask clarifying questions first
- Focus on SR&ED eligibility: technological uncertainty, systematic investigation, advancement
- Reference specific projects by name (e.g., "Project 1: AURORA")"""

    async def _apply_workspace_edits(
        self,
        workspace: Conversation,
        content: str
    ) -> tuple[str, bool]:
        """
        Parse response for <workspace_edit> tags and apply changes.

        Returns:
            (clean_content, was_edited)
        """
        # Find workspace edit blocks
        edit_pattern = r'<workspace_edit>\s*(.*?)\s*</workspace_edit>'
        matches = re.findall(edit_pattern, content, re.DOTALL)

        if not matches:
            return content, False

        # Apply the last edit (in case there are multiple)
        new_markdown = matches[-1].strip()

        # Update workspace
        workspace.workspace_md = new_markdown
        workspace.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Remove edit blocks from content for display
        clean_content = re.sub(edit_pattern, '', content, flags=re.DOTALL).strip()

        # Add note about the edit if content is empty
        if not clean_content:
            clean_content = "I've updated the workspace markdown."

        logger.info(f"Applied workspace edit to conversation {workspace.id}")

        return clean_content, True

    async def _get_conversation_history(
        self,
        conversation_id: UUID,
        limit: int = 10
    ) -> List[Message]:
        """Get recent conversation history."""
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        return list(reversed(messages))

    def _format_history_for_claude(self, history: List[Message]) -> List[Dict]:
        """Format message history for Claude API."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in history
            if msg.role in ("user", "assistant")
        ]

    async def _save_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        model_name: Optional[str] = None,
        token_count: Optional[int] = None
    ) -> Message:
        """Save message to database."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_name=model_name,
            token_count=token_count
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message

    def _format_sse_chunk(self, chunk_type: str, data: Any) -> str:
        """Format chunk as JSON for SSE."""
        if isinstance(data, dict):
            return json.dumps({"type": chunk_type, **data})
        else:
            return json.dumps({"type": chunk_type, chunk_type: data})


def get_workspace_chat_service(db: AsyncSession) -> WorkspaceChatService:
    """Factory function to create WorkspaceChatService with database session"""
    return WorkspaceChatService(db)
