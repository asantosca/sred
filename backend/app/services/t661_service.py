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
    T661_SECTIONS, T661_SECTION_DESCRIPTIONS, T661_WORD_LIMITS,
    SourceCitation, T661StreamlineRequest, T661StreamlineResponse
)
from app.services.vector_storage import vector_storage_service
from app.services.embeddings import embedding_service

logger = logging.getLogger(__name__)


# Prompts for each T661 box (aligned with CRA Form T661 structure)
T661_SECTION_PROMPTS = {
    "box242": """You are an SR&ED tax credit specialist drafting Line 242 of CRA Form T661.

## CRA Question (Line 242)
"What scientific or technological uncertainties did you attempt to overcome?"
(Maximum 350 words)

## Project Context
Company: {company_name}
Claim Number: {claim_number}
Project Type: {project_type}

## Document Evidence (with source IDs)
{document_excerpts}

## Instructions
Draft the response for Line 242. According to CRA guidance, your response should:

1. **Include the project objective** - What scientific knowledge or new/improved capability were you seeking?
2. **Describe the technological uncertainty** - What was unknown or uncertain that could not be determined from generally available scientific or technological knowledge?
3. **Explain the knowledge gap** - What was the existing knowledge base at the onset? What were its shortcomings or limitations that prevented you from overcoming the uncertainties?

The uncertainty must be TECHNOLOGICAL in nature (not market, cost, or time uncertainties). It should show that the outcome was not predictable based on standard practice.

CRITICAL: CITE SOURCES using [X] notation (e.g., [1], [2]) whenever you reference information from the documents.

Use phrases like: "The objective was to...", "It was uncertain whether...", "Standard approaches could not address...", "The existing knowledge base lacked..."

Draft the section content only (aim for ~350 words), no additional commentary:""",

    "box244": """You are an SR&ED tax credit specialist drafting Line 244 of CRA Form T661.

## CRA Question (Line 244)
"What work did you perform in the tax year to overcome the technological obstacles/uncertainties described in Line 242?"
(Maximum 700 words)

## Project Context
Company: {company_name}
Claim Number: {claim_number}
Project Type: {project_type}

## Document Evidence (with source IDs)
{document_excerpts}

## Instructions
Draft the response for Line 244. According to CRA guidance, your response should:

1. **Describe work in chronological order** - Present the investigation timeline clearly
2. **Demonstrate systematic investigation** - Show hypothesis → testing → analysis cycle
3. **Detail specific activities** - Experiments, prototypes, trials, iterations conducted
4. **Show the methodology** - What approach was used and why
5. **Document learning from each iteration** - What was learned and how it informed next steps

The work described must connect directly to the uncertainties identified in Line 242.

CRITICAL: CITE SOURCES using [X] notation (e.g., [1], [2]) whenever you reference information from the documents.

Structure chronologically: initial approach → tests/experiments → analysis → iterations → refinements.

Draft the section content only (aim for ~700 words), no additional commentary:""",

    "box246": """You are an SR&ED tax credit specialist drafting Line 246 of CRA Form T661.

## CRA Question (Line 246)
"What scientific or technological advancements did you achieve or attempt to achieve as a result of the work described in Line 244?"
(Maximum 350 words)

## Project Context
Company: {company_name}
Claim Number: {claim_number}
Project Type: {project_type}

## Document Evidence (with source IDs)
{document_excerpts}

## Instructions
Draft the response for Line 246. According to CRA guidance, your response should:

1. **State what was learned or achieved** - Describe the technological advancement gained
2. **Include partial or negative results** - CRA values honest reporting; failed attempts that generated knowledge count
3. **Explain how uncertainties were resolved** - Connect back to Line 242
4. **Note new knowledge gained** - What can be applied to future work?
5. **Be objective** - Report both successes and failures

Remember: An advancement doesn't have to be a complete success. Discovering that an approach doesn't work IS a valid advancement if it adds to technological knowledge.

CRITICAL: CITE SOURCES using [X] notation (e.g., [1], [2]) whenever you reference information from the documents.

Draft the section content only (aim for ~350 words), no additional commentary:"""
}

