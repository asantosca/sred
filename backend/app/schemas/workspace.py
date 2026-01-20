# app/schemas/workspace.py - Project Workspace Pydantic models

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class WorkspaceResponse(BaseModel):
    """Response containing workspace data"""
    id: UUID = Field(..., description="Workspace conversation ID")
    claim_id: UUID
    workspace_md: str = Field(..., description="Markdown content")
    last_discovery_at: Optional[datetime] = Field(None, description="Last discovery run timestamp")
    known_document_ids: List[str] = Field(default_factory=list, description="Document IDs at last discovery")
    has_document_changes: bool = Field(False, description="Whether new documents exist since last discovery")
    new_document_count: int = Field(0, description="Number of new documents since last discovery")
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class WorkspaceWithHistory(WorkspaceResponse):
    """Workspace with chat history"""
    messages: List["WorkspaceMessageResponse"] = []


class WorkspaceMessageResponse(BaseModel):
    """Single message in workspace chat"""
    id: UUID
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceUpdateRequest(BaseModel):
    """Request to update workspace markdown"""
    markdown: str = Field(..., min_length=0, description="Updated markdown content")


class WorkspaceDiscoverRequest(BaseModel):
    """Request to run project discovery"""
    discovery_mode: str = Field(
        "sred_first",
        pattern="^(sred_first|names_only|clustering_only|hybrid)$",
        description="Discovery algorithm mode"
    )
    generate_narratives: bool = Field(
        True,
        description="Whether to generate AI narratives for projects"
    )
    min_cluster_size: int = Field(3, ge=2, le=10, description="Minimum documents per project cluster")


class WorkspaceDiscoverResponse(BaseModel):
    """Response from discovery run"""
    workspace_id: UUID
    workspace_md: str
    projects_discovered: int
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    orphan_count: int
    document_ids: List[str] = Field(..., description="Document IDs included in this discovery")


class WorkspaceChatRequest(BaseModel):
    """Request to send a chat message in the workspace"""
    message: str = Field(..., min_length=1, max_length=10000, description="User's message")
    stream: bool = Field(True, description="Whether to stream the response (SSE)")


class WorkspaceChatResponse(BaseModel):
    """Response from workspace chat (non-streaming)"""
    message_id: UUID
    content: str
    workspace_md: str = Field(..., description="Updated workspace markdown (if AI made edits)")
    workspace_was_edited: bool = Field(False, description="Whether the AI edited the workspace")


class ParsedProjectResponse(BaseModel):
    """Parsed project data from workspace markdown"""
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    contributors: List[Dict[str, str]] = []
    document_count: int = 0
    has_narrative: bool = False


class WorkspaceParseResponse(BaseModel):
    """Response with parsed project data"""
    projects: List[ParsedProjectResponse]
    parse_errors: List[str] = []


# Forward reference resolution
WorkspaceWithHistory.model_rebuild()
