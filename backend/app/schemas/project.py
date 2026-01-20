# app/schemas/project.py
"""
Pydantic schemas for Project Discovery endpoints.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field


# ============== Request Schemas ==============

class DiscoverProjectsRequest(BaseModel):
    """Request to run project discovery for a claim"""
    claim_id: UUID
    min_cluster_size: int = Field(default=3, ge=2, le=10, description="Minimum documents per cluster (fallback clustering)")
    backfill_signals: bool = Field(default=True, description="Backfill SR&ED signals for docs missing them")
    discovery_mode: str = Field(
        default="sred_first",
        description="Discovery mode: 'sred_first' (recommended - find docs with technological uncertainty, then cluster), 'names_only' (use extracted names), 'clustering_only' (HDBSCAN), 'hybrid' (names first, cluster orphans)"
    )
    fuzzy_matching: bool = Field(default=True, description="Enable fuzzy matching for project name variations")
    fuzzy_threshold: float = Field(default=0.8, ge=0.5, le=1.0, description="Similarity threshold for fuzzy name matching")


class UpdateProjectRequest(BaseModel):
    """Request to update a project"""
    project_name: Optional[str] = Field(None, max_length=255)
    project_code: Optional[str] = Field(None, max_length=50)
    project_status: Optional[str] = Field(None, max_length=50)
    project_start_date: Optional[date] = None
    project_end_date: Optional[date] = None
    team_members: Optional[List[str]] = None
    estimated_spend: Optional[Decimal] = None
    eligible_expenditures: Optional[Decimal] = None
    narrative_line_242: Optional[str] = None
    narrative_line_244: Optional[str] = None
    narrative_line_246: Optional[str] = None


class AddDocumentsRequest(BaseModel):
    """Request to add documents to a project"""
    document_ids: List[UUID]


class RemoveDocumentRequest(BaseModel):
    """Request body for removing a document (optional confidence/notes)"""
    reason: Optional[str] = None


# ============== Response Schemas ==============

class ProjectSummary(BaseModel):
    """Brief project information for list views"""
    id: UUID
    project_name: str
    project_code: Optional[str] = None
    project_status: str
    sred_confidence_score: Optional[float] = None
    document_count: int = 0
    project_start_date: Optional[date] = None
    project_end_date: Optional[date] = None
    discovery_method: Optional[str] = None
    ai_suggested: bool = False
    user_confirmed: bool = False
    created_at: datetime


class ProjectDetail(BaseModel):
    """Full project details"""
    id: UUID
    claim_id: UUID
    company_id: UUID

    # Identity
    project_name: str
    project_code: Optional[str] = None

    # Status
    project_status: str
    sred_confidence_score: Optional[float] = None
    discovery_method: Optional[str] = None
    ai_suggested: bool = False
    user_confirmed: bool = False

    # Dates
    project_start_date: Optional[date] = None
    project_end_date: Optional[date] = None

    # Team
    team_members: Optional[List[str]] = None
    team_size: Optional[int] = None

    # Financial
    estimated_spend: Optional[float] = None
    eligible_expenditures: Optional[float] = None

    # SR&ED Signals
    uncertainty_signal_count: int = 0
    systematic_signal_count: int = 0
    failure_signal_count: int = 0
    advancement_signal_count: int = 0

    # AI Summaries
    ai_summary: Optional[str] = None
    uncertainty_summary: Optional[str] = None
    work_summary: Optional[str] = None
    advancement_summary: Optional[str] = None

    # Narratives
    narrative_status: str = "not_started"
    narrative_line_242: Optional[str] = None
    narrative_line_244: Optional[str] = None
    narrative_line_246: Optional[str] = None
    narrative_word_count_242: Optional[int] = None
    narrative_word_count_244: Optional[int] = None
    narrative_word_count_246: Optional[int] = None

    # Document count (populated by endpoint)
    document_count: int = 0

    # Audit
    created_at: datetime
    updated_at: Optional[datetime] = None


class DocumentTag(BaseModel):
    """Document tag association with project"""
    id: UUID
    document_id: UUID
    project_id: UUID
    tagged_by: str
    confidence_score: Optional[float] = None
    page_ranges: Optional[str] = None
    relevance_notes: Optional[str] = None
    created_at: datetime


class ProjectDocument(BaseModel):
    """Document information within a project"""
    document_id: UUID
    filename: str
    document_title: str
    document_type: str
    document_date: Optional[date] = None
    sred_score: Optional[float] = None
    tag_confidence: Optional[float] = None
    tagged_by: str


class DiscoveryRunSummary(BaseModel):
    """Summary of a discovery run"""
    id: UUID
    claim_id: UUID
    total_documents_analyzed: Optional[int] = None
    discovery_algorithm: Optional[str] = None
    projects_discovered: Optional[int] = None
    high_confidence_count: Optional[int] = None
    medium_confidence_count: Optional[int] = None
    low_confidence_count: Optional[int] = None
    execution_time_seconds: Optional[float] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime


class ContributorInfo(BaseModel):
    """Contributor information with role details"""
    name: str
    title: Optional[str] = None
    role_type: str = "unknown"  # "technical", "management", "support", "unknown"
    is_qualified_personnel: bool = False  # SR&ED qualified personnel indicator
    score: Optional[float] = None  # Contribution score
    doc_count: Optional[int] = None  # Number of documents contributed to


class DiscoveredProjectCandidate(BaseModel):
    """Project candidate from discovery (before saving)"""
    name: str
    document_count: int
    document_ids: List[UUID]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_members: List[str] = []
    contributors: List[ContributorInfo] = []  # Structured contributor info with titles/roles
    sred_score: float
    confidence: float
    signals: Dict[str, int] = {}
    summary: str = ""
    discovery_source: str = "clustering"  # "sred_signal", "name_based", or "clustering"
    name_variations: List[str] = []  # Original name variations found in documents


class DiscoverProjectsResponse(BaseModel):
    """Response from project discovery"""
    success: bool
    run_id: Optional[UUID] = None
    total_documents: int = 0
    high_confidence: List[DiscoveredProjectCandidate] = []
    medium_confidence: List[DiscoveredProjectCandidate] = []
    low_confidence: List[DiscoveredProjectCandidate] = []
    orphan_document_ids: List[UUID] = []  # Documents that couldn't be assigned to any project
    message: Optional[str] = None


class ProjectListResponse(BaseModel):
    """Response for listing projects"""
    success: bool
    projects: List[ProjectSummary]
    total: int


class ProjectDetailResponse(BaseModel):
    """Response for single project"""
    success: bool
    project: ProjectDetail


class ProjectDocumentsResponse(BaseModel):
    """Response for project documents"""
    success: bool
    documents: List[ProjectDocument]
    total: int


class SaveProjectsRequest(BaseModel):
    """Request to save discovered projects to database"""
    claim_id: UUID
    candidates: List[DiscoveredProjectCandidate]


class SaveProjectsResponse(BaseModel):
    """Response from saving discovered projects"""
    success: bool
    projects_created: int
    project_ids: List[UUID]
    message: Optional[str] = None


class GenericResponse(BaseModel):
    """Generic success/error response"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ============== Change Detection Schemas ==============

