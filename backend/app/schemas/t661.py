# app/schemas/t661.py - Pydantic schemas for T661 form drafting

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime
from uuid import UUID


class T661SectionDraft(BaseModel):
    """Draft content for a single T661 section"""
    section: str = Field(..., description="Section identifier: part2, part3, part4, part5, part6")
    section_name: str = Field(..., description="Human-readable section name")
    draft_content: str = Field(..., description="Draft response content")
    word_count: int = Field(default=0, description="Word count of the draft")
    sources_cited: List[str] = Field(default_factory=list, description="Document sources cited")
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
        default=["part3", "part4", "part5", "part6"],
        description="Which sections to generate drafts for"
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
    fiscal_year_end: Optional[date] = None
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


# Constants for T661 sections
T661_SECTIONS = {
    "part2": "Project Information",
    "part3": "Scientific or Technological Objectives",
    "part4": "Technological Uncertainties",
    "part5": "Work Done to Address Uncertainties",
    "part6": "Conclusions"
}

T661_SECTION_DESCRIPTIONS = {
    "part3": "State the specific scientific or technological objectives of the work",
    "part4": "Describe the technological uncertainties that existed at the start of work",
    "part5": "Describe the systematic investigation undertaken to resolve uncertainties",
    "part6": "State what was learned or achieved as a result of the work"
}
