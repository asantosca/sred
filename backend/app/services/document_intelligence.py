# app/services/document_intelligence.py - Document auto-detection and intelligence service for SR&ED

import re
import os
from typing import Dict, List, Optional
from datetime import datetime, date
from dataclasses import dataclass


@dataclass
class DetectedMetadata:
    """Container for auto-detected document metadata"""
    document_type: Optional[str] = None
    document_subtype: Optional[str] = None
    document_title: Optional[str] = None
    document_date: Optional[date] = None
    confidence_score: float = 0.0

    # SR&ED-specific fields
    project_name: Optional[str] = None
    fiscal_year: Optional[str] = None
    author: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None

    # Additional suggestions
    suggested_tags: List[str] = None
    confidence_notes: List[str] = None

    def __post_init__(self):
        if self.suggested_tags is None:
            self.suggested_tags = []
        if self.confidence_notes is None:
            self.confidence_notes = []


class DocumentIntelligenceService:
    """Service for auto-detecting document metadata from filenames and content for SR&ED documents"""

    def __init__(self):
        """Initialize detection patterns and rules"""
        self.filename_patterns = self._initialize_filename_patterns()
        self.content_patterns = self._initialize_content_patterns()
        self.date_patterns = self._initialize_date_patterns()

    def _initialize_filename_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize filename patterns for SR&ED document type detection"""
        return {
            "Technical Report": [
                {"pattern": r".*technical[_\s-]?report.*\.(pdf|doc|docx)$", "subtype": "technical_report", "confidence": 0.9},
                {"pattern": r".*tech[_\s-]?report.*\.(pdf|doc|docx)$", "subtype": "technical_report", "confidence": 0.8},
                {"pattern": r".*engineering[_\s-]?report.*\.(pdf|doc|docx)$", "subtype": "engineering_report", "confidence": 0.8},
                {"pattern": r".*research[_\s-]?report.*\.(pdf|doc|docx)$", "subtype": "research_report", "confidence": 0.8},
                {"pattern": r".*analysis[_\s-]?report.*\.(pdf|doc|docx)$", "subtype": "analysis_report", "confidence": 0.7},
                {"pattern": r".*test[_\s-]?report.*\.(pdf|doc|docx)$", "subtype": "test_report", "confidence": 0.8},
                {"pattern": r".*findings.*\.(pdf|doc|docx)$", "subtype": "findings", "confidence": 0.6},
            ],
            "Lab Notebook": [
                {"pattern": r".*lab[_\s-]?notebook.*\.(pdf|doc|docx)$", "subtype": "lab_notebook", "confidence": 0.9},
                {"pattern": r".*lab[_\s-]?notes.*\.(pdf|doc|docx)$", "subtype": "lab_notes", "confidence": 0.9},
                {"pattern": r".*experiment[_\s-]?log.*\.(pdf|doc|docx)$", "subtype": "experiment_log", "confidence": 0.9},
                {"pattern": r".*r&d[_\s-]?notes.*\.(pdf|doc|docx)$", "subtype": "rd_notes", "confidence": 0.8},
                {"pattern": r".*research[_\s-]?notes.*\.(pdf|doc|docx)$", "subtype": "research_notes", "confidence": 0.8},
                {"pattern": r".*dev[_\s-]?log.*\.(pdf|doc|docx)$", "subtype": "development_log", "confidence": 0.7},
                {"pattern": r".*prototype[_\s-]?notes.*\.(pdf|doc|docx)$", "subtype": "prototype_notes", "confidence": 0.8},
            ],
            "Project Plan": [
                {"pattern": r".*project[_\s-]?plan.*\.(pdf|doc|docx)$", "subtype": "project_plan", "confidence": 0.9},
                {"pattern": r".*design[_\s-]?doc.*\.(pdf|doc|docx)$", "subtype": "design_document", "confidence": 0.8},
                {"pattern": r".*specification.*\.(pdf|doc|docx)$", "subtype": "specification", "confidence": 0.7},
                {"pattern": r".*requirements.*\.(pdf|doc|docx)$", "subtype": "requirements", "confidence": 0.7},
                {"pattern": r".*architecture.*\.(pdf|doc|docx)$", "subtype": "architecture", "confidence": 0.7},
                {"pattern": r".*roadmap.*\.(pdf|doc|docx)$", "subtype": "roadmap", "confidence": 0.7},
                {"pattern": r".*proposal.*\.(pdf|doc|docx)$", "subtype": "proposal", "confidence": 0.6},
            ],
            "Timesheet": [
                {"pattern": r".*timesheet.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "timesheet", "confidence": 0.9},
                {"pattern": r".*time[_\s-]?sheet.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "timesheet", "confidence": 0.9},
                {"pattern": r".*time[_\s-]?log.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "time_log", "confidence": 0.8},
                {"pattern": r".*hours.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "hours", "confidence": 0.6},
                {"pattern": r".*labour[_\s-]?record.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "labour_record", "confidence": 0.8},
                {"pattern": r".*labor[_\s-]?record.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "labor_record", "confidence": 0.8},
            ],
            "Email": [
                {"pattern": r".*\.(eml|msg)$", "subtype": "email", "confidence": 0.9},
                {"pattern": r".*email.*\.(pdf|doc|docx)$", "subtype": "email_export", "confidence": 0.8},
                {"pattern": r".*correspondence.*\.(pdf|doc|docx)$", "subtype": "correspondence", "confidence": 0.6},
                {"pattern": r".*communication.*\.(pdf|doc|docx)$", "subtype": "communication", "confidence": 0.5},
            ],
            "Financial Record": [
                {"pattern": r".*financial.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "financial", "confidence": 0.8},
                {"pattern": r".*expense.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "expense_report", "confidence": 0.8},
                {"pattern": r".*budget.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "budget", "confidence": 0.7},
                {"pattern": r".*cost.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "cost_report", "confidence": 0.6},
                {"pattern": r".*ledger.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "ledger", "confidence": 0.8},
                {"pattern": r".*payroll.*\.(pdf|doc|docx|xlsx|xls|csv)$", "subtype": "payroll", "confidence": 0.8},
            ],
            "Invoice": [
                {"pattern": r".*invoice.*\.(pdf|doc|docx)$", "subtype": "invoice", "confidence": 0.9},
                {"pattern": r".*inv[_\s-]?\d+.*\.(pdf|doc|docx)$", "subtype": "invoice", "confidence": 0.8},
                {"pattern": r".*bill.*\.(pdf|doc|docx)$", "subtype": "bill", "confidence": 0.6},
                {"pattern": r".*receipt.*\.(pdf|doc|docx)$", "subtype": "receipt", "confidence": 0.7},
                {"pattern": r".*purchase[_\s-]?order.*\.(pdf|doc|docx)$", "subtype": "purchase_order", "confidence": 0.8},
                {"pattern": r".*po[_\s-]?\d+.*\.(pdf|doc|docx)$", "subtype": "purchase_order", "confidence": 0.7},
            ],
            "Meeting Notes": [
                {"pattern": r".*meeting[_\s-]?notes.*\.(pdf|doc|docx)$", "subtype": "meeting_notes", "confidence": 0.9},
                {"pattern": r".*minutes.*\.(pdf|doc|docx)$", "subtype": "minutes", "confidence": 0.8},
                {"pattern": r".*meeting[_\s-]?minutes.*\.(pdf|doc|docx)$", "subtype": "meeting_minutes", "confidence": 0.9},
                {"pattern": r".*standup.*\.(pdf|doc|docx)$", "subtype": "standup_notes", "confidence": 0.7},
                {"pattern": r".*retrospective.*\.(pdf|doc|docx)$", "subtype": "retrospective", "confidence": 0.7},
                {"pattern": r".*review[_\s-]?notes.*\.(pdf|doc|docx)$", "subtype": "review_notes", "confidence": 0.7},
            ],
            "Source Code": [
                {"pattern": r".*\.(py|js|ts|java|cpp|c|h|cs|go|rs|rb|php|swift|kt)$", "subtype": "source_code", "confidence": 0.9},
                {"pattern": r".*code[_\s-]?sample.*\.(pdf|doc|docx|txt)$", "subtype": "code_sample", "confidence": 0.7},
                {"pattern": r".*source.*\.(zip|tar|gz)$", "subtype": "source_archive", "confidence": 0.6},
                {"pattern": r".*commit[_\s-]?log.*\.(pdf|doc|docx|txt)$", "subtype": "commit_log", "confidence": 0.8},
                {"pattern": r".*changelog.*\.(pdf|doc|docx|txt|md)$", "subtype": "changelog", "confidence": 0.8},
            ],
        }

    def _initialize_content_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize content patterns for SR&ED document detection"""
        return {
            "technical_report_indicators": [
                {"pattern": r"ABSTRACT", "weight": 0.3},
                {"pattern": r"METHODOLOGY", "weight": 0.4},
                {"pattern": r"CONCLUSION", "weight": 0.3},
                {"pattern": r"RESULTS", "weight": 0.3},
                {"pattern": r"ANALYSIS", "weight": 0.2},
                {"pattern": r"FINDINGS", "weight": 0.3},
                {"pattern": r"EXPERIMENT", "weight": 0.3},
            ],
            "lab_notebook_indicators": [
                {"pattern": r"HYPOTHESIS", "weight": 0.5},
                {"pattern": r"OBSERVATION", "weight": 0.4},
                {"pattern": r"PROCEDURE", "weight": 0.3},
                {"pattern": r"TRIAL", "weight": 0.3},
                {"pattern": r"TEST\s+#?\d+", "weight": 0.4},
                {"pattern": r"ITERATION", "weight": 0.3},
                {"pattern": r"PROTOTYPE", "weight": 0.3},
            ],
            "project_plan_indicators": [
                {"pattern": r"OBJECTIVE", "weight": 0.4},
                {"pattern": r"MILESTONE", "weight": 0.4},
                {"pattern": r"DELIVERABLE", "weight": 0.4},
                {"pattern": r"SCOPE", "weight": 0.3},
                {"pattern": r"TIMELINE", "weight": 0.3},
                {"pattern": r"RESOURCE", "weight": 0.2},
                {"pattern": r"PHASE\s+\d+", "weight": 0.3},
            ],
            "timesheet_indicators": [
                {"pattern": r"HOURS", "weight": 0.4},
                {"pattern": r"TIME\s+ENTRY", "weight": 0.5},
                {"pattern": r"TOTAL\s+HOURS", "weight": 0.5},
                {"pattern": r"EMPLOYEE", "weight": 0.2},
                {"pattern": r"WEEK\s+(OF|ENDING)", "weight": 0.4},
                {"pattern": r"PAY\s+PERIOD", "weight": 0.4},
            ],
            "email_indicators": [
                {"pattern": r"FROM:", "weight": 0.4},
                {"pattern": r"TO:", "weight": 0.3},
                {"pattern": r"SUBJECT:", "weight": 0.4},
                {"pattern": r"SENT:", "weight": 0.3},
                {"pattern": r"CC:", "weight": 0.2},
            ],
            "financial_indicators": [
                {"pattern": r"EXPENSE", "weight": 0.4},
                {"pattern": r"REVENUE", "weight": 0.3},
                {"pattern": r"BUDGET", "weight": 0.4},
                {"pattern": r"COST\s+CENTER", "weight": 0.4},
                {"pattern": r"ACCOUNT", "weight": 0.2},
                {"pattern": r"FISCAL\s+YEAR", "weight": 0.5},
                {"pattern": r"\$[\d,]+\.\d{2}", "weight": 0.3},
            ],
            "invoice_indicators": [
                {"pattern": r"INVOICE\s*(NO|NUMBER|#)", "weight": 0.5},
                {"pattern": r"BILL\s+TO", "weight": 0.4},
                {"pattern": r"DUE\s+DATE", "weight": 0.4},
                {"pattern": r"AMOUNT\s+DUE", "weight": 0.4},
                {"pattern": r"PAYMENT\s+TERMS", "weight": 0.3},
                {"pattern": r"SUBTOTAL", "weight": 0.3},
                {"pattern": r"TAX", "weight": 0.2},
            ],
            "meeting_notes_indicators": [
                {"pattern": r"ATTENDEES", "weight": 0.5},
                {"pattern": r"AGENDA", "weight": 0.4},
                {"pattern": r"ACTION\s+ITEMS", "weight": 0.5},
                {"pattern": r"MINUTES", "weight": 0.4},
                {"pattern": r"DISCUSSION", "weight": 0.2},
                {"pattern": r"NEXT\s+STEPS", "weight": 0.3},
            ],
        }

    def _initialize_date_patterns(self) -> List[str]:
        """Initialize date extraction patterns"""
        return [
            r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",  # MM/DD/YYYY
            r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b",  # MM-DD-YYYY
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b",
            r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})\b",
            r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
            r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b",  # YYYY-MM-DD
        ]

    def detect_from_filename(self, filename: str) -> DetectedMetadata:
        """Detect document metadata from filename patterns"""
        filename_lower = filename.lower()
        detected = DetectedMetadata()

        # Try to match against each document type
        best_match = None
        best_confidence = 0.0

        for doc_type, patterns in self.filename_patterns.items():
            for pattern_config in patterns:
                pattern = pattern_config["pattern"]
                confidence = pattern_config["confidence"]

                if re.search(pattern, filename_lower, re.IGNORECASE):
                    if confidence > best_confidence:
                        best_match = {
                            "type": doc_type,
                            "subtype": pattern_config.get("subtype"),
                            "confidence": confidence
                        }
                        best_confidence = confidence

        if best_match:
            detected.document_type = best_match["type"]
            detected.document_subtype = best_match["subtype"]
            detected.confidence_score = best_match["confidence"]
            detected.confidence_notes.append(f"Filename pattern match: {best_match['confidence']:.1%}")

        # Generate document title from filename
        detected.document_title = self._generate_title_from_filename(filename)

        # Extract fiscal year if present (common in SR&ED documents)
        fy_match = re.search(r"(fy|fiscal[_\s-]?year)[_\s-]?(\d{4})", filename_lower)
        if fy_match:
            detected.fiscal_year = fy_match.group(2)
            detected.confidence_notes.append(f"Fiscal year extracted: {detected.fiscal_year}")

        return detected

    def detect_from_content(self, content: str, filename: str = None) -> DetectedMetadata:
        """Detect document metadata from content analysis"""
        detected = DetectedMetadata()
        content_upper = content.upper()

        # Map indicator types to document types
        indicator_to_type = {
            "technical_report_indicators": "Technical Report",
            "lab_notebook_indicators": "Lab Notebook",
            "project_plan_indicators": "Project Plan",
            "timesheet_indicators": "Timesheet",
            "email_indicators": "Email",
            "financial_indicators": "Financial Record",
            "invoice_indicators": "Invoice",
            "meeting_notes_indicators": "Meeting Notes",
        }

        # Score each document type based on content indicators
        type_scores = {}

        for indicator_type, patterns in self.content_patterns.items():
            score = 0.0
            for pattern_config in patterns:
                pattern = pattern_config["pattern"]
                weight = pattern_config["weight"]

                matches = len(re.findall(pattern, content_upper))
                score += matches * weight

            doc_type = indicator_to_type.get(indicator_type, "Other")
            if doc_type not in type_scores:
                type_scores[doc_type] = 0.0
            type_scores[doc_type] += score

        # Determine best match
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            best_score = type_scores[best_type]

            if best_score > 0.5:  # Minimum confidence threshold
                detected.document_type = best_type
                detected.confidence_score = min(best_score / 2.0, 0.9)  # Cap at 90%
                detected.confidence_notes.append(f"Content analysis match: {detected.confidence_score:.1%}")

        # Extract dates from content
        extracted_dates = self._extract_dates_from_content(content)
        if extracted_dates:
            detected.document_date = extracted_dates[0]  # Use first found date
            detected.confidence_notes.append(f"Date extracted from content: {len(extracted_dates)} dates found")

        # Extract email metadata if it looks like an email
        if detected.document_type == "Email":
            detected = self._extract_email_metadata(content, detected)

        return detected

    def detect_comprehensive(self, filename: str, content: str = None) -> DetectedMetadata:
        """Comprehensive detection combining filename and content analysis"""
        # Start with filename detection
        filename_detected = self.detect_from_filename(filename)

        if content:
            # Add content detection
            content_detected = self.detect_from_content(content, filename)

            # Merge results with filename taking precedence for type, content for details
            merged = DetectedMetadata()

            # Document type: prefer filename if confident, otherwise use content
            if filename_detected.confidence_score >= 0.7:
                merged.document_type = filename_detected.document_type
                merged.document_subtype = filename_detected.document_subtype
                merged.confidence_score = filename_detected.confidence_score
            elif content_detected.document_type:
                merged.document_type = content_detected.document_type
                merged.confidence_score = content_detected.confidence_score
            else:
                merged.document_type = filename_detected.document_type
                merged.document_subtype = filename_detected.document_subtype
                merged.confidence_score = filename_detected.confidence_score

            # Title: prefer filename
            merged.document_title = filename_detected.document_title

            # Date: prefer content extraction
            merged.document_date = content_detected.document_date or filename_detected.document_date

            # Merge SR&ED-specific fields
            for field in ['project_name', 'fiscal_year', 'author', 'recipient', 'subject']:
                content_value = getattr(content_detected, field)
                filename_value = getattr(filename_detected, field)
                setattr(merged, field, content_value or filename_value)

            # Merge confidence notes
            merged.confidence_notes = filename_detected.confidence_notes + content_detected.confidence_notes

            return merged

        return filename_detected

    def _generate_title_from_filename(self, filename: str) -> str:
        """Generate a clean document title from filename"""
        # Remove extension
        title = os.path.splitext(filename)[0]

        # Replace underscores and hyphens with spaces
        title = re.sub(r"[_-]", " ", title)

        # Remove common prefixes/suffixes
        title = re.sub(r"^(doc|document|file)\s*", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s*(final|draft|v\d+|version\s*\d+)$", "", title, flags=re.IGNORECASE)

        # Title case
        title = " ".join(word.capitalize() for word in title.split())

        # Limit length
        if len(title) > 100:
            title = title[:97] + "..."

        return title.strip() or filename

    def _extract_dates_from_content(self, content: str) -> List[date]:
        """Extract dates from document content"""
        dates = []

        for pattern in self.date_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    date_str = match.group(0)
                    parsed_date = self._parse_date_string(date_str)
                    if parsed_date:
                        dates.append(parsed_date)
                except:
                    continue

        # Remove duplicates and sort
        unique_dates = list(set(dates))
        unique_dates.sort()

        return unique_dates

    def _parse_date_string(self, date_str: str) -> Optional[date]:
        """Parse various date formats"""
        date_formats = [
            "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d",
            "%B %d, %Y", "%b %d, %Y", "%d %B %Y",
            "%B %d %Y", "%b %d %Y"
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    def _extract_email_metadata(self, content: str, detected: DetectedMetadata) -> DetectedMetadata:
        """Extract email-specific metadata"""
        # Extract subject
        subject_match = re.search(r"SUBJECT:\s*([^\n]+)", content, re.IGNORECASE)
        if subject_match:
            detected.subject = subject_match.group(1).strip()

        # Extract sender
        from_match = re.search(r"FROM:\s*([^\n]+)", content, re.IGNORECASE)
        if from_match:
            detected.author = from_match.group(1).strip()

        # Extract recipient
        to_match = re.search(r"TO:\s*([^\n]+)", content, re.IGNORECASE)
        if to_match:
            detected.recipient = to_match.group(1).strip()

        return detected

    def generate_suggested_tags(self, detected: DetectedMetadata, filename: str) -> List[str]:
        """Generate suggested tags based on detected metadata"""
        tags = []

        if detected.document_type:
            # Convert to lowercase tag format
            tags.append(detected.document_type.lower().replace(" ", "_"))

        if detected.document_subtype:
            tags.append(detected.document_subtype)

        if detected.fiscal_year:
            tags.append(f"fy_{detected.fiscal_year}")

        # Add year if date is available
        if detected.document_date:
            tags.append(str(detected.document_date.year))

        # Remove duplicates and return
        return list(set(tags))


# Create global service instance
document_intelligence_service = DocumentIntelligenceService()
