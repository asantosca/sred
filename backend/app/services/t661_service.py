# app/services/t661_service.py - CRA T661 form drafting service

import json
import logging
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Claim, Document, User
from app.schemas.t661 import (
    T661Draft, T661SectionDraft, T661DraftRequest, T661ProjectInfo,
    T661_SECTIONS, T661_SECTION_DESCRIPTIONS
)
from app.services.vector_storage import vector_storage_service
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


# Prompts for each T661 section
T661_SECTION_PROMPTS = {
    "part3": """You are an SR&ED tax credit specialist drafting Part 3 of CRA Form T661: Scientific or Technological Objectives.

## Project Context
Company: {company_name}
Claim Number: {claim_number}
Project Type: {project_type}

## Document Evidence
{document_excerpts}

## Instructions
Draft the "Scientific or Technological Objectives" section for this SR&ED claim.

The objectives should:
1. Be specific and measurable
2. Describe WHAT technological advancement was sought
3. Be stated in technical terms
4. NOT describe business objectives or product features
5. Be achievable through systematic R&D work

Format: Write 200-500 words in clear, professional language suitable for CRA submission.
Focus on the technological goals, not business outcomes.

Draft the section content only, no additional commentary:""",

    "part4": """You are an SR&ED tax credit specialist drafting Part 4 of CRA Form T661: Technological Uncertainties.

## Project Context
Company: {company_name}
Claim Number: {claim_number}
Project Type: {project_type}

## Document Evidence
{document_excerpts}

## Instructions
Draft the "Technological Uncertainties" section for this SR&ED claim.

The uncertainties should:
1. Describe WHAT was unknown or uncertain at the START of the project
2. Explain WHY standard practice or public knowledge couldn't resolve them
3. Be technological in nature (not market, cost, or time uncertainties)
4. Show that the outcome was not predictable
5. Be specific, not generic

Format: Write 200-500 words describing the specific technological uncertainties.
Use phrases like "It was uncertain whether...", "The challenge was to determine...", "Standard approaches could not address..."

Draft the section content only, no additional commentary:""",

    "part5": """You are an SR&ED tax credit specialist drafting Part 5 of CRA Form T661: Work Done to Address Uncertainties.

## Project Context
Company: {company_name}
Claim Number: {claim_number}
Project Type: {project_type}

## Document Evidence
{document_excerpts}

## Instructions
Draft the "Work Done to Address Uncertainties" section for this SR&ED claim.

The work description should:
1. Show SYSTEMATIC investigation (hypothesis → testing → analysis)
2. Describe specific experiments, prototypes, or trials conducted
3. Explain the methodology and approach used
4. Document iterations and what was learned from each
5. Connect the work directly to the uncertainties identified

Format: Write 300-600 words describing the systematic investigation.
Structure as: approach taken, experiments/tests conducted, analysis performed, iterations made.

Draft the section content only, no additional commentary:""",

    "part6": """You are an SR&ED tax credit specialist drafting Part 6 of CRA Form T661: Conclusions.

## Project Context
Company: {company_name}
Claim Number: {claim_number}
Project Type: {project_type}

## Document Evidence
{document_excerpts}

## Instructions
Draft the "Conclusions" section for this SR&ED claim.

The conclusions should:
1. State what was LEARNED or achieved as a result of the work
2. Describe technological advancements achieved (even if partial or negative results)
3. Explain how uncertainties were resolved or what was discovered
4. Note any new knowledge gained applicable to future work
5. Be objective about both successes and failures

Format: Write 150-300 words summarizing the technological conclusions.
Include both what worked and what didn't - CRA values honest reporting.

Draft the section content only, no additional commentary:"""
}


