# app/services/workspace_service.py
"""
Workspace Service for Project Discovery

Manages the collaborative markdown workspace for project discovery:
- Converts discovered projects to markdown with AI-generated narratives
- Parses markdown back to structured data
- Detects document changes for incremental updates
"""

import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Any
from uuid import UUID
from dataclasses import dataclass

from anthropic import AsyncAnthropic
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import (
    Conversation, Document, Claim, Project, DocumentProjectTag
)
from app.services.project_discovery_service import ProjectCandidate
from app.services.usage_logging import usage_logging_service

logger = logging.getLogger(__name__)


@dataclass
class ParsedProject:
    """Structured project data parsed from markdown"""
    name: str
    start_date: Optional[str] = None
    start_context: Optional[str] = None
    end_date: Optional[str] = None
    end_context: Optional[str] = None
    contributors: List[Dict[str, str]] = None
    documents: List[Dict[str, str]] = None
    narrative_uncertainty: Optional[str] = None
    narrative_objective: Optional[str] = None
    narrative_investigation: Optional[str] = None
    narrative_outcome: Optional[str] = None

    def __post_init__(self):
        if self.contributors is None:
            self.contributors = []
        if self.documents is None:
            self.documents = []


class WorkspaceService:
    """Service for managing project discovery workspace"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def get_or_create_workspace(
        self,
        claim_id: UUID,
        company_id: UUID,
        user_id: UUID
    ) -> Conversation:
        """
        Get or create the project workspace conversation for a claim.

        Each claim has exactly one project_workspace conversation.
        """
        # Try to find existing workspace
        query = select(Conversation).where(
            and_(
                Conversation.claim_id == claim_id,
                Conversation.company_id == company_id,
                Conversation.conversation_type == "project_workspace"
            )
        )
        result = await self.db.execute(query)
        workspace = result.scalar_one_or_none()

        if workspace:
            return workspace

        # Create new workspace conversation
        workspace = Conversation(
            company_id=company_id,
            user_id=user_id,
            claim_id=claim_id,
            title="Project Discovery Workspace",
            conversation_type="project_workspace",
            workspace_md="",
            known_document_ids=[]
        )
        self.db.add(workspace)
        await self.db.commit()
        await self.db.refresh(workspace)

        return workspace

    async def update_workspace_markdown(
        self,
        workspace_id: UUID,
        markdown: str,
        company_id: UUID
    ) -> Conversation:
        """Update the workspace markdown content."""
        query = select(Conversation).where(
            and_(
                Conversation.id == workspace_id,
                Conversation.company_id == company_id,
                Conversation.conversation_type == "project_workspace"
            )
        )
        result = await self.db.execute(query)
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise ValueError("Workspace not found")

        workspace.workspace_md = markdown
        workspace.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(workspace)

        return workspace

    async def generate_workspace_markdown(
        self,
        candidates: List[ProjectCandidate],
        claim: Claim,
        documents: List[Document],
        generate_narratives: bool = True
    ) -> str:
        """
        Convert discovered project candidates to workspace markdown.

        Args:
            candidates: List of ProjectCandidate from discovery
            claim: The claim being analyzed
            documents: All documents for the claim
            generate_narratives: Whether to generate AI narratives

        Returns:
            Markdown content for the workspace
        """
        if not candidates:
            return self._generate_empty_workspace(claim)

        # Build document lookup by ID
        doc_lookup = {doc.id: doc for doc in documents}

        # Generate markdown for each project
        sections = []
        for i, candidate in enumerate(candidates, 1):
            section = await self._generate_project_section(
                project_num=i,
                candidate=candidate,
                doc_lookup=doc_lookup,
                claim=claim,
                generate_narratives=generate_narratives
            )
            sections.append(section)

        # Calculate summary statistics
        summary = self._generate_summary_statistics(candidates, documents)

        # Build header
        header = f"""# Project Discovery Workspace
## {claim.company_name} - FY {claim.fiscal_year_end.year if claim.fiscal_year_end else 'N/A'}

