# app/schemas/eligibility.py - Pydantic schemas for SR&ED eligibility reports

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class FiveQuestionScore(BaseModel):
    """Score for each criterion in the five-question test"""
    technological_uncertainty: str = Field(..., description="STRONG, MODERATE, WEAK, or INSUFFICIENT")
    systematic_investigation: str = Field(..., description="STRONG, MODERATE, WEAK, or INSUFFICIENT")
    technological_advancement: str = Field(..., description="STRONG, MODERATE, WEAK, or INSUFFICIENT")
    scientific_content: Optional[str] = Field(None, description="STRONG, MODERATE, WEAK, or INSUFFICIENT")
    documentation: Optional[str] = Field(None, description="STRONG, MODERATE, WEAK, or INSUFFICIENT")


class DocumentationGap(BaseModel):
    """A gap in documentation that needs to be addressed"""
    category: str = Field(..., description="Category of missing documentation")
    description: str = Field(..., description="Description of what's missing")
    priority: str = Field(default="medium", description="Priority: high, medium, low")
    recommendation: Optional[str] = Field(None, description="Suggested action to address the gap")


class EligibilityRecommendation(BaseModel):
    """A recommendation for the claim"""
    title: str = Field(..., description="Short title for the recommendation")
    description: str = Field(..., description="Detailed recommendation")
    priority: str = Field(default="medium", description="Priority: high, medium, low")


class EligibilityReportRequest(BaseModel):
    """Request to generate an eligibility report"""
    include_expenditure_analysis: bool = Field(default=True, description="Include expenditure analysis")
    include_documentation_gaps: bool = Field(default=True, description="Include documentation gap analysis")


class EligibilityReport(BaseModel):
    """Full SR&ED eligibility assessment report"""
    claim_id: UUID
    generated_at: datetime

    # Overall assessment
    overall_risk_level: str = Field(..., description="LOW, MEDIUM, or HIGH")
    eligibility_summary: str = Field(..., description="Brief summary of eligibility assessment")

    # Five-question test scores
    five_question_scores: FiveQuestionScore

    # Expenditure estimates
    estimated_eligible_expenditures: Optional[Decimal] = Field(None, description="Estimated eligible costs")
    expenditure_breakdown: Optional[Dict[str, Decimal]] = Field(None, description="Breakdown by category")

    # Gaps and recommendations
    documentation_gaps: List[DocumentationGap] = Field(default_factory=list)
    recommendations: List[EligibilityRecommendation] = Field(default_factory=list)

    # Full report content
    full_report_markdown: str = Field(..., description="Complete report in Markdown format")

    # Metadata
    model_name: str = Field(..., description="AI model used")
    input_token_count: int = Field(default=0)
    output_token_count: int = Field(default=0)
    documents_analyzed: int = Field(default=0)

    # Sources referenced
    source_documents: List[Dict] = Field(default_factory=list, description="Documents cited in the report")


class EligibilityReportResponse(BaseModel):
    """API response for eligibility report"""
    success: bool
    report: Optional[EligibilityReport] = None
    error: Optional[str] = None