class AnalyzeBatchRequest(BaseModel):
    """Request to analyze a batch of new documents"""
    claim_id: UUID
    document_ids: Optional[List[UUID]] = Field(
        None, description="Specific document IDs to analyze. If not provided, uses batch_id"
    )
    batch_id: Optional[UUID] = Field(
        None, description="Upload batch ID to analyze"
    )


class ProjectAdditionResponse(BaseModel):
    """Documents that should be added to an existing project"""
    project_id: UUID
    project_name: str
    document_ids: List[UUID]
    document_count: int
    confidence: str  # high, medium, low
    average_similarity: float
    summary: str


class NewProjectCandidateResponse(BaseModel):
    """A new project discovered from new documents"""
    name: str
    document_ids: List[UUID]
    document_count: int
    confidence: float
    sred_score: float
    summary: str


class NarrativeImpactResponse(BaseModel):
    """Impact on an existing project's narrative"""
    project_id: UUID
    project_name: str
    severity: str  # high, medium, low
    impact_type: str  # contradiction, enhancement, gap, new_evidence
    description: str
    document_ids: List[UUID]
    affected_line: Optional[int] = None  # T661 line number (242, 244, 246)


class ChangeAnalysisResponse(BaseModel):
    """Complete result of change detection analysis"""
    success: bool
    batch_id: Optional[UUID] = None
    total_new_documents: int = 0
    additions_to_existing: List[ProjectAdditionResponse] = []
    new_projects_discovered: List[NewProjectCandidateResponse] = []
    narrative_impacts: List[NarrativeImpactResponse] = []
    unassigned_count: int = 0
    unassigned_document_ids: List[UUID] = []


class ApplyAdditionsRequest(BaseModel):
    """Request to apply document additions to projects"""
    additions: List[ProjectAdditionResponse]


class ApplyAdditionsResponse(BaseModel):
    """Response from applying additions"""
    success: bool
    tags_created: int
    message: str


class UploadBatchSummary(BaseModel):
    """Summary of an upload batch"""
    id: UUID
    claim_id: UUID
    batch_number: Optional[int] = None
    document_count: Optional[int] = None
    total_size_bytes: Optional[int] = None
    analyzed: bool = False
    impact_summary: Optional[Dict[str, Any]] = None
    created_at: datetime