# Prompt for streamlining content
STREAMLINE_PROMPT = """Condense this SR&ED T661 form section while preserving all essential content.

Current word count: {current_words}
Target word count: {target_words} (CRA limit)

CRITICAL REQUIREMENTS:
1. Preserve ALL source citations [X] - do not remove any
2. Keep all technical specifics (dates, metrics, technologies, names)
3. Maintain factual accuracy - do not change meaning
4. Keep evidence of SR&ED eligibility criteria (uncertainty, advancement, systematic approach)

Techniques to reduce length:
- Remove redundant phrases and filler words
- Combine related sentences
- Use active voice
- Replace phrases with single words where possible
- Remove unnecessary qualifiers

Original text:
{text}

Condensed version (target ~{target_words} words):"""


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
                # Get relevant excerpts for this section (now returns tuple)
                excerpts, source_citations = await self._get_section_excerpts(
                    section_key, claim_id, user.company_id
                )

                # Generate the section draft
                section_draft, input_tokens, output_tokens = await self._generate_section(
                    section_key=section_key,
                    claim=claim,
                    document_excerpts=excerpts,
                    source_citations=source_citations,
                    max_words=request.max_words_per_section
                )

                sections.append(section_draft)
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens

            except Exception as e:
                logger.error(f"Failed to generate section {section_key}: {e}")
                # Add a placeholder section with word limit info
                word_limit = T661_WORD_LIMITS.get(section_key, 350)
                sections.append(T661SectionDraft(
                    section=section_key,
                    section_name=T661_SECTIONS[section_key],
                    draft_content=f"[Error generating this section: {str(e)}]",
                    word_count=0,
                    word_limit=word_limit,
                    is_over_limit=False,
                    words_over=0,
                    sources=[],
                    sources_cited=[],
                    evidence_strength="insufficient",
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
    ) -> tuple[str, List[SourceCitation]]:
        """
        Get relevant document excerpts for a specific T661 section.

        Returns:
            Tuple of (formatted excerpts string, list of SourceCitation objects)
        """
        # Box-specific queries (aligned with CRA T661 structure)
        section_queries = {
            "box242": [
                "What were the project objectives and technological goals?",
                "What technological uncertainties existed at the start?",
                "What challenges could not be solved with standard practice or existing knowledge?",
                "What was unknown or unpredictable about achieving the objective?"
            ],
            "box244": [
                "What experiments or tests were conducted?",
                "What systematic approach was used to investigate?",
                "What iterations or prototypes were developed?",
                "What methodology was followed in chronological order?"
            ],
            "box246": [
                "What were the results and conclusions?",
                "What technological advancements were achieved?",
                "What was learned from the R&D work?",
                "What new knowledge or capabilities were gained?"
            ]
        }

        queries = section_queries.get(section_key, [])
        all_excerpts = []
        source_citations: List[SourceCitation] = []
        seen_chunks = set()
        citation_id = 1

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
                        doc_title = result.get("document_title", "Unknown Document")
                        doc_id = result.get("document_id")
                        similarity = result.get("similarity", 0.0)
                        page_num = result.get("page_number")

                        # Add formatted excerpt with citation ID
                        all_excerpts.append(
                            f"[{citation_id}] Source: {doc_title}\n{content}\n"
                        )

                        # Create SourceCitation object
                        source_citations.append(SourceCitation(
                            citation_id=citation_id,
                            document_id=UUID(doc_id) if doc_id else UUID('00000000-0000-0000-0000-000000000000'),
                            document_title=doc_title,
                            chunk_id=UUID(chunk_id) if chunk_id else None,
                            page_number=page_num,
                            excerpt=content[:200] + "..." if len(content) > 200 else content,
                            relevance_score=float(similarity) if similarity else 0.0
                        ))

                        citation_id += 1

            except Exception as e:
                logger.warning(f"RAG search failed for query '{query}': {e}")
                continue

        if not all_excerpts:
            return ("No relevant document excerpts found. Draft based on general guidance.", [])

        # Limit to 10 excerpts
        formatted_excerpts = "\n---\n".join(all_excerpts[:10])
        return (formatted_excerpts, source_citations[:10])

    async def _generate_section(
        self,
        section_key: str,
        claim: Claim,
        document_excerpts: str,
        source_citations: List[SourceCitation],
        max_words: int
    ) -> tuple[T661SectionDraft, int, int]:
        """Generate a single T661 section draft with source citations and word limit tracking."""
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
                max_tokens=2000,  # Increased for comprehensive drafts
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()
            word_count = self._count_words(content)

            # Get word limit for this section
            word_limit = T661_WORD_LIMITS.get(section_key, 350)
            is_over_limit = word_count > word_limit
            words_over = max(0, word_count - word_limit)

            # Determine if review is needed based on content quality indicators
            needs_review = (
                word_count < 100 or
                "insufficient" in content.lower() or
                "no relevant" in content.lower() or
                "[error" in content.lower()
            )

            # Extract citation IDs used in the content
            citations_used = set(re.findall(r'\[(\d+)\]', content))

            # Filter source_citations to only those actually used in the content
            used_sources = [
                src for src in source_citations
                if str(src.citation_id) in citations_used
            ]

            # Also keep legacy format for backward compatibility
            sources_cited = [src.document_title for src in used_sources]

            # Assess evidence strength
            evidence_strength = self._assess_evidence_strength(used_sources)

            # Add confidence notes
            confidence_notes = None
            if word_count < 150:
                confidence_notes = "Draft is shorter than recommended. Consider adding more detail."
            elif "based on limited" in content.lower() or "no relevant" in content.lower():
                confidence_notes = "Limited evidence found in documents. Manual review required."
            elif evidence_strength == "insufficient":
                confidence_notes = "No document sources cited. Manual review required."
            elif evidence_strength == "weak":
                confidence_notes = "Limited document evidence. Consider adding more supporting documentation."

            section_draft = T661SectionDraft(
                section=section_key,
                section_name=T661_SECTIONS[section_key],
                draft_content=content,
                word_count=word_count,
                word_limit=word_limit,
                is_over_limit=is_over_limit,
                words_over=words_over,
                sources=used_sources,
                sources_cited=sources_cited,
                evidence_strength=evidence_strength,
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

    def _count_words(self, text: str) -> int:
        """Count words excluding citation markers like [1], [2], etc."""
        # Remove citation markers before counting
        clean_text = re.sub(r'\[\d+\]', '', text)
        return len(clean_text.split())

    def _count_citations(self, text: str) -> int:
        """Count unique citation markers in text."""
        citations = set(re.findall(r'\[(\d+)\]', text))
        return len(citations)

    def _assess_evidence_strength(self, sources: List[SourceCitation]) -> str:
        """Assess evidence strength based on source count and relevance."""
        if not sources:
            return "insufficient"

        # Calculate average relevance score
        avg_relevance = sum(s.relevance_score for s in sources) / len(sources)

        if len(sources) >= 3 and avg_relevance >= 0.7:
            return "strong"
        elif len(sources) >= 2 or (len(sources) >= 1 and avg_relevance >= 0.8):
            return "moderate"
        elif len(sources) >= 1:
            return "weak"
        return "insufficient"

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

        # Check for missing boxes
        required_sections = {"box242", "box244", "box246"}
        missing_sections = required_sections - section_keys
        for section in missing_sections:
            missing.append(f"Missing box: {T661_SECTIONS.get(section, section)}")

        # Check section quality
        for section in sections:
            if section.word_count < 100:
                missing.append(f"{section.section_name}: Needs more detail")
            if not section.sources_cited and not section.sources:
                missing.append(f"{section.section_name}: No document evidence cited")

        return missing

    async def streamline_section(
        self,
        request: T661StreamlineRequest,
        user: User
    ) -> T661StreamlineResponse:
        """
        Streamline (condense) a T661 section while preserving meaning and citations.

        Args:
            request: Streamline request with section content and target words
            user: Current user for authentication

        Returns:
            T661StreamlineResponse with original and condensed content
        """
        logger.info(f"Streamlining T661 section {request.section}")

        # Get target word count (use CRA limit if not specified)
        target_words = request.target_words or T661_WORD_LIMITS.get(request.section, 350)

        # Count original words and citations
        original_word_count = self._count_words(request.current_content)
        original_citations = self._count_citations(request.current_content)

        # If already under limit, return as-is
        if original_word_count <= target_words:
            return T661StreamlineResponse(
                section=request.section,
                original_content=request.current_content,
                streamlined_content=request.current_content,
                original_word_count=original_word_count,
                new_word_count=original_word_count,
                words_reduced=0,
                target_word_count=target_words,
                is_within_limit=True,
                citations_preserved=True,
                citations_in_original=original_citations,
                citations_in_result=original_citations
            )

        # Build the streamline prompt
        prompt = STREAMLINE_PROMPT.format(
            current_words=original_word_count,
            target_words=target_words,
            text=request.current_content
        )

        try:
            response = await self.anthropic.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            streamlined_content = response.content[0].text.strip()
            new_word_count = self._count_words(streamlined_content)
            new_citations = self._count_citations(streamlined_content)

            # Check if citations were preserved
            citations_preserved = new_citations >= original_citations
            if request.preserve_citations and not citations_preserved:
                logger.warning(
                    f"Citations may have been lost during streamlining: "
                    f"{original_citations} -> {new_citations}"
                )

            return T661StreamlineResponse(
                section=request.section,
                original_content=request.current_content,
                streamlined_content=streamlined_content,
                original_word_count=original_word_count,
                new_word_count=new_word_count,
                words_reduced=original_word_count - new_word_count,
                target_word_count=target_words,
                is_within_limit=new_word_count <= target_words,
                citations_preserved=citations_preserved,
                citations_in_original=original_citations,
                citations_in_result=new_citations
            )

        except Exception as e:
            logger.error(f"Error streamlining T661 section {request.section}: {e}")
            raise