{summary}

---
"""
        return header + "\n\n".join(sections)

    def _generate_summary_statistics(
        self,
        candidates: List[ProjectCandidate],
        documents: List[Document]
    ) -> str:
        """Generate summary statistics section."""
        # Count by confidence level
        high_conf = sum(1 for c in candidates if c.confidence >= 0.7)
        medium_conf = sum(1 for c in candidates if 0.4 <= c.confidence < 0.7)
        low_conf = sum(1 for c in candidates if c.confidence < 0.4)

        # Aggregate SR&ED signals
        total_uncertainty = sum(c.signals.get("uncertainty", 0) for c in candidates)
        total_systematic = sum(c.signals.get("systematic", 0) for c in candidates)
        total_advancement = sum(c.signals.get("advancement", 0) for c in candidates)

        # Count unique contributors
        all_contributors = set()
        for c in candidates:
            for contrib in c.contributors:
                name = contrib.get("name", "")
                if name:
                    all_contributors.add(name)

        # Count documents by type
        doc_types = {}
        for doc in documents:
            dtype = doc.document_type or "other"
            doc_types[dtype] = doc_types.get(dtype, 0) + 1

        # Calculate review status
        needs_review = sum(1 for c in candidates if c.confidence < 0.7 or not c.contributors)
        ready_count = len(candidates) - needs_review

        lines = [
            f"### Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| **Projects Discovered** | {len(candidates)} |",
            f"| **High Confidence** | {high_conf} |",
            f"| **Needs Review** | {medium_conf + low_conf} |",
            f"| **Total Documents** | {len(documents)} |",
            f"| **Team Members Identified** | {len(all_contributors)} |",
            f"",
            f"#### SR&ED Signal Strength",
            f"",
            f"| Signal Type | Count | Strength |",
            f"|-------------|-------|----------|",
            f"| Technological Uncertainty | {total_uncertainty} | {self._signal_strength(total_uncertainty, len(candidates))} |",
            f"| Systematic Investigation | {total_systematic} | {self._signal_strength(total_systematic, len(candidates))} |",
            f"| Technological Advancement | {total_advancement} | {self._signal_strength(total_advancement, len(candidates))} |",
            f"",
            f"#### Review Status",
            f"",
            f"- {ready_count} project(s) ready for T661 drafting",
            f"- {needs_review} project(s) need additional review",
        ]

        return "\n".join(lines)

    def _signal_strength(self, count: int, num_projects: int) -> str:
        """Convert signal count to strength indicator."""
        if num_projects == 0:
            return "—"
        avg = count / num_projects
        if avg >= 5:
            return "🟢 Strong"
        elif avg >= 2:
            return "🟡 Moderate"
        elif avg >= 1:
            return "🟠 Weak"
        else:
            return "🔴 Missing"

    async def _generate_project_section(
        self,
        project_num: int,
        candidate: ProjectCandidate,
        doc_lookup: Dict[UUID, Document],
        claim: Claim,
        generate_narratives: bool
    ) -> str:
        """Generate markdown section for a single project."""
        lines = []

        # Determine review status
        review_status = self._get_review_status(candidate)

        # Project header with confidence badge
        confidence_pct = int(candidate.confidence * 100)
        confidence_badge = self._get_confidence_badge(candidate.confidence)
        lines.append(f"## Project {project_num}: {candidate.name}")
        lines.append("")
        lines.append(f"> {confidence_badge} **Confidence: {confidence_pct}%** | {review_status}")
        lines.append("")

        # SR&ED Signals section
        lines.append("### SR&ED Signals")
        uncertainty = candidate.signals.get("uncertainty", 0)
        systematic = candidate.signals.get("systematic", 0)
        advancement = candidate.signals.get("advancement", 0)
        failure = candidate.signals.get("failure", 0)

        lines.append("")
        lines.append(f"| Signal | Count | Assessment |")
        lines.append(f"|--------|-------|------------|")
        lines.append(f"| Technological Uncertainty | {uncertainty} | {self._assess_signal(uncertainty, 'uncertainty')} |")
        lines.append(f"| Systematic Investigation | {systematic} | {self._assess_signal(systematic, 'systematic')} |")
        lines.append(f"| Technological Advancement | {advancement} | {self._assess_signal(advancement, 'advancement')} |")
        if failure > 0:
            lines.append(f"| Failed Approaches | {failure} | Documents challenges faced |")
        lines.append("")

        # Dates section
        lines.append("### Project Timeline")
        if candidate.start_date:
            start_str = candidate.start_date.strftime("%B %d, %Y")
            lines.append(f"- **Start**: {start_str} *(first documentation of technological uncertainty)*")
        else:
            lines.append("- **Start**: ⚠️ *Not determined - review documents for project initiation*")

        if candidate.end_date:
            end_str = candidate.end_date.strftime("%B %d, %Y")
            lines.append(f"- **End**: {end_str} *(resolution of uncertainty or latest activity)*")
        else:
            lines.append("- **End**: *Ongoing or not determined*")
        lines.append("")

        # Contributors section
        lines.append("### Qualified Personnel")
        if candidate.contributors:
            # Separate technical vs other contributors
            technical = [c for c in candidate.contributors if c.get("role_type") == "technical"]
            others = [c for c in candidate.contributors if c.get("role_type") != "technical"]

            if technical:
                lines.append("")
                lines.append("**Technical Staff** (directly involved in R&D):")
                for contrib in technical[:8]:
                    lines.append(self._format_contributor(contrib))

            if others:
                lines.append("")
                lines.append("**Supporting Staff**:")
                for contrib in others[:5]:
                    lines.append(self._format_contributor(contrib))
        else:
            lines.append("- ⚠️ *No contributors identified - review documents for personnel*")
        lines.append("")

        # Documents section
        lines.append("### Supporting Documents")
        if candidate.documents:
            lines.append("")
            lines.append(f"*{len(candidate.documents)} document(s) linked to this project*")
            lines.append("")
            for doc_id in candidate.documents[:15]:  # Top 15
                doc = doc_lookup.get(doc_id)
                if doc:
                    date_str = doc.document_date.strftime("%Y-%m-%d") if doc.document_date else "N/A"
                    doc_type = doc.document_type.replace("_", " ").title() if doc.document_type else "Document"
                    lines.append(f"- [{doc.filename}](doc:{doc_id}) — {doc_type}, {date_str}")
        else:
            lines.append("- ⚠️ *No documents linked*")
        lines.append("")

        # Narrative section
        lines.append("### T661 Narrative Draft")
        lines.append("")
        lines.append(f"> {review_status}")
        lines.append("")
        if generate_narratives:
            narrative = await self._generate_project_narrative(candidate, doc_lookup)
            lines.append(narrative)
        else:
            lines.append(self._generate_placeholder_narrative())

        lines.append("")
        lines.append("---")

        return "\n".join(lines)

    def _get_confidence_badge(self, confidence: float) -> str:
        """Get emoji badge for confidence level."""
        if confidence >= 0.7:
            return "🟢"
        elif confidence >= 0.4:
            return "🟡"
        else:
            return "🔴"

    def _get_review_status(self, candidate: ProjectCandidate) -> str:
        """Determine review status for a project."""
        issues = []

        if candidate.confidence < 0.4:
            issues.append("low confidence")
        if not candidate.contributors:
            issues.append("no personnel identified")
        if not candidate.start_date:
            issues.append("missing start date")
        if candidate.signals.get("uncertainty", 0) == 0:
            issues.append("no uncertainty signals")

        if not issues:
            return "✅ **Ready for T661**"
        elif len(issues) == 1:
            return f"⚠️ **Needs Review**: {issues[0]}"
        else:
            return f"⚠️ **Needs Review**: {', '.join(issues)}"

    def _assess_signal(self, count: int, signal_type: str) -> str:
        """Assess signal strength with CRA-relevant context."""
        if signal_type == "uncertainty":
            if count >= 3:
                return "✅ Strong evidence of technological uncertainty"
            elif count >= 1:
                return "⚠️ Some uncertainty indicators - strengthen narrative"
            else:
                return "❌ Missing - critical for SR&ED eligibility"
        elif signal_type == "systematic":
            if count >= 5:
                return "✅ Clear systematic investigation documented"
            elif count >= 2:
                return "⚠️ Some methodology shown - add more detail"
            else:
                return "❌ Weak - document hypothesis/testing approach"
        elif signal_type == "advancement":
            if count >= 2:
                return "✅ Technological advancement documented"
            elif count >= 1:
                return "⚠️ Some advancement - clarify what was learned"
            else:
                return "⚠️ Missing - document knowledge gained"
        return "—"

    def _format_contributor(self, contrib: Dict) -> str:
        """Format a contributor line."""
        name = contrib.get("name", "Unknown")
        title = contrib.get("title", "")
        is_qualified = contrib.get("is_qualified_personnel", False)

        line = f"- {name}"
        if title:
            line += f", {title}"
        if is_qualified:
            line += " ✓"
        return line

    async def _generate_project_narrative(
        self,
        candidate: ProjectCandidate,
        doc_lookup: Dict[UUID, Document]
    ) -> str:
        """Generate AI narrative for a project using Claude, aligned with CRA T661 requirements."""
        # Build context from documents
        doc_excerpts = []
        for doc_id in candidate.documents[:5]:  # Sample first 5 docs
            doc = doc_lookup.get(doc_id)
            if doc and doc.extracted_text:
                excerpt = doc.extracted_text[:2000]
                doc_excerpts.append(f"[{doc.filename}]: {excerpt}")

        context = "\n\n".join(doc_excerpts)

        # Get contributor names for context
        contributors = ", ".join([c.get("name", "") for c in candidate.contributors[:5] if c.get("name")])

        prompt = f"""You are a SR&ED (Scientific Research and Experimental Development) tax credit specialist helping draft T661 form narratives for CRA (Canada Revenue Agency) submission.

