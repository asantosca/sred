# app/services/eligibility_report_service.py - SR&ED eligibility report generation

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Claim, Document, User
from app.schemas.eligibility import (
    EligibilityReport, FiveQuestionScore, DocumentationGap,
    EligibilityRecommendation, EligibilityReportRequest
)
from app.services.vector_storage import vector_storage_service
from app.services.embeddings import embedding_service

logger = logging.getLogger(__name__)


# Prompt for eligibility assessment
ELIGIBILITY_ASSESSMENT_PROMPT = """You are an SR&ED (Scientific Research and Experimental Development) tax credit specialist for PwC. Analyze the following project documentation and generate a comprehensive eligibility assessment.

## Project Context
Company: {company_name}
Claim Number: {claim_number}
Project Type: {project_type}
Fiscal Year End: {fiscal_year_end}

## Document Summaries
{document_summaries}

## Relevant Document Excerpts
{document_excerpts}

## Your Task
Generate a detailed SR&ED eligibility assessment in the following JSON format:

```json
{{
  "overall_risk_level": "LOW|MEDIUM|HIGH",
  "eligibility_summary": "2-3 sentence summary of overall eligibility assessment",
  "five_question_scores": {{
    "technological_uncertainty": "STRONG|MODERATE|WEAK|INSUFFICIENT",
    "systematic_investigation": "STRONG|MODERATE|WEAK|INSUFFICIENT",
    "technological_advancement": "STRONG|MODERATE|WEAK|INSUFFICIENT",
    "scientific_content": "STRONG|MODERATE|WEAK|INSUFFICIENT",
    "documentation": "STRONG|MODERATE|WEAK|INSUFFICIENT"
  }},
  "documentation_gaps": [
    {{
      "category": "Category name",
      "description": "What is missing",
      "priority": "high|medium|low",
      "recommendation": "How to address this gap"
    }}
  ],
  "recommendations": [
    {{
      "title": "Short title",
      "description": "Detailed recommendation",
      "priority": "high|medium|low"
    }}
  ],
  "full_report_markdown": "Complete report in Markdown format (see structure below)"
}}
```

## Full Report Structure (for full_report_markdown)
The full_report_markdown should follow this structure:

# SR&ED Eligibility Assessment

## Executive Summary
Brief overview of the project and eligibility assessment.

## Five-Question Test Analysis

### 1. Technological Uncertainty
Analysis of whether technological uncertainties existed that could not be resolved by standard practice.

### 2. Systematic Investigation
Analysis of whether a systematic investigation was conducted (hypothesis, testing, analysis).

### 3. Technological Advancement
Analysis of whether the work sought to achieve technological advancement.

### 4. Scientific/Technical Content
Analysis of the scientific or technical content of the work.

### 5. Documentation Quality
Assessment of the documentation quality and completeness.

## Risk Assessment
Overall risk level with explanation.

## Documentation Gaps
List of identified gaps in the documentation with recommendations.

## Recommendations
Prioritized list of actions to strengthen the claim.

## Conclusion
Final assessment and next steps.

---

IMPORTANT Guidelines:
- Base your assessment ONLY on the provided documentation
- Be specific about evidence found (or not found) in the documents
- Use [Doc: title] notation when referencing specific documents
- Be conservative in scoring - if evidence is thin, score accordingly
- Focus on CRA's eligibility criteria
- Provide actionable recommendations

Respond with ONLY the JSON object, no additional text."""


