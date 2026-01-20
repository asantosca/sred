# app/services/entity_extractor.py
"""
Entity Extraction Service

Lightweight regex-based entity extraction for temporal metadata and project identifiers.
Extracts dates, project names, Jira codes, and team members from document text.
"""

import re
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Contributor:
    """A project contributor with role information"""
    name: str
    title: Optional[str] = None
    role_type: str = "unknown"  # "technical", "management", "support", "unknown"
    is_qualified_personnel: bool = False  # SR&ED qualified personnel indicator
    contribution_type: str = "mentioned"  # "author", "recipient", "mentioned", "attendee"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "title": self.title,
            "role_type": self.role_type,
            "is_qualified_personnel": self.is_qualified_personnel,
            "contribution_type": self.contribution_type
        }


@dataclass
class ExtractedEntities:
    """Entities extracted from document text"""
    dates: List[str] = field(default_factory=list)
    project_names: List[str] = field(default_factory=list)
    team_members: List[str] = field(default_factory=list)
    contributors: List[Contributor] = field(default_factory=list)  # Structured contributor info
    organizations: List[str] = field(default_factory=list)
    technical_terms: List[str] = field(default_factory=list)
    jira_codes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return {
            "date_references": self.dates,
            "project_names": self.project_names,
            "team_members": self.team_members,
            "contributors": [c.to_dict() for c in self.contributors],
            "organizations": self.organizations,
            "technical_terms": self.technical_terms,
            "jira_codes": self.jira_codes
        }