Based on the project documentation below, draft narrative sections for project "{candidate.name}".

IMPORTANT CRA REQUIREMENTS:
- Focus on TECHNOLOGICAL uncertainties, not business/market uncertainties
- Describe what could NOT be accomplished using standard practice or publicly available knowledge
- Show systematic investigation: hypothesis → experimentation → analysis
- Emphasize knowledge gained, even from failed approaches

Structure your response with these EXACT headers (matching T661 form lines):

**Line 242: Technological Uncertainties**
[2-3 sentences answering: "What scientific or technological uncertainties did you attempt to overcome?"]
- Start with "The project faced technological uncertainty regarding..."
- Focus on what was unknown at the START of the work
- Explain why existing solutions/knowledge were insufficient

**Line 244: Work Performed**
[3-4 sentences answering: "What work did you perform in the tax year to overcome the uncertainties?"]
- Describe the systematic approach (hypothesis, testing, iterations)
- Mention specific technical activities (design, prototyping, testing, analysis)
- Reference team expertise where relevant

**Line 246: Technological Advancements**
[2-3 sentences answering: "What scientific or technological advancements did you achieve or attempt to achieve?"]
- Describe NEW knowledge or capabilities gained
- Even partial solutions or failed approaches count if they advanced understanding
- Focus on technical achievements, not business outcomes