class EligibilityReportService:
    """Service for generating SR&ED eligibility assessment reports"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate_report(
        self,
        claim_id: UUID,
        user: User,
        request: Optional[EligibilityReportRequest] = None
    ) -> EligibilityReport:
        """
        Generate an SR&ED eligibility report for a claim.

        Args:
            claim_id: UUID of the claim to analyze
            user: Current user (for tenant isolation)
            request: Optional configuration for report generation

        Returns:
            EligibilityReport with full assessment
        """
        logger.info(f"Generating eligibility report for claim {claim_id}")

        # Get claim with tenant isolation
        claim = await self._get_claim(claim_id, user.company_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found or access denied")

        # Get all documents for the claim
        documents = await self._get_claim_documents(claim_id, user.company_id)
        if not documents:
            raise ValueError(f"No documents found for claim {claim_id}")

        # Build document summaries
        document_summaries = self._format_document_summaries(documents)

        # Get relevant document excerpts via RAG
        document_excerpts = await self._get_relevant_excerpts(
            claim_id, user.company_id
        )

        # Generate the report using Claude
        report_data, input_tokens, output_tokens = await self._generate_assessment(
            claim=claim,
            document_summaries=document_summaries,
            document_excerpts=document_excerpts
        )

        # Build the report response
        report = EligibilityReport(
            claim_id=claim_id,
            generated_at=datetime.utcnow(),
            overall_risk_level=report_data.get("overall_risk_level", "MEDIUM"),
            eligibility_summary=report_data.get("eligibility_summary", ""),
            five_question_scores=FiveQuestionScore(
                **report_data.get("five_question_scores", {
                    "technological_uncertainty": "INSUFFICIENT",
                    "systematic_investigation": "INSUFFICIENT",
                    "technological_advancement": "INSUFFICIENT",
                    "scientific_content": "INSUFFICIENT",
                    "documentation": "INSUFFICIENT"
                })
            ),
            documentation_gaps=[
                DocumentationGap(**gap)
                for gap in report_data.get("documentation_gaps", [])
            ],
            recommendations=[
                EligibilityRecommendation(**rec)
                for rec in report_data.get("recommendations", [])
            ],
            full_report_markdown=report_data.get("full_report_markdown", ""),
            model_name=settings.ANTHROPIC_MODEL,
            input_token_count=input_tokens,
            output_token_count=output_tokens,
            documents_analyzed=len(documents),
            source_documents=[
                {
                    "id": str(doc.id),
                    "title": doc.document_title,
                    "type": doc.document_type
                }
                for doc in documents
            ]
        )

        logger.info(
            f"Generated eligibility report for claim {claim_id}: "
            f"risk={report.overall_risk_level}, docs={len(documents)}"
        )

        return report

    async def _get_claim(self, claim_id: UUID, company_id: UUID) -> Optional[Claim]:
        """Get claim with tenant isolation."""
        query = select(Claim).where(
            Claim.id == claim_id,
            Claim.company_id == company_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_claim_documents(
        self,
        claim_id: UUID,
        company_id: UUID
    ) -> List[Document]:
        """Get all documents for a claim."""
        query = select(Document).join(Claim).where(
            Document.claim_id == claim_id,
            Claim.company_id == company_id
        ).order_by(Document.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _format_document_summaries(self, documents: List[Document]) -> str:
        """Format document summaries for the prompt."""
        if not documents:
            return "No documents available."

        summaries = []
        for doc in documents:
            summary = doc.ai_summary or "No summary available"
            summaries.append(
                f"### {doc.document_title}\n"
                f"- Type: {doc.document_type}\n"
                f"- Uploaded: {doc.created_at.strftime('%Y-%m-%d')}\n"
                f"- Summary: {summary}\n"
            )

        return "\n".join(summaries)

    async def _get_relevant_excerpts(
        self,
        claim_id: UUID,
        company_id: UUID
    ) -> str:
        """Get relevant document excerpts using RAG."""
        # Key questions to search for eligibility evidence
        eligibility_queries = [
            "What technological uncertainties or challenges existed in this project?",
            "What systematic investigation or experiments were conducted?",
            "What technological advancements were achieved or attempted?",
            "What R&D methodologies or approaches were used?",
            "What were the project objectives and outcomes?"
        ]

        all_excerpts = []
        seen_chunks = set()

        for query in eligibility_queries:
            try:
                # Generate embedding for the query
                query_embedding = await embedding_service.get_embedding(query)

                # Search for relevant chunks
                results = await vector_storage_service.similarity_search(
                    query_embedding=query_embedding,
                    company_id=company_id,
                    matter_id=claim_id,  # Note: vector storage still uses matter_id
                    limit=3,
                    similarity_threshold=0.7
                )

                for result in results:
                    chunk_id = result.get("id")
                    if chunk_id and chunk_id not in seen_chunks:
                        seen_chunks.add(chunk_id)
                        content = result.get("content", "")[:500]
                        all_excerpts.append(f"[Excerpt]\n{content}\n")

            except Exception as e:
                logger.warning(f"RAG search failed for query '{query}': {e}")
                continue

        if not all_excerpts:
            return "No relevant excerpts found via search."

        return "\n---\n".join(all_excerpts[:15])  # Limit to 15 excerpts

    async def _generate_assessment(
        self,
        claim: Claim,
        document_summaries: str,
        document_excerpts: str
    ) -> tuple[Dict[str, Any], int, int]:
        """Generate the eligibility assessment using Claude."""
        prompt = ELIGIBILITY_ASSESSMENT_PROMPT.format(
            company_name=claim.company_name,
            claim_number=claim.claim_number,
            project_type=claim.project_type or "Not specified",
            fiscal_year_end=claim.fiscal_year_end.isoformat() if claim.fiscal_year_end else "Not specified",
            document_summaries=document_summaries,
            document_excerpts=document_excerpts
        )

        try:
            response = await self.anthropic.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Parse JSON response (handle potential markdown code blocks)
            if response_text.startswith("```"):
                import re
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            report_data = json.loads(response_text)

            return (
                report_data,
                response.usage.input_tokens,
                response.usage.output_tokens
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse eligibility assessment JSON: {e}")
            # Return a minimal valid response
            return (
                {
                    "overall_risk_level": "HIGH",
                    "eligibility_summary": "Unable to generate assessment due to parsing error.",
                    "five_question_scores": {
                        "technological_uncertainty": "INSUFFICIENT",
                        "systematic_investigation": "INSUFFICIENT",
                        "technological_advancement": "INSUFFICIENT",
                        "scientific_content": "INSUFFICIENT",
                        "documentation": "INSUFFICIENT"
                    },
                    "documentation_gaps": [],
                    "recommendations": [{
                        "title": "Manual Review Required",
                        "description": "The automated assessment could not be completed. Please review the documents manually.",
                        "priority": "high"
                    }],
                    "full_report_markdown": "# Assessment Error\n\nUnable to generate automated assessment. Please review documents manually."
                },
                0,
                0
            )
        except Exception as e:
            logger.error(f"Error generating eligibility assessment: {e}", exc_info=True)
            raise