class EntityExtractor:
    """
    Lightweight entity extractor using regex patterns.

    Extracts:
    - Dates in various formats
    - Project identifiers (Jira codes, project names)
    - Team member names from email headers
    - Technical terms
    """

    # Date patterns (common formats)
    DATE_PATTERNS = [
        # ISO format: 2024-03-15
        r'\b(\d{4}-\d{2}-\d{2})\b',
        # US format: 03/15/2024 or 3/15/2024
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
        # Written format: March 15, 2024 or Mar 15, 2024
        r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})\b',
        # Written format: 15 March 2024
        r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{4})\b',
        # Quarter references: Q1 2024, Q2 2024
        r'\b(Q[1-4]\s+\d{4})\b',
        # Month-Year: March 2024, Mar 2024
        r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{4})\b',
    ]

    # Project identifier patterns
    PROJECT_PATTERNS = [
        # Jira-style codes: ABC-123, PROJ-4567
        r'\b([A-Z]{2,10}-\d{1,5})\b',
        # Project name pattern: "Project Phoenix", "Project Alpha"
        r'Project\s+([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*)',
        # Feature branch style: feature/user-auth, feature/ml-model
        r'\b(?:feature|fix|hotfix)/([a-z][a-z0-9-]+)\b',
        # Internal project codes: PRJ-2024-001
        r'\b(PRJ-\d{4}-\d{3})\b',
        # Sprint references: Sprint 23, Sprint-45
        r'\b(Sprint[- ]?\d{1,3})\b',
    ]

    # Email header patterns for team member extraction (with contribution type)
    # Format: (pattern, contribution_type)
    EMAIL_PATTERNS = [
        # From: John Smith <john@example.com>
        (r'From:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*<?', 'author'),
        # To: Jane Doe <jane@example.com>
        (r'To:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*<?', 'recipient'),
        # Cc: Bob Wilson
        (r'Cc:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*<?', 'recipient'),
        # Author: Sarah Chen
        (r'Author:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', 'author'),
        # Prepared by: Mike Johnson
        (r'(?:Prepared|Written|Created|Authored)\s+by[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', 'author'),
        # @mention style: @john.smith
        (r'@([a-z]+\.[a-z]+)', 'mentioned'),
    ]

    # Patterns for extracting names with titles
    # Format: (pattern, group_for_name, group_for_title, contribution_type)
    NAME_WITH_TITLE_PATTERNS = [
        # "John Smith, Senior Developer" or "John Smith, Ph.D."
        (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),\s*([A-Z][A-Za-z\.\s]+(?:Developer|Engineer|Scientist|Researcher|Manager|Director|Lead|Architect|Analyst|Specialist|Consultant|Ph\.?D\.?|Dr\.|M\.?Sc\.?|P\.?Eng\.?))', 1, 2, 'mentioned'),
        # "Dr. John Smith" or "Dr John Smith"
        (r'(Dr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', 1, None, 'mentioned'),
        # Signature blocks: "Name\nTitle" pattern
        (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\n\s*([A-Z][A-Za-z\s]+(?:Developer|Engineer|Scientist|Researcher|Manager|Director|Lead|Architect|Analyst))', 1, 2, 'author'),
        # "Name | Title" pattern (common in email signatures)
        (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\|\s*([A-Z][A-Za-z\s]+(?:Developer|Engineer|Scientist|Researcher|Manager|Director|Lead|Architect))', 1, 2, 'author'),
        # Meeting attendees: "- John Smith (Developer)"
        (r'[-•]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(([^)]+)\)', 1, 2, 'attendee'),
    ]

    # Technical/qualified personnel titles (for SR&ED)
    TECHNICAL_TITLES = {
        'developer', 'engineer', 'scientist', 'researcher', 'architect',
        'programmer', 'analyst', 'technician', 'specialist', 'consultant',
        'phd', 'ph.d', 'ph.d.', 'dr', 'dr.', 'm.sc', 'm.sc.', 'p.eng', 'p.eng.',
        'senior developer', 'senior engineer', 'staff engineer', 'principal engineer',
        'software engineer', 'software developer', 'data scientist', 'data engineer',
        'machine learning engineer', 'ml engineer', 'ai researcher', 'research scientist',
        'technical lead', 'tech lead', 'team lead', 'engineering lead',
        'solutions architect', 'systems architect', 'cloud architect',
        'devops engineer', 'sre', 'site reliability engineer',
        'qa engineer', 'test engineer', 'automation engineer',
        'firmware engineer', 'embedded engineer', 'hardware engineer',
        'network engineer', 'security engineer', 'backend engineer', 'frontend engineer',
        'full stack developer', 'full-stack developer', 'fullstack developer',
    }

    # Management titles
    MANAGEMENT_TITLES = {
        'manager', 'director', 'vp', 'vice president', 'cto', 'ceo', 'cio',
        'project manager', 'program manager', 'product manager', 'engineering manager',
        'technical director', 'r&d director', 'research director',
        'head of engineering', 'head of development', 'head of research',
        'chief scientist', 'chief architect', 'chief engineer',
    }

    # Support/admin titles (not qualified personnel for SR&ED)
    SUPPORT_TITLES = {
        'coordinator', 'administrator', 'assistant', 'secretary', 'clerk',
        'hr', 'human resources', 'finance', 'accounting', 'marketing', 'sales',
        'receptionist', 'office manager', 'executive assistant',
    }

    # Technical term indicators
    TECH_TERM_PATTERNS = [
        # Acronyms: API, ML, AI, NLP (3+ uppercase letters)
        r'\b([A-Z]{3,})\b',
        # CamelCase: TensorFlow, PyTorch
        r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b',
        # Version numbers: v2.0, 1.5.3
        r'\b(v?\d+\.\d+(?:\.\d+)?)\b',
    ]

    # Month name mapping for date normalization
    MONTH_MAP = {
        'january': '01', 'jan': '01',
        'february': '02', 'feb': '02',
        'march': '03', 'mar': '03',
        'april': '04', 'apr': '04',
        'may': '05',
        'june': '06', 'jun': '06',
        'july': '07', 'jul': '07',
        'august': '08', 'aug': '08',
        'september': '09', 'sep': '09',
        'october': '10', 'oct': '10',
        'november': '11', 'nov': '11',
        'december': '12', 'dec': '12',
    }

    def __init__(self):
        """Initialize the extractor with compiled patterns"""
        self.date_patterns = [re.compile(p, re.IGNORECASE) for p in self.DATE_PATTERNS]
        self.project_patterns = [re.compile(p) for p in self.PROJECT_PATTERNS]
        # Compile email patterns with contribution type
        self.email_patterns = [
            (re.compile(p, re.IGNORECASE), contrib_type)
            for p, contrib_type in self.EMAIL_PATTERNS
        ]
        # Compile name with title patterns
        self.name_title_patterns = [
            (re.compile(p, re.IGNORECASE), name_grp, title_grp, contrib_type)
            for p, name_grp, title_grp, contrib_type in self.NAME_WITH_TITLE_PATTERNS
        ]
        self.tech_patterns = [re.compile(p) for p in self.TECH_TERM_PATTERNS]
        logger.info("EntityExtractor initialized")

    def extract_entities(self, text: str) -> ExtractedEntities:
        """
        Extract named entities and metadata from text.

        Args:
            text: Document text

        Returns:
            ExtractedEntities object with all extracted entities
        """
        if not text or len(text.strip()) < 10:
            return ExtractedEntities()

        # Limit text length for performance (first 100k chars)
        text_sample = text[:100000]

        # Extract each entity type
        dates = self._extract_dates(text_sample)
        project_names, jira_codes = self._extract_project_identifiers(text_sample)
        team_members = self._extract_team_members(text_sample)
        contributors = self._extract_contributors(text_sample)
        technical_terms = self._extract_technical_terms(text_sample)

        return ExtractedEntities(
            dates=dates[:20],  # Limit to 20 dates
            project_names=project_names[:10],
            team_members=team_members[:20],
            contributors=contributors[:30],  # Limit to 30 contributors
            organizations=[],  # Placeholder - could add org extraction
            technical_terms=technical_terms[:30],
            jira_codes=jira_codes[:20]
        )

    def _extract_dates(self, text: str) -> List[str]:
        """Extract and normalize dates from text"""
        dates = set()

        for pattern in self.date_patterns:
            matches = pattern.findall(text)
            for match in matches:
                normalized = self._normalize_date(match)
                if normalized:
                    dates.add(normalized)

        return sorted(list(dates))

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Attempt to normalize date to ISO format (YYYY-MM-DD).
        Returns None if unable to parse.
        """
        date_str = date_str.strip().replace('.', '')

        # Already ISO format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str

        # US format: MM/DD/YYYY
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
        if match:
            month, day, year = match.groups()
            try:
                return f"{year}-{int(month):02d}-{int(day):02d}"
            except ValueError:
                return None

        # Written format: Month DD, YYYY
        match = re.match(r'^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$', date_str)
        if match:
            month_name, day, year = match.groups()
            month_num = self.MONTH_MAP.get(month_name.lower())
            if month_num:
                return f"{year}-{month_num}-{int(day):02d}"

        # Written format: DD Month YYYY
        match = re.match(r'^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$', date_str)
        if match:
            day, month_name, year = match.groups()
            month_num = self.MONTH_MAP.get(month_name.lower())
            if month_num:
                return f"{year}-{month_num}-{int(day):02d}"

        # Quarter: Q1 2024 -> 2024-01-01 (start of quarter)
        match = re.match(r'^Q([1-4])\s+(\d{4})$', date_str)
        if match:
            quarter, year = match.groups()
            quarter_start_month = {'1': '01', '2': '04', '3': '07', '4': '10'}
            return f"{year}-{quarter_start_month[quarter]}-01"

        # Month-Year: March 2024 -> 2024-03-01
        match = re.match(r'^([A-Za-z]+)\s+(\d{4})$', date_str)
        if match:
            month_name, year = match.groups()
            month_num = self.MONTH_MAP.get(month_name.lower())
            if month_num:
                return f"{year}-{month_num}-01"

        return None

    def _extract_project_identifiers(self, text: str) -> tuple[List[str], List[str]]:
        """Extract project names and Jira codes"""
        project_names = set()
        jira_codes = set()

        for pattern in self.project_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Jira-style codes go in jira_codes
                if re.match(r'^[A-Z]{2,10}-\d{1,5}$', match):
                    jira_codes.add(match)
                else:
                    # Clean up project names
                    clean_name = match.strip()
                    if len(clean_name) >= 3:
                        project_names.add(clean_name)

        return list(project_names), list(jira_codes)

    def _extract_team_members(self, text: str) -> List[str]:
        """Extract team member names from email headers and attribution"""
        members = set()

        for pattern, contrib_type in self.email_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Clean up name
                name = match.strip() if isinstance(match, str) else match
                # Filter out obvious non-names
                if self._is_valid_name(name):
                    members.add(name)

        return list(members)

    def _extract_contributors(self, text: str) -> List['Contributor']:
        """
        Extract contributors with titles and roles from text.

        Returns structured Contributor objects with:
        - Name
        - Title (if found)
        - Role type (technical, management, support)
        - Qualified personnel indicator (for SR&ED)
        - Contribution type (author, recipient, mentioned, attendee)
        """
        contributors_dict: Dict[str, Contributor] = {}  # name -> Contributor

        # 1. Extract from name-with-title patterns (highest quality)
        for pattern, name_grp, title_grp, contrib_type in self.name_title_patterns:
            for match in pattern.finditer(text):
                try:
                    name = match.group(name_grp).strip() if name_grp else match.group(1).strip()

                    # Handle "Dr. John Smith" - extract just the name part
                    if name.lower().startswith('dr.') or name.lower().startswith('dr '):
                        name = name[3:].strip()
                        title = "Dr."
                    elif title_grp:
                        title = match.group(title_grp).strip() if match.lastindex >= title_grp else None
                    else:
                        title = None

                    if not self._is_valid_name(name):
                        continue

                    # Classify role type and qualified personnel
                    role_type, is_qualified = self._classify_title(title)

                    # Update or create contributor
                    if name in contributors_dict:
                        # Update with better info if available
                        existing = contributors_dict[name]
                        if title and not existing.title:
                            existing.title = title
                            existing.role_type = role_type
                            existing.is_qualified_personnel = is_qualified
                        # Upgrade contribution type (author > recipient > mentioned)
                        existing.contribution_type = self._better_contribution_type(
                            existing.contribution_type, contrib_type
                        )
                    else:
                        contributors_dict[name] = Contributor(
                            name=name,
                            title=title,
                            role_type=role_type,
                            is_qualified_personnel=is_qualified,
                            contribution_type=contrib_type
                        )
                except (IndexError, AttributeError):
                    continue

        # 2. Extract from email patterns (for names without titles)
        for pattern, contrib_type in self.email_patterns:
            for match in pattern.finditer(text):
                try:
                    name = match.group(1).strip()

                    if not self._is_valid_name(name):
                        continue

                    if name not in contributors_dict:
                        contributors_dict[name] = Contributor(
                            name=name,
                            title=None,
                            role_type="unknown",
                            is_qualified_personnel=False,
                            contribution_type=contrib_type
                        )
                    else:
                        # Upgrade contribution type if better
                        existing = contributors_dict[name]
                        existing.contribution_type = self._better_contribution_type(
                            existing.contribution_type, contrib_type
                        )
                except (IndexError, AttributeError):
                    continue

        return list(contributors_dict.values())

    def _classify_title(self, title: Optional[str]) -> tuple:
        """
        Classify a job title into role type and qualified personnel status.

        Returns:
            (role_type, is_qualified_personnel)
        """
        if not title:
            return ("unknown", False)

        title_lower = title.lower().strip()

        # Check for technical titles (qualified personnel for SR&ED)
        for tech_title in self.TECHNICAL_TITLES:
            if tech_title in title_lower:
                return ("technical", True)

        # Check for management titles (may be qualified if technical management)
        for mgmt_title in self.MANAGEMENT_TITLES:
            if mgmt_title in title_lower:
                # Technical management is still qualified
                if any(t in title_lower for t in ['technical', 'engineering', 'r&d', 'research', 'development']):
                    return ("management", True)
                return ("management", False)

        # Check for support titles (not qualified)
        for support_title in self.SUPPORT_TITLES:
            if support_title in title_lower:
                return ("support", False)

        # Default: unknown but might be qualified if has technical keywords
        if any(t in title_lower for t in ['tech', 'dev', 'eng', 'research', 'science']):
            return ("technical", True)

        return ("unknown", False)

    def _better_contribution_type(self, current: str, new: str) -> str:
        """Return the higher-value contribution type"""
        priority = {'author': 4, 'attendee': 3, 'recipient': 2, 'mentioned': 1}
        if priority.get(new, 0) > priority.get(current, 0):
            return new
        return current

    def _is_valid_name(self, name: str) -> bool:
        """Check if a string looks like a valid person name"""
        # Must be at least 2 words (first and last name)
        parts = name.split()
        if len(parts) < 2:
            return False

        # Each part should be capitalized and reasonable length
        for part in parts:
            if len(part) < 2 or len(part) > 20:
                return False
            if not part[0].isupper():
                return False

        # Filter out common false positives
        false_positives = {
            'Dear Sir', 'Dear Madam', 'Best Regards', 'Kind Regards',
            'Yours Truly', 'Thank You', 'Please Note', 'For Example'
        }
        if name in false_positives:
            return False

        return True

    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract likely technical terms (acronyms, CamelCase, versions)"""
        terms = set()

        # Common non-technical acronyms to filter out
        skip_acronyms = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL',
            'CAN', 'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY',
            'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW',
            'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID',
            'USA', 'CEO', 'CFO', 'CTO', 'COO', 'EVP', 'SVP', 'VP'
        }

        for pattern in self.tech_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Skip common words and very short terms
                if match.upper() in skip_acronyms:
                    continue
                if len(match) < 3:
                    continue

                terms.add(match)

        return list(terms)

    def extract_date_range(self, text: str) -> Optional[Dict]:
        """
        Extract earliest and latest dates from text.

        Returns:
            Dict with 'earliest' and 'latest' dates, or None if no dates found
        """
        entities = self.extract_entities(text)
        dates = entities.dates

        if not dates:
            return None

        # Filter to valid ISO dates and sort
        valid_dates = [d for d in dates if re.match(r'^\d{4}-\d{2}-\d{2}$', d)]
        if not valid_dates:
            return None

        valid_dates.sort()

        return {
            'earliest': valid_dates[0],
            'latest': valid_dates[-1],
            'count': len(valid_dates)
        }


class ProjectNameNormalizer:
    """
    Normalizes and groups project names to handle variations.

    Handles cases like:
    - "Project AURORA" → "AURORA"
    - "AURORA-2024" → "AURORA"
    - "Project AURORA 2024" → "AURORA"
    - "aurora" → "AURORA"
    """

    # Patterns to strip from project names
    PREFIX_PATTERNS = [
        r'^project\s+',  # "Project AURORA" -> "AURORA"
        r'^prj[_-]?',    # "PRJ-AURORA" -> "AURORA"
        r'^proj[_-]?',   # "PROJ_AURORA" -> "AURORA"
    ]

    SUFFIX_PATTERNS = [
        r'[-_\s]?20\d{2}$',           # "AURORA-2024" -> "AURORA"
        r'[-_\s]?v\d+(\.\d+)*$',      # "AURORA-v2.0" -> "AURORA"
        r'[-_\s]?phase\s*\d+$',       # "AURORA Phase 2" -> "AURORA"
        r'[-_\s]?\d+$',               # "AURORA 3" -> "AURORA" (trailing numbers)
    ]

    # Common words that are NOT project names (extracted from "Project X" patterns)
    STOPWORDS = {
        # Project management terms
        'KICKOFF', 'KICK_OFF', 'LEAD', 'LEADER', 'MANAGER', 'MANAGEMENT',
        'PLAN', 'PLANNING', 'SCOPE', 'TIMELINE', 'SCHEDULE', 'MILESTONE',
        'PHASE', 'STAGE', 'STATUS', 'UPDATE', 'REPORT', 'REVIEW', 'MEETING',
        'TEAM', 'MEMBER', 'RESOURCE', 'BUDGET', 'COST', 'ESTIMATE',
        'REQUIREMENT', 'REQUIREMENTS', 'SPECIFICATION', 'SPECIFICATIONS',
        'DELIVERABLE', 'DELIVERABLES', 'OBJECTIVE', 'OBJECTIVES', 'GOAL', 'GOALS',
        # Technical terms
        'CODE', 'CODING', 'DEVELOPMENT', 'DESIGN', 'ARCHITECTURE',
        'TEST', 'TESTING', 'IMPLEMENTATION', 'DEPLOYMENT', 'RELEASE',
        'DOCUMENTATION', 'DOCUMENT', 'DOCS', 'ANALYSIS', 'RESEARCH',
        # Generic terms
        'NAME', 'TITLE', 'DESCRIPTION', 'SUMMARY', 'OVERVIEW', 'DETAILS',
        'START', 'END', 'BEGIN', 'FINISH', 'COMPLETE', 'COMPLETION',
        'NEW', 'OLD', 'CURRENT', 'PREVIOUS', 'NEXT', 'FUTURE',
        'INTERNAL', 'EXTERNAL', 'MAIN', 'PRIMARY', 'SECONDARY',
        # Document-related terms
        'DOCUMENT', 'DOCUMENTS', 'FILE', 'FILES', 'FOLDER', 'FOLDERS',
        'ATTACHMENT', 'ATTACHMENTS', 'APPENDIX', 'APPENDICES',
        # Role/person terms
        'RESEARCHER', 'DEVELOPER', 'ENGINEER', 'ANALYST', 'CONSULTANT',
        'DIRECTOR', 'COORDINATOR', 'SPECIALIST', 'ADMINISTRATOR',
        # SR&ED specific
        'SRED', 'CLAIM', 'ELIGIBLE', 'EXPENDITURE', 'CREDIT',
    }

    def __init__(self):
        """Initialize with compiled patterns"""
        self.prefix_patterns = [re.compile(p, re.IGNORECASE) for p in self.PREFIX_PATTERNS]
        self.suffix_patterns = [re.compile(p, re.IGNORECASE) for p in self.SUFFIX_PATTERNS]

    def normalize(self, name: str) -> str:
        """
        Extract canonical form of a project name.

        Args:
            name: Raw project name (e.g., "Project AURORA-2024")

        Returns:
            Canonical form (e.g., "AURORA"), or empty string if it's a stopword
        """
        if not name:
            return ""

        # Start with the original name
        result = name.strip()

        # Remove prefixes
        for pattern in self.prefix_patterns:
            result = pattern.sub('', result)

        # Remove suffixes
        for pattern in self.suffix_patterns:
            result = pattern.sub('', result)

        # Clean up and normalize
        result = result.strip()
        result = re.sub(r'[-_\s]+', '_', result)  # Normalize separators to underscore
        result = result.upper()

        # Handle edge case where normalization removed everything
        if not result:
            result = name.upper().strip()

        # Filter out stopwords (common words that aren't project names)
        # Check if the entire name OR any word in it is a stopword
        if result in self.STOPWORDS:
            return ""

        # Check if any word in the name is a stopword (handles "KICKOFF_DOCUMENT" etc.)
        words = result.split('_')
        for word in words:
            if word in self.STOPWORDS:
                return ""

        return result

    def are_similar(self, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """
        Check if two project names are similar enough to be the same project.

        Uses normalized form comparison plus fuzzy matching for variations.

        Args:
            name1: First project name
            name2: Second project name
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            True if names likely refer to the same project
        """
        if not name1 or not name2:
            return False

        # Normalize both names
        norm1 = self.normalize(name1)
        norm2 = self.normalize(name2)

        # Exact match after normalization
        if norm1 == norm2:
            return True

        # One contains the other (handles "AURORA" vs "AURORA_ML")
        if norm1 in norm2 or norm2 in norm1:
            # Only if the difference is small
            len_diff = abs(len(norm1) - len(norm2))
            max_len = max(len(norm1), len(norm2))
            if len_diff / max_len < 0.3:  # Less than 30% length difference
                return True

        # Fuzzy matching using Levenshtein-like ratio
        similarity = self._string_similarity(norm1, norm2)
        return similarity >= threshold

    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate string similarity ratio (simplified Levenshtein-based).

        Returns value between 0.0 (no similarity) and 1.0 (identical).
        """
        if s1 == s2:
            return 1.0

        if not s1 or not s2:
            return 0.0

        # Calculate Levenshtein distance
        len1, len2 = len(s1), len(s2)

        # Use shorter/longer for ratio calculation
        if len1 > len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1

        # Dynamic programming for edit distance
        current_row = list(range(len1 + 1))

        for i in range(1, len2 + 1):
            previous_row = current_row
            current_row = [i] + [0] * len1

            for j in range(1, len1 + 1):
                add = previous_row[j] + 1
                delete = current_row[j - 1] + 1
                change = previous_row[j - 1]

                if s1[j - 1] != s2[i - 1]:
                    change += 1

                current_row[j] = min(add, delete, change)

        distance = current_row[len1]
        max_len = max(len1, len2)

        return 1.0 - (distance / max_len)

    def group_by_similarity(
        self,
        names: List[str],
        threshold: float = 0.8
    ) -> Dict[str, List[str]]:
        """
        Group similar project names together.

        Args:
            names: List of project names to group
            threshold: Similarity threshold for grouping

        Returns:
            Dict mapping canonical name to list of original variations
        """
        if not names:
            return {}

        groups: Dict[str, List[str]] = {}
        canonical_map: Dict[str, str] = {}  # Maps normalized form to group key

        for name in names:
            if not name:
                continue

            normalized = self.normalize(name)

            # Skip stopwords (normalize returns empty string)
            if not normalized:
                continue

            # Check if this matches an existing group
            matched_group = None
            for group_key, group_normalized in canonical_map.items():
                if self.are_similar(normalized, group_normalized, threshold):
                    matched_group = group_key
                    break

            if matched_group:
                # Add to existing group
                if name not in groups[matched_group]:
                    groups[matched_group].append(name)
            else:
                # Create new group
                groups[normalized] = [name]
                canonical_map[normalized] = normalized

        return groups

    def get_canonical_name(self, variations: List[str]) -> str:
        """
        Choose the best canonical name from a list of variations.

        Prefers:
        1. Names without year suffixes
        2. Shorter names
        3. Names with more uppercase letters (suggests official name)

        Args:
            variations: List of project name variations

        Returns:
            Best canonical name
        """
        if not variations:
            return ""

        if len(variations) == 1:
            return self.normalize(variations[0])

        # Score each variation
        scored = []
        for name in variations:
            score = 0

            # Prefer names without years
            if not re.search(r'20\d{2}', name):
                score += 10

            # Prefer shorter normalized names
            normalized = self.normalize(name)
            score -= len(normalized) * 0.1

            # Prefer uppercase (official names tend to be uppercase)
            uppercase_ratio = sum(1 for c in name if c.isupper()) / max(len(name), 1)
            score += uppercase_ratio * 5

            scored.append((score, name, normalized))

        # Sort by score descending
        scored.sort(reverse=True)

        return scored[0][2]  # Return normalized form of best match


# Singleton instances
entity_extractor = EntityExtractor()
project_name_normalizer = ProjectNameNormalizer()