PROJECT CONTEXT:
- Team members: {contributors if contributors else 'Not identified'}
- Period: {candidate.start_date.strftime('%B %Y') if candidate.start_date else 'Unknown'} to {candidate.end_date.strftime('%B %Y') if candidate.end_date else 'ongoing'}
- SR&ED signal strength: Uncertainty={candidate.signals.get('uncertainty', 0)}, Systematic={candidate.signals.get('systematic', 0)}, Advancement={candidate.signals.get('advancement', 0)}

DOCUMENT EXCERPTS:
{context if context else 'No document excerpts available - generate placeholder based on project name.'}

Generate a professional draft suitable for CRA review. Use technical language appropriate for the domain. If information is missing, use [PLACEHOLDER: description] markers.
"""

        try:
            response = await self.anthropic.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}]
            )

            # Log usage
            await usage_logging_service.log_usage(
                service="claude_chat",
                operation="workspace_narrative_generation",
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                model_name=settings.ANTHROPIC_MODEL,
                db=self.db
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Failed to generate narrative for {candidate.name}: {e}")
            return self._generate_placeholder_narrative()

    def _generate_placeholder_narrative(self) -> str:
        """Generate placeholder narrative when AI generation fails or is disabled."""
        return """**Line 242: Technological Uncertainties**
