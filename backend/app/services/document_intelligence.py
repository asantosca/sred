# app/services/document_intelligence.py - Document auto-detection and intelligence service

import re
import os
from typing import Dict, List, Optional, Tuple
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
    
    # Type-specific fields
    contract_type: Optional[str] = None
    court_jurisdiction: Optional[str] = None
    case_number: Optional[str] = None
    opposing_party: Optional[str] = None
    author: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None
    discovery_type: Optional[str] = None
    exhibit_number: Optional[str] = None
    
    # Additional suggestions
    suggested_tags: List[str] = None
    confidence_notes: List[str] = None
    
    def __post_init__(self):
        if self.suggested_tags is None:
            self.suggested_tags = []
        if self.confidence_notes is None:
            self.confidence_notes = []

class DocumentIntelligenceService:
    """Service for auto-detecting document metadata from filenames and content"""
    
    def __init__(self):
        """Initialize detection patterns and rules"""
        self.filename_patterns = self._initialize_filename_patterns()
        self.content_patterns = self._initialize_content_patterns()
        self.date_patterns = self._initialize_date_patterns()
    
    def _initialize_filename_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize filename patterns for document type detection"""
        return {
            "contract": [
                {"pattern": r".*agreement.*\.pdf$", "subtype": "service_agreement", "confidence": 0.8},
                {"pattern": r".*contract.*\.pdf$", "subtype": "general_contract", "confidence": 0.8},
                {"pattern": r".*nda.*\.pdf$", "subtype": "non_disclosure", "confidence": 0.9},
                {"pattern": r".*confidentiality.*\.pdf$", "subtype": "non_disclosure", "confidence": 0.7},
                {"pattern": r".*employment.*\.pdf$", "subtype": "employment_agreement", "confidence": 0.8},
                {"pattern": r".*lease.*\.pdf$", "subtype": "lease_agreement", "confidence": 0.8},
                {"pattern": r".*purchase.*\.pdf$", "subtype": "purchase_agreement", "confidence": 0.8},
                {"pattern": r".*license.*\.pdf$", "subtype": "license_agreement", "confidence": 0.8},
                {"pattern": r".*settlement.*\.pdf$", "subtype": "settlement_agreement", "confidence": 0.8},
            ],
            "pleading": [
                {"pattern": r".*complaint.*\.pdf$", "subtype": "complaint", "confidence": 0.9},
                {"pattern": r".*answer.*\.pdf$", "subtype": "answer", "confidence": 0.8},
                {"pattern": r".*motion.*\.pdf$", "subtype": "motion", "confidence": 0.8},
                {"pattern": r".*brief.*\.pdf$", "subtype": "brief", "confidence": 0.7},
                {"pattern": r".*order.*\.pdf$", "subtype": "order", "confidence": 0.8},
                {"pattern": r".*judgment.*\.pdf$", "subtype": "judgment", "confidence": 0.9},
                {"pattern": r".*subpoena.*\.pdf$", "subtype": "subpoena", "confidence": 0.9},
                {"pattern": r".*notice.*\.pdf$", "subtype": "notice", "confidence": 0.6},
                {"pattern": r".*petition.*\.pdf$", "subtype": "petition", "confidence": 0.8},
                {"pattern": r".*filing.*\.pdf$", "subtype": "general_filing", "confidence": 0.5},
            ],
            "correspondence": [
                {"pattern": r".*letter.*\.(pdf|doc|docx)$", "subtype": "letter", "confidence": 0.8},
                {"pattern": r".*email.*\.(pdf|msg|eml)$", "subtype": "email", "confidence": 0.8},
                {"pattern": r".*memo.*\.(pdf|doc|docx)$", "subtype": "memo", "confidence": 0.8},
                {"pattern": r".*fax.*\.pdf$", "subtype": "fax", "confidence": 0.8},
                {"pattern": r".*communication.*\.(pdf|doc|docx)$", "subtype": "general", "confidence": 0.6},
            ],
            "discovery": [
                {"pattern": r".*interrogator.*\.pdf$", "subtype": "interrogatories", "confidence": 0.9},
                {"pattern": r".*rfp.*\.pdf$", "subtype": "request_for_production", "confidence": 0.9},
                {"pattern": r".*rfa.*\.pdf$", "subtype": "request_for_admission", "confidence": 0.9},
                {"pattern": r".*deposition.*\.pdf$", "subtype": "deposition", "confidence": 0.8},
                {"pattern": r".*production.*\.pdf$", "subtype": "document_production", "confidence": 0.7},
                {"pattern": r".*discovery.*\.pdf$", "subtype": "general_discovery", "confidence": 0.6},
            ],
            "exhibit": [
                {"pattern": r".*exhibit.*[a-z0-9].*\.pdf$", "subtype": "trial_exhibit", "confidence": 0.8},
                {"pattern": r".*ex[_\-\s]*[a-z0-9].*\.pdf$", "subtype": "exhibit", "confidence": 0.7},
                {"pattern": r".*attachment.*\.pdf$", "subtype": "attachment", "confidence": 0.6},
            ],
            "memo": [
                {"pattern": r".*memo.*\.(pdf|doc|docx)$", "subtype": "legal_memo", "confidence": 0.8},
                {"pattern": r".*research.*\.(pdf|doc|docx)$", "subtype": "research_memo", "confidence": 0.7},
                {"pattern": r".*analysis.*\.(pdf|doc|docx)$", "subtype": "legal_analysis", "confidence": 0.6},
            ]
        }
    
    def _initialize_content_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize content patterns for enhanced detection"""
        return {
            "contract_indicators": [
                {"pattern": r"WHEREAS", "weight": 0.3},
                {"pattern": r"IN CONSIDERATION OF", "weight": 0.4},
                {"pattern": r"AGREEMENT", "weight": 0.2},
                {"pattern": r"Party", "weight": 0.1},
                {"pattern": r"effective date", "weight": 0.2},
                {"pattern": r"termination", "weight": 0.1},
            ],
            "pleading_indicators": [
                {"pattern": r"SUPERIOR COURT", "weight": 0.4},
                {"pattern": r"SUPREME COURT", "weight": 0.4},
                {"pattern": r"Case No\.", "weight": 0.3},
                {"pattern": r"PLAINTIFF", "weight": 0.3},
                {"pattern": r"DEFENDANT", "weight": 0.3},
                {"pattern": r"HONORABLE", "weight": 0.2},
                {"pattern": r"BEFORE THE", "weight": 0.2},
            ],
            "discovery_indicators": [
                {"pattern": r"INTERROGATORY", "weight": 0.5},
                {"pattern": r"REQUEST FOR PRODUCTION", "weight": 0.5},
                {"pattern": r"REQUEST FOR ADMISSION", "weight": 0.5},
                {"pattern": r"DEPOSITION", "weight": 0.4},
                {"pattern": r"propounding party", "weight": 0.3},
                {"pattern": r"responding party", "weight": 0.3},
            ]
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
        """
        Detect document metadata from filename patterns
        """
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
        
        # Extract exhibit number if it's an exhibit
        if detected.document_type == "exhibit":
            exhibit_match = re.search(r"exhibit[\s_-]*([a-z0-9]+)", filename_lower, re.IGNORECASE)
            if exhibit_match:
                detected.exhibit_number = exhibit_match.group(1).upper()
                detected.confidence_notes.append("Exhibit number extracted from filename")
        
        # Generate document title from filename
        detected.document_title = self._generate_title_from_filename(filename)
        
        # Extract potential case number
        case_number_match = re.search(r"(\d{4}[-_]?\d{2,4}[-_]?\w*)", filename)
        if case_number_match:
            detected.case_number = case_number_match.group(1)
            detected.confidence_notes.append("Potential case number found in filename")
        
        return detected
    
    def detect_from_content(self, content: str, filename: str = None) -> DetectedMetadata:
        """
        Detect document metadata from content analysis
        Note: This is a basic implementation. In production, you'd use more sophisticated NLP.
        """
        detected = DetectedMetadata()
        content_upper = content.upper()
        
        # Score each document type based on content indicators
        type_scores = {}
        
        for indicator_type, patterns in self.content_patterns.items():
            score = 0.0
            for pattern_config in patterns:
                pattern = pattern_config["pattern"]
                weight = pattern_config["weight"]
                
                matches = len(re.findall(pattern, content_upper))
                score += matches * weight
            
            doc_type = indicator_type.replace("_indicators", "")
            type_scores[doc_type] = score
        
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
        
        # Extract additional metadata based on document type
        if detected.document_type == "pleading":
            detected = self._extract_pleading_metadata(content, detected)
        elif detected.document_type == "contract":
            detected = self._extract_contract_metadata(content, detected)
        elif detected.document_type == "correspondence":
            detected = self._extract_correspondence_metadata(content, detected)
        
        return detected
    
    def detect_comprehensive(self, filename: str, content: str = None) -> DetectedMetadata:
        """
        Comprehensive detection combining filename and content analysis
        """
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
            
            # Merge type-specific fields
            for field in ['contract_type', 'court_jurisdiction', 'case_number', 'opposing_party',
                         'author', 'recipient', 'subject', 'discovery_type', 'exhibit_number']:
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
    
    def _extract_pleading_metadata(self, content: str, detected: DetectedMetadata) -> DetectedMetadata:
        """Extract pleading-specific metadata"""
        content_upper = content.upper()
        
        # Extract court jurisdiction
        court_patterns = [
            r"SUPERIOR COURT OF ([^,\n]+)",
            r"SUPREME COURT OF ([^,\n]+)",
            r"COURT OF ([^,\n]+)",
            r"BEFORE THE ([^,\n]+COURT[^,\n]*)"
        ]
        
        for pattern in court_patterns:
            match = re.search(pattern, content_upper)
            if match:
                detected.court_jurisdiction = match.group(1).strip().title()
                break
        
        # Extract case number
        case_patterns = [
            r"CASE NO\.?\s*([A-Z0-9-]+)",
            r"NO\.?\s*([A-Z0-9-]+)",
            r"DOCKET NO\.?\s*([A-Z0-9-]+)"
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, content_upper)
            if match:
                detected.case_number = match.group(1).strip()
                break
        
        # Extract parties
        plaintiff_match = re.search(r"PLAINTIFF[S]?\s*[:\-]?\s*([^,\n]+)", content_upper)
        if plaintiff_match:
            detected.opposing_party = plaintiff_match.group(1).strip().title()
        
        return detected
    
    def _extract_contract_metadata(self, content: str, detected: DetectedMetadata) -> DetectedMetadata:
        """Extract contract-specific metadata"""
        content_upper = content.upper()
        
        # Determine contract type
        if "SERVICE" in content_upper and "AGREEMENT" in content_upper:
            detected.contract_type = "service_agreement"
        elif "NON-DISCLOSURE" in content_upper or "NDA" in content_upper:
            detected.contract_type = "non_disclosure"
        elif "EMPLOYMENT" in content_upper:
            detected.contract_type = "employment_agreement"
        elif "LEASE" in content_upper:
            detected.contract_type = "lease_agreement"
        elif "PURCHASE" in content_upper:
            detected.contract_type = "purchase_agreement"
        
        return detected
    
    def _extract_correspondence_metadata(self, content: str, detected: DetectedMetadata) -> DetectedMetadata:
        """Extract correspondence-specific metadata"""
        # Extract subject (common in emails)
        subject_patterns = [
            r"SUBJECT:\s*([^\n]+)",
            r"RE:\s*([^\n]+)",
            r"REGARDING:\s*([^\n]+)"
        ]
        
        for pattern in subject_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                detected.subject = match.group(1).strip()
                break
        
        # Extract sender/recipient (basic email pattern)
        from_match = re.search(r"FROM:\s*([^\n]+)", content, re.IGNORECASE)
        if from_match:
            detected.author = from_match.group(1).strip()
        
        to_match = re.search(r"TO:\s*([^\n]+)", content, re.IGNORECASE)
        if to_match:
            detected.recipient = to_match.group(1).strip()
        
        return detected
    
    def generate_suggested_tags(self, detected: DetectedMetadata, filename: str) -> List[str]:
        """Generate suggested tags based on detected metadata"""
        tags = []
        
        if detected.document_type:
            tags.append(detected.document_type)
        
        if detected.document_subtype:
            tags.append(detected.document_subtype)
        
        if detected.contract_type:
            tags.append(detected.contract_type)
        
        if detected.court_jurisdiction:
            tags.append("court_filing")
            
        if detected.case_number:
            tags.append("case_" + detected.case_number.replace("-", "_").lower())
        
        # Add year if date is available
        if detected.document_date:
            tags.append(str(detected.document_date.year))
        
        # Remove duplicates and return
        return list(set(tags))

# Create global service instance
document_intelligence = DocumentIntelligenceService()