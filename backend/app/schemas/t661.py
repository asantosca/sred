# app/schemas/t661.py - Pydantic schemas for T661 form drafting

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime
from uuid import UUID


# CRA word limits by box (official T661 form structure)
T661_WORD_LIMITS = {
    "box242": 350,  # Scientific or Technological Uncertainties (includes objectives)
    "box244": 700,  # Work Performed to Overcome Uncertainties
    "box246": 350,  # Advancements Achieved
}

# Evidence strength levels
EVIDENCE_STRENGTH_LEVELS = ["strong", "moderate", "weak", "insufficient"]


class SourceCitation(BaseModel):
    """Citation linking content to a specific source document"""
    citation_id: int = Field(..., description="Citation number [1], [2], etc.")
    document_id: UUID = Field(..., description="Source document ID")
    document_title: str = Field(..., description="Document title for display")
    chunk_id: Optional[UUID] = Field(None, description="Specific chunk ID if applicable")
    page_number: Optional[int] = Field(None, description="Page number if available")
    excerpt: str = Field(..., description="Relevant text excerpt from the source")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score 0-1")


class T661SectionDraft(BaseModel):
    """Draft content for a single T661 box with citations and word tracking"""
    section: str = Field(..., description="Box identifier: box242, box244, box246")
    section_name: str = Field(..., description="Human-readable section name")
    draft_content: str = Field(..., description="Draft response content with [X] citation markers")

    # Word count tracking
    word_count: int = Field(default=0, description="Word count of the draft")
    word_limit: int = Field(default=350, description="CRA word limit for this section")
    is_over_limit: bool = Field(default=False, description="True if over CRA word limit")
    words_over: int = Field(default=0, description="Number of words over limit (0 if under)")

    # Source citations
    sources: List[SourceCitation] = Field(default_factory=list, description="Detailed source citations")
    sources_cited: List[str] = Field(default_factory=list, description="Document titles cited (legacy)")

    # Evidence assessment
    evidence_strength: str = Field(
        default="insufficient",
        description="Evidence strength: strong, moderate, weak, insufficient"
    )

    # Review status
    confidence_notes: Optional[str] = Field(None, description="Notes about confidence or areas needing review")
    needs_review: bool = Field(default=True, description="Flag if section needs consultant review")


class T661ProjectInfo(BaseModel):
    """Project information for T661 Part 2"""
    project_title: Optional[str] = None
    field_of_science: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    project_description: Optional[str] = None


class T661DraftRequest(BaseModel):
    """Request to generate T661 draft"""
    sections: List[str] = Field(
        default=["box242", "box244", "box246"],
        description="Which boxes to generate drafts for (box242, box244, box246)"
    )
    project_info: Optional[T661ProjectInfo] = Field(
        None, description="Optional project info to include"
    )
    max_words_per_section: int = Field(
        default=500,
        description="Maximum words per section"
    )


class T661Draft(BaseModel):
    """Complete T661 form draft"""
    claim_id: UUID
    fiscal_year_start: Optional[date] = Field(None, description="Fiscal year start date for this claim")
    fiscal_year_end: Optional[date] = Field(None, description="Fiscal year end date for this claim")
    generated_at: datetime

    # Project information (Part 2)
    project_info: Optional[T661ProjectInfo] = None

    # Section drafts
    sections: List[T661SectionDraft] = Field(default_factory=list)

    # Overall assessment
    overall_completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Completeness score 0.0-1.0"
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Key information that's missing"
    )

    # Metadata
    model_name: str = Field(..., description="AI model used")
    input_token_count: int = Field(default=0)
    output_token_count: int = Field(default=0)
    documents_analyzed: int = Field(default=0)


class T661DraftResponse(BaseModel):
    """API response for T661 draft"""
    success: bool
    draft: Optional[T661Draft] = None
    error: Optional[str] = None


class T661SectionUpdateRequest(BaseModel):
    """Request to update a specific T661 section"""
    section: str = Field(..., description="Section to update")
    content: str = Field(..., description="Updated content")
    notes: Optional[str] = Field(None, description="Consultant notes")


# Constants for T661 boxes (official CRA nomenclature)
T661_SECTIONS = {
    "box242": "Line 242 – Scientific or Technological Uncertainties",
    "box244": "Line 244 – Work Performed",
    "box246": "Line 246 – Advancements Achieved"
}

T661_SECTION_DESCRIPTIONS = {
    "box242": "What scientific or technological uncertainties did you attempt to overcome? Include the objective of the project and describe the uncertainty.",
    "box244": "What work did you perform in the tax year to overcome the technological obstacles/uncertainties described in Line 242?",
    "box246": "What scientific or technological advancements did you achieve or attempt to achieve as a result of the work described in Line 244?"
}


# Streamline feature schemas
class T661StreamlineRequest(BaseModel):
    """Request to streamline (condense) a T661 box"""
    section: str = Field(..., description="Box identifier: box242, box244, box246")
    current_content: str = Field(..., description="Current content to streamline")
    target_words: Optional[int] = Field(
        None,
        description="Target word count (defaults to CRA limit for section)"
    )
    preserve_citations: bool = Field(
        default=True,
        description="Ensure all [X] citations are preserved"
    )


class T661StreamlineResponse(BaseModel):
    """Response from streamline operation"""
    section: str = Field(..., description="Section that was streamlined")
    original_content: str = Field(..., description="Original content before streamlining")
    streamlined_content: str = Field(..., description="Condensed content")
    original_word_count: int = Field(..., description="Word count before streamlining")
    new_word_count: int = Field(..., description="Word count after streamlining")
    words_reduced: int = Field(..., description="Number of words removed")
    target_word_count: int = Field(..., description="Target word count used")
    is_within_limit: bool = Field(..., description="True if now within CRA limit")
    citations_preserved: bool = Field(
        default=True,
        description="True if all original citations were preserved"
    )
    citations_in_original: int = Field(default=0, description="Number of citations in original")
    citations_in_result: int = Field(default=0, description="Number of citations in result")


class T661DraftListItem(BaseModel):
    """Summary item for listing saved T661 drafts"""
    id: UUID
    claim_id: UUID
    generated_at: datetime
    sections_included: List[str] = Field(default_factory=list)
    overall_completeness: float = Field(default=0.0)
    documents_analyzed: int = Field(default=0)


class T661DraftListResponse(BaseModel):
    """Response for listing T661 drafts"""
    drafts: List[T661DraftListItem] = Field(default_factory=list)
    total: int = Field(default=0)