*[PLACEHOLDER: Describe what scientific or technological uncertainties existed at the start of the project. What could not be accomplished using standard practice or publicly available knowledge?]*

**Line 244: Work Performed**
*[PLACEHOLDER: Describe the systematic investigation conducted - what hypotheses were tested, what experiments/prototypes were built, what analysis was performed?]*

**Line 246: Technological Advancements**
*[PLACEHOLDER: Describe what new knowledge or capabilities were gained. What did you learn that you didn't know before, even if the project didn't fully succeed?]*"""

    def _generate_empty_workspace(self, claim: Claim) -> str:
        """Generate empty workspace markdown when no projects discovered."""
        return f"""# Project Discovery Workspace
## {claim.company_name} - FY {claim.fiscal_year_end.year if claim.fiscal_year_end else 'N/A'}

*No projects discovered yet. Upload documents and run discovery to get started.*

---

### Tips for Better Discovery

1. **Upload R&D documents** - Technical reports, design docs, lab notebooks
2. **Include communication** - Emails and meeting notes with project discussions
3. **Add timesheets** - Help identify team members and project timelines

Click **Run Discovery** to analyze your documents and identify SR&ED projects.
"""

    async def detect_document_changes(
        self,
        claim_id: UUID,
        company_id: UUID,
        known_document_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare current documents against known document IDs.

        Returns:
            {
                "has_changes": bool,
                "new_documents": [Document],
                "removed_document_ids": [str],
                "current_document_ids": [str]
            }
        """
        # Fetch current processed documents
        query = select(Document).where(
            and_(
                Document.claim_id == claim_id,
                Document.company_id == company_id,
                Document.processing_status.in_(['embedded', 'complete']),
                Document.indexed_for_search == True
            )
        )
        result = await self.db.execute(query)
        current_docs = list(result.scalars().all())

        current_ids = {str(doc.id) for doc in current_docs}
        known_ids = set(known_document_ids) if known_document_ids else set()

        new_ids = current_ids - known_ids
        removed_ids = known_ids - current_ids

        new_documents = [doc for doc in current_docs if str(doc.id) in new_ids]

        return {
            "has_changes": bool(new_ids or removed_ids),
            "new_documents": new_documents,
            "removed_document_ids": list(removed_ids),
            "current_document_ids": list(current_ids)
        }

    def parse_markdown_to_projects(self, markdown: str) -> List[ParsedProject]:
        """
        Parse workspace markdown back to structured project data.

        This is useful for:
        - Extracting data for T661 form generation
        - Validating changes made in chat
        - Syncing with database Project records
        """
        projects = []

        # Split by project headers (## Project N: ...)
        project_pattern = r'^## Project \d+: (.+)$'
        sections = re.split(r'(?=^## Project \d+:)', markdown, flags=re.MULTILINE)

        for section in sections:
            if not section.strip() or not re.match(project_pattern, section.strip(), re.MULTILINE):
                continue

            project = self._parse_project_section(section)
            if project:
                projects.append(project)

        return projects

    def _parse_project_section(self, section: str) -> Optional[ParsedProject]:
        """Parse a single project section from markdown."""
        lines = section.strip().split('\n')
        if not lines:
            return None

        # Extract project name from header
        header_match = re.match(r'^## Project \d+: (.+)$', lines[0])
        if not header_match:
            return None

        project = ParsedProject(name=header_match.group(1))

        current_subsection = None
        narrative_section = None
        narrative_content = []

        for line in lines[1:]:
            line = line.strip()

            # Check for subsection headers
            if line.startswith('### '):
                current_subsection = line[4:].lower()
                if current_subsection == 'narrative':
                    narrative_section = True
                continue

            # Parse based on current subsection
            if current_subsection == 'dates':
                self._parse_date_line(line, project)
            elif current_subsection == 'contributors':
                self._parse_contributor_line(line, project)
            elif current_subsection == 'documents':
                self._parse_document_line(line, project)
            elif narrative_section:
                self._parse_narrative_line(line, project, narrative_content)

        return project

    def _parse_date_line(self, line: str, project: ParsedProject):
        """Parse a date line from the Dates section."""
        if line.startswith('- **Start**:'):
            content = line.replace('- **Start**:', '').strip()
            # Extract date and context
            match = re.match(r'([A-Z][a-z]+ \d+, \d{4})\s*\((.+)\)', content)
            if match:
                project.start_date = match.group(1)
                project.start_context = match.group(2)
        elif line.startswith('- **End**:'):
            content = line.replace('- **End**:', '').strip()
            match = re.match(r'([A-Z][a-z]+ \d+, \d{4})\s*\((.+)\)', content)
            if match:
                project.end_date = match.group(1)
                project.end_context = match.group(2)

    def _parse_contributor_line(self, line: str, project: ParsedProject):
        """Parse a contributor line."""
        if not line.startswith('- ') or line.startswith('- *'):
            return

        content = line[2:].strip()
        parts = content.split(', ')

        contributor = {"name": parts[0]}
        if len(parts) > 1:
            # Check for role in parentheses
            role_match = re.match(r'(.+)\s*\((.+)\)$', parts[1])
            if role_match:
                contributor["title"] = role_match.group(1).strip()
                contributor["role"] = role_match.group(2).strip()
            else:
                contributor["title"] = parts[1].strip()

        project.contributors.append(contributor)

    def _parse_document_line(self, line: str, project: ParsedProject):
        """Parse a document link line."""
        if not line.startswith('- ') or line.startswith('- *'):
            return

        # Match pattern: - [filename](doc:uuid) - date
        match = re.match(r'- \[(.+)\]\(doc:([a-f0-9-]+)\)\s*-?\s*(.*)$', line)
        if match:
            project.documents.append({
                "filename": match.group(1),
                "id": match.group(2),
                "date": match.group(3).strip() if match.group(3) else None
            })

    def _parse_narrative_line(
        self,
        line: str,
        project: ParsedProject,
        content_buffer: List[str]
    ):
        """Parse narrative content."""
        # Check for narrative headers
        if line.startswith('**Technological Uncertainty'):
            content_buffer.clear()
            content_buffer.append('uncertainty')
        elif line.startswith('**Objective'):
            # Save previous section
            if content_buffer and content_buffer[0] == 'uncertainty':
                project.narrative_uncertainty = '\n'.join(content_buffer[1:])
            content_buffer.clear()
            content_buffer.append('objective')
        elif line.startswith('**Systematic Investigation'):
            if content_buffer and content_buffer[0] == 'objective':
                project.narrative_objective = '\n'.join(content_buffer[1:])
            content_buffer.clear()
            content_buffer.append('investigation')
        elif line.startswith('**Outcome'):
            if content_buffer and content_buffer[0] == 'investigation':
                project.narrative_investigation = '\n'.join(content_buffer[1:])
            content_buffer.clear()
            content_buffer.append('outcome')
        elif line.startswith('---'):
            # End of project section
            if content_buffer and content_buffer[0] == 'outcome':
                project.narrative_outcome = '\n'.join(content_buffer[1:])
        elif line and content_buffer:
            content_buffer.append(line)


def get_workspace_service(db: AsyncSession) -> WorkspaceService:
    """Factory function to create WorkspaceService with database session"""
    return WorkspaceService(db)