class T661DraftService:
    """Service for generating draft T661 form responses from project documents"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate_draft(
        self,
        claim_id: UUID,
        user: User,
        request: Optional[T661DraftRequest] = None
    ) -> T661Draft:
        """
        Generate draft T661 form sections for a claim.

        Args:
            claim_id: UUID of the claim to analyze
            user: Current user (for tenant isolation)
            request: Configuration for which sections to generate

        Returns:
            T661Draft with generated section content
        """
        logger.info(f"Generating T661 draft for claim {claim_id}")

        # Default request if not provided
        if request is None:
            request = T661DraftRequest()

        # Get claim with tenant isolation
        claim = await self._get_claim(claim_id, user.company_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found or access denied")

        # Get all documents for the claim
        documents = await self._get_claim_documents(claim_id, user.company_id)
        if not documents:
            raise ValueError(f"No documents found for claim {claim_id}")

        # Generate each requested section
        sections: List[T661SectionDraft] = []
        total_input_tokens = 0
        total_output_tokens = 0

        for section_key in request.sections:
            if section_key not in T661_SECTIONS:
                logger.warning(f"Unknown section requested: {section_key}")
                continue

            try:
                # Get relevant excerpts for this section
                excerpts = await self._get_section_excerpts(
                    section_key, claim_id, user.company_id
                )

                # Generate the section draft
                section_draft, input_tokens, output_tokens = await self._generate_section(
                    section_key=section_key,
                    claim=claim,
                    document_excerpts=excerpts,
                    max_words=request.max_words_per_section
                )

                sections.append(section_draft)
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens

            except Exception as e:
                logger.error(f"Failed to generate section {section_key}: {e}")
                # Add a placeholder section
                sections.append(T661SectionDraft(
                    section=section_key,
                    section_name=T661_SECTIONS[section_key],
                    draft_content=f"[Error generating this section: {str(e)}]",
                    word_count=0,
                    sources_cited=[],
                    confidence_notes="Generation failed - manual drafting required",
                    needs_review=True
                ))

        # Calculate completeness score
        completeness = self._calculate_completeness(sections)

        # Build project info from claim
        project_info = T661ProjectInfo(
            project_title=f"{claim.company_name} - {claim.claim_number}",
            field_of_science=claim.project_type,
            start_date=None,  # Would need to extract from documents
            end_date=claim.fiscal_year_end,
            project_description=claim.description
        )

        # Build the draft response
        draft = T661Draft(
            claim_id=claim_id,
            fiscal_year_end=claim.fiscal_year_end,
            generated_at=datetime.utcnow(),
            project_info=project_info,
            sections=sections,
            overall_completeness=completeness,
            missing_information=self._identify_missing_info(sections),
            model_name=settings.ANTHROPIC_MODEL,
            input_token_count=total_input_tokens,
            output_token_count=total_output_tokens,
            documents_analyzed=len(documents)
        )

        logger.info(
            f"Generated T661 draft for claim {claim_id}: "
            f"{len(sections)} sections, completeness={completeness:.0%}"
        )

        return draft

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

    async def _get_section_excerpts(
        self,
        section_key: str,
        claim_id: UUID,
        company_id: UUID
    ) -> str:
        """Get relevant document excerpts for a specific T661 section."""
        # Section-specific queries
        section_queries = {
            "part3": [
                "What were the technical objectives of this project?",
                "What technological goals were being pursued?",
                "What scientific or engineering targets were set?"
            ],
            "part4": [
                "What technological uncertainties existed?",
                "What challenges could not be solved with standard practice?",
                "What was unknown or unpredictable at the start?"
            ],
            "part5": [
                "What experiments or tests were conducted?",
                "What systematic approach was used to investigate?",
                "What iterations or prototypes were developed?"
            ],
            "part6": [
                "What were the results and conclusions?",
                "What technological advancements were achieved?",
                "What was learned from the R&D work?"
            ]
        }

        queries = section_queries.get(section_key, [])
        all_excerpts = []
        seen_chunks = set()

        for query in queries:
            try:
                # Generate embedding for the query
                query_embedding = await embedding_service.get_embedding(query)

                # Search for relevant chunks
                results = await vector_storage_service.similarity_search(
                    query_embedding=query_embedding,
                    company_id=company_id,
                    matter_id=claim_id,  # Note: vector storage still uses matter_id
                    limit=5,
                    similarity_threshold=0.65
                )

                for result in results:
                    chunk_id = result.get("id")
                    if chunk_id and chunk_id not in seen_chunks:
                        seen_chunks.add(chunk_id)
                        content = result.get("content", "")[:600]
                        all_excerpts.append(f"[Document Excerpt]\n{content}\n")

            except Exception as e:
                logger.warning(f"RAG search failed for query '{query}': {e}")
                continue

        if not all_excerpts:
            return "No relevant document excerpts found. Draft based on general guidance."

        return "\n---\n".join(all_excerpts[:10])  # Limit to 10 excerpts

    async def _generate_section(
        self,
        section_key: str,
        claim: Claim,
        document_excerpts: str,
        max_words: int
    ) -> tuple[T661SectionDraft, int, int]:
        """Generate a single T661 section draft."""
        prompt_template = T661_SECTION_PROMPTS.get(section_key)
        if not prompt_template:
            raise ValueError(f"No prompt template for section {section_key}")

        prompt = prompt_template.format(
            company_name=claim.company_name,
            claim_number=claim.claim_number,
            project_type=claim.project_type or "Not specified",
            document_excerpts=document_excerpts
        )

        try:
            response = await self.anthropic.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()
            word_count = len(content.split())

            # Determine if review is needed based on content quality indicators
            needs_review = (
                word_count < 100 or
                "insufficient" in content.lower() or
                "no relevant" in content.lower() or
                "[error" in content.lower()
            )

            # Extract any document references
            sources_cited = re.findall(r'\[Doc(?:ument)?:?\s*([^\]]+)\]', content)

            # Add confidence notes
            confidence_notes = None
            if word_count < 150:
                confidence_notes = "Draft is shorter than recommended. Consider adding more detail."
            elif "based on limited" in content.lower() or "no relevant" in content.lower():
                confidence_notes = "Limited evidence found in documents. Manual review required."

            section_draft = T661SectionDraft(
                section=section_key,
                section_name=T661_SECTIONS[section_key],
                draft_content=content,
                word_count=word_count,
                sources_cited=sources_cited,
                confidence_notes=confidence_notes,
                needs_review=needs_review
            )

            return (
                section_draft,
                response.usage.input_tokens,
                response.usage.output_tokens
            )

        except Exception as e:
            logger.error(f"Error generating T661 section {section_key}: {e}")
            raise

    def _calculate_completeness(self, sections: List[T661SectionDraft]) -> float:
        """Calculate overall completeness score based on section quality."""
        if not sections:
            return 0.0

        total_score = 0.0
        for section in sections:
            section_score = 0.0

            # Word count contribution (up to 0.4)
            if section.word_count >= 300:
                section_score += 0.4
            elif section.word_count >= 150:
                section_score += 0.25
            elif section.word_count >= 50:
                section_score += 0.1

            # Has sources (up to 0.3)
            if len(section.sources_cited) >= 2:
                section_score += 0.3
            elif len(section.sources_cited) >= 1:
                section_score += 0.15

            # Doesn't need urgent review (0.3)
            if not section.needs_review:
                section_score += 0.3
            elif section.confidence_notes is None:
                section_score += 0.15

            total_score += section_score

        return total_score / len(sections)

    def _identify_missing_info(self, sections: List[T661SectionDraft]) -> List[str]:
        """Identify what information is missing from the draft."""
        missing = []

        section_keys = {s.section for s in sections}

        # Check for missing sections
        required_sections = {"part3", "part4", "part5", "part6"}
        missing_sections = required_sections - section_keys
        for section in missing_sections:
            missing.append(f"Missing section: {T661_SECTIONS.get(section, section)}")

        # Check section quality
        for section in sections:
            if section.word_count < 100:
                missing.append(f"{section.section_name}: Needs more detail")
            if not section.sources_cited:
                missing.append(f"{section.section_name}: No document evidence cited")

        return missing
