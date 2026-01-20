# Phase 2: SR&ED Signal Detection Service

## Overview

Extend the existing document processing pipeline to detect SR&ED eligibility signals during chunking/embedding phase.

## Integration Point

The existing pipeline is:
```
Upload → Text Extraction → Chunking → Embedding → Vector Storage
```

Add SR&ED signal detection:
```
Upload → Text Extraction → Chunking → **SR&ED Detection** → Embedding → Vector Storage
```

## File Location

Create: `backend/app/services/sred_signal_detector.py`

Integrate into: `backend/app/services/document_processor.py` (existing)

## Implementation

### 1. SR&ED Keyword Taxonomy

```python
# backend/app/services/sred_signal_detector.py

from typing import Dict, List, Set
import re
from dataclasses import dataclass

@dataclass
class SREDSignals:
    """SR&ED eligibility signals found in text"""
    uncertainty_count: int = 0
    systematic_count: int = 0
    failure_count: int = 0
    advancement_count: int = 0
    score: float = 0.0
    keyword_matches: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.keyword_matches is None:
            self.keyword_matches = {
                "uncertainty": [],
                "systematic": [],
                "failure": [],
                "advancement": []
            }


class SREDSignalDetector:
    """
    Detects SR&ED eligibility signals in document text.
    
    Based on CRA SR&ED eligibility criteria:
    1. Technological uncertainty
    2. Systematic investigation
    3. Technological advancement
    """
    
    # Keyword categories based on CRA guidance
    UNCERTAINTY_KEYWORDS = {
        # Direct uncertainty language
        "uncertain", "uncertainty", "unknown", "unclear",
        "not known", "couldn't determine", "unable to predict",
        
        # Problem statements
        "no existing solution", "no available technology",
        "no clear path", "couldn't find", "failed to locate",
        "existing methods inadequate", "current approaches insufficient",
        
        # Investigation triggers
        "needed to determine", "attempted to resolve",
        "tried to understand", "explored whether",
        "investigated if", "researched how",
        
        # SR&ED-specific language (from CRA docs)
        "technological uncertainty", "scientific uncertainty",
        "knowledge gap", "unproven technology"
    }
    
    SYSTEMATIC_INVESTIGATION_KEYWORDS = {
        # Hypothesis-driven
        "hypothesis", "hypotheses", "hypothesized",
        "proposed that", "theorized", "postulated",
        
        # Experimental approach
        "experiment", "experimental", "tested", "trial",
        "pilot", "proof of concept", "prototype",
        "baseline", "benchmark", "control group",
        
        # Iterative process
        "iteration", "iterated", "refined", "revised",
        "approach 1", "approach 2", "method a", "method b",
        "first attempt", "second attempt", "alternative approach",
        "compared", "evaluated", "analyzed results",
        
        # Measurement & analysis
        "measured", "quantified", "metrics", "performance data",
        "statistical analysis", "correlation", "regression",
        
        # SR&ED-specific
        "systematic investigation", "systematic approach",
        "methodical", "structured experimentation"
    }
    
    FAILURE_KEYWORDS = {
        # Direct failure statements
        "failed", "failure", "unsuccessful", "didn't work",
        "did not work", "not successful", "proved inadequate",
        
        # Negative results
        "abandoned", "rejected", "discarded", "discontinued",
        "dead end", "proved unfeasible", "not viable",
        
        # Iteration due to problems
        "had to redesign", "forced to reconsider",
        "went back to drawing board", "started over",
        "tried again", "another attempt",
        
        # Performance issues
        "performance degraded", "didn't meet requirements",
        "insufficient accuracy", "unacceptable latency",
        "below target", "worse than expected"
    }
    
    ADVANCEMENT_KEYWORDS = {
        # Achievement language
        "achieved", "accomplished", "succeeded", "breakthrough",
        "solved", "resolved", "overcame",
        
        # Novelty
        "novel", "new", "first time", "unprecedented",
        "original", "innovative", "unique approach",
        "never before", "no prior work",
        
        # Improvement
        "improved", "enhancement", "advancement", "progress",
        "better than", "exceeded", "outperformed",
        "state of the art", "cutting edge",
        
        # SR&ED-specific
        "technological advancement", "scientific advancement",
        "knowledge generation", "contributed to knowledge base"
    }
    
    # Disqualifying keywords (routine work)
    ROUTINE_WORK_KEYWORDS = {
        "routine maintenance", "standard procedure",
        "regular updates", "normal operation",
        "business as usual", "typical workflow",
        "common practice", "well-established method",
        "off the shelf", "out of the box",
        "vendor documentation", "standard implementation"
    }
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.uncertainty_pattern = self._compile_pattern(self.UNCERTAINTY_KEYWORDS)
        self.systematic_pattern = self._compile_pattern(self.SYSTEMATIC_INVESTIGATION_KEYWORDS)
        self.failure_pattern = self._compile_pattern(self.FAILURE_KEYWORDS)
        self.advancement_pattern = self._compile_pattern(self.ADVANCEMENT_KEYWORDS)
        self.routine_pattern = self._compile_pattern(self.ROUTINE_WORK_KEYWORDS)
    
    def _compile_pattern(self, keywords: Set[str]) -> re.Pattern:
        """Compile keyword set into case-insensitive regex pattern"""
        # Escape special regex characters and join with OR
        escaped = [re.escape(kw) for kw in keywords]
        pattern_str = r'\b(' + '|'.join(escaped) + r')\b'
        return re.compile(pattern_str, re.IGNORECASE)
    
    def detect_signals(self, text: str) -> SREDSignals:
        """
        Detect SR&ED signals in text.
        
        Args:
            text: Document or chunk text
            
        Returns:
            SREDSignals object with counts and score
        """
        if not text:
            return SREDSignals()
        
        # Find all matches
        uncertainty_matches = self.uncertainty_pattern.findall(text)
        systematic_matches = self.systematic_pattern.findall(text)
        failure_matches = self.failure_pattern.findall(text)
        advancement_matches = self.advancement_pattern.findall(text)
        routine_matches = self.routine_pattern.findall(text)
        
        # Calculate score
        score = self._calculate_score(
            len(uncertainty_matches),
            len(systematic_matches),
            len(failure_matches),
            len(advancement_matches),
            len(routine_matches),
            len(text)
        )
        
        return SREDSignals(
            uncertainty_count=len(uncertainty_matches),
            systematic_count=len(systematic_matches),
            failure_count=len(failure_matches),
            advancement_count=len(advancement_matches),
            score=score,
            keyword_matches={
                "uncertainty": list(set(uncertainty_matches))[:10],  # Top 10 unique
                "systematic": list(set(systematic_matches))[:10],
                "failure": list(set(failure_matches))[:10],
                "advancement": list(set(advancement_matches))[:10]
            }
        )
    
    def _calculate_score(
        self,
        uncertainty: int,
        systematic: int,
        failure: int,
        advancement: int,
        routine: int,
        text_length: int
    ) -> float:
        """
        Calculate SR&ED likelihood score (0.0 to 1.0)
        
        Scoring logic:
        - Uncertainty signals are critical (weight: 3.0)
        - Systematic investigation signals (weight: 2.0)
        - Failure signals are valuable! (weight: 2.5)
        - Advancement signals (weight: 2.0)
        - Routine work signals reduce score
        - Normalize by text length
        """
        if text_length == 0:
            return 0.0
        
        # Weighted sum
        positive_score = (
            uncertainty * 3.0 +
            systematic * 2.0 +
            failure * 2.5 +  # Failures are good for SR&ED!
            advancement * 2.0
        )
        
        # Penalty for routine work
        routine_penalty = routine * 2.0
        
        # Normalize by text length (per 1000 characters)
        normalized_score = (positive_score - routine_penalty) / (text_length / 1000)
        
        # Require minimum signals to get score > 0.5
        min_signals = (uncertainty >= 1 and systematic >= 1)
        if not min_signals and normalized_score > 0.5:
            normalized_score = 0.5
        
        # Cap at 1.0
        return min(max(normalized_score, 0.0), 1.0)
    
    def detect_signals_batch(self, texts: List[str]) -> List[SREDSignals]:
        """Batch process multiple texts"""
        return [self.detect_signals(text) for text in texts]
```

### 2. Named Entity Recognition (NER)

Add spaCy for extracting people, organizations, dates, and technical terms.

```python
# backend/app/services/entity_extractor.py

import spacy
from typing import Dict, List, Set
from datetime import datetime
import re

class EntityExtractor:
    """Extract entities for document metadata and project clustering"""
    
    def __init__(self):
        # Load spaCy model (add to requirements: spacy, en_core_web_sm)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Model not installed, download instructions
            raise RuntimeError(
                "spaCy model not found. Install with: "
                "python -m spacy download en_core_web_sm"
            )
    
    def extract_entities(self, text: str) -> Dict[str, any]:
        """
        Extract named entities and metadata from text.
        
        Returns:
            {
                "people": [...],
                "organizations": [...],
                "dates": [...],
                "project_names": [...],
                "technical_terms": [...]
            }
        """
        if not text or len(text) < 10:
            return self._empty_result()
        
        # Limit text length for performance (process first 50k chars)
        text_sample = text[:50000]
        
        # Process with spaCy
        doc = self.nlp(text_sample)
        
        # Extract entities by type
        people = set()
        organizations = set()
        dates = set()
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                people.add(ent.text)
            elif ent.label_ == "ORG":
                organizations.add(ent.text)
            elif ent.label_ == "DATE":
                dates.add(ent.text)
        
        # Extract project names (heuristic patterns)
        project_names = self._extract_project_names(text_sample)
        
        # Extract technical terms (noun chunks that might be technical)
        technical_terms = self._extract_technical_terms(doc)
        
        return {
            "people": list(people)[:20],  # Top 20
            "organizations": list(organizations)[:10],
            "dates": self._normalize_dates(list(dates)[:20]),
            "project_names": list(project_names)[:10],
            "technical_terms": list(technical_terms)[:30]
        }
    
    def _extract_project_names(self, text: str) -> Set[str]:
        """
        Extract project identifiers using common patterns:
        - "Project Phoenix"
        - "FRAUD-123"
        - "ML-Optimization"
        """
        project_names = set()
        
        # Pattern 1: "Project <Name>"
        pattern1 = r'Project\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        matches1 = re.findall(pattern1, text)
        project_names.update(matches1)
        
        # Pattern 2: Jira-style codes "ABC-123"
        pattern2 = r'\b([A-Z]{2,10}-\d{1,5})\b'
        matches2 = re.findall(pattern2, text)
        project_names.update(matches2)
        
        # Pattern 3: GitHub-style feature names "[feature/...]"
        pattern3 = r'\[([a-z]+/[a-z-]+)\]'
        matches3 = re.findall(pattern3, text, re.IGNORECASE)
        project_names.update(matches3)
        
        return project_names
    
    def _extract_technical_terms(self, doc) -> Set[str]:
        """Extract likely technical terms from noun chunks"""
        technical_terms = set()
        
        for chunk in doc.noun_chunks:
            # Heuristics for technical terms:
            # - Contains technical words
            # - All caps (acronyms)
            # - Contains numbers
            chunk_text = chunk.text.strip()
            
            if len(chunk_text) < 3 or len(chunk_text) > 50:
                continue
            
            # Check if looks technical
            is_technical = any([
                chunk_text.isupper() and len(chunk_text) >= 3,  # Acronym
                any(c.isdigit() for c in chunk_text),  # Has numbers
                any(tech_word in chunk_text.lower() for tech_word in [
                    'algorithm', 'model', 'system', 'protocol', 'framework',
                    'architecture', 'optimization', 'processing', 'analysis'
                ])
            ])
            
            if is_technical:
                technical_terms.add(chunk_text)
        
        return technical_terms
    
    def _normalize_dates(self, date_strings: List[str]) -> List[str]:
        """
        Attempt to normalize dates to ISO format.
        Best effort - some dates may remain as strings.
        """
        normalized = []
        
        for date_str in date_strings:
            # Try to parse common formats
            for fmt in ["%Y-%m-%d", "%B %d, %Y", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    normalized.append(dt.strftime("%Y-%m-%d"))
                    break
                except ValueError:
                    continue
            else:
                # Couldn't parse, keep original
                normalized.append(date_str)
        
        return normalized
    
    def _empty_result(self) -> Dict[str, List]:
        """Return empty result structure"""
        return {
            "people": [],
            "organizations": [],
            "dates": [],
            "project_names": [],
            "technical_terms": []
        }
```

### 3. Integration into Document Processor

Modify `backend/app/services/document_processor.py`:

```python
# backend/app/services/document_processor.py

from app.services.sred_signal_detector import SREDSignalDetector, SREDSignals
from app.services.entity_extractor import EntityExtractor
from app.models.models import Document, DocumentChunk
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

class DocumentProcessor:
    """Existing document processor - add SR&ED detection"""
    
    def __init__(self):
        # Existing services
        # ... (text_extraction, chunking, embeddings, vector_storage)
        
        # NEW: Add SR&ED services
        self.sred_detector = SREDSignalDetector()
        self.entity_extractor = EntityExtractor()
    
    async def process_document(
        self,
        document_id: UUID,
        db: AsyncSession
    ) -> Document:
        """
        Process document through full pipeline.
        
        Existing steps:
        1. Extract text
        2. Chunk text
        3. Generate embeddings
        4. Store in vector DB
        
        NEW steps:
        5. Detect SR&ED signals
        6. Extract entities
        7. Update document metadata
        """
        # ... (existing processing code)
        
        # After text extraction, before chunking:
        # Extract entities for temporal_metadata
        entities = self.entity_extractor.extract_entities(extracted_text)
        
        # Detect document-level SR&ED signals
        doc_signals = self.sred_detector.detect_signals(extracted_text)
        
        # Update document with new metadata
        document.sred_signals = {
            "uncertainty_keywords": doc_signals.uncertainty_count,
            "systematic_keywords": doc_signals.systematic_count,
            "failure_keywords": doc_signals.failure_count,
            "novel_keywords": doc_signals.advancement_count,
            "score": float(doc_signals.score)
        }
        
        document.temporal_metadata = {
            "date_references": entities["dates"],
            "team_members": entities["people"],
            "project_names": entities["project_names"],
            "organizations": entities["organizations"],
            "technical_terms": entities["technical_terms"]
        }
        
        await db.commit()
        
        # ... continue with chunking, embeddings, etc.
        
        # When creating chunks, also detect chunk-level signals
        for chunk in chunks:
            chunk_signals = self.sred_detector.detect_signals(chunk.content)
            chunk.sred_keyword_matches = {
                "uncertainty": chunk_signals.keyword_matches["uncertainty"],
                "systematic": chunk_signals.keyword_matches["systematic"],
                "failure": chunk_signals.keyword_matches["failure"],
                "advancement": chunk_signals.keyword_matches["advancement"]
            }
        
        return document
```

### 4. Celery Task for Batch Processing

Add async task in `backend/app/tasks/`:

```python
# backend/app/tasks/sred_detection_tasks.py

from celery import shared_task
from app.core.database import SessionLocal
from app.services.document_processor import DocumentProcessor
from app.models.models import Document
from uuid import UUID

@shared_task
def detect_sred_signals_batch(document_ids: List[str]):
    """
    Background task to detect SR&ED signals for multiple documents.
    Useful for backfilling existing documents.
    """
    processor = DocumentProcessor()
    db = SessionLocal()
    
    try:
        for doc_id in document_ids:
            doc_uuid = UUID(doc_id)
            processor.process_document(doc_uuid, db)
        
        db.commit()
    finally:
        db.close()
    
    return {"processed": len(document_ids)}
```

## Testing

### Unit Tests

```python
# backend/tests/test_sred_detector.py

import pytest
from app.services.sred_signal_detector import SREDSignalDetector

def test_uncertainty_detection():
    detector = SREDSignalDetector()
    
    text = """
    We faced technological uncertainty about how to achieve 
    sub-50ms latency. No existing solution could handle our requirements.
    """
    
    signals = detector.detect_signals(text)
    
    assert signals.uncertainty_count >= 2
    assert "technological uncertainty" in signals.keyword_matches["uncertainty"]
    assert "no existing solution" in signals.keyword_matches["uncertainty"]

def test_systematic_investigation_detection():
    detector = SREDSignalDetector()
    
    text = """
    We hypothesized that a hybrid approach would work. First attempt
    with caching failed. Second approach with pre-computation was tested
    and showed 40% improvement.
    """
    
    signals = detector.detect_signals(text)
    
    assert signals.systematic_count >= 2
    assert signals.failure_count >= 1
    assert "hypothesized" in signals.keyword_matches["systematic"]

def test_sred_score_calculation():
    detector = SREDSignalDetector()
    
    # High SR&ED text
    high_sred_text = """
    We faced technological uncertainty around real-time processing.
    No existing methods could achieve our latency requirements.
    We hypothesized several approaches and tested each systematically.
    First experiment failed due to memory constraints.
    Second approach succeeded and achieved breakthrough performance.
    """
    
    # Routine work text
    routine_text = """
    We performed routine maintenance on the system using standard procedures.
    Applied vendor documentation to implement the update.
    Followed the regular update workflow as per normal operations.
    """
    
    high_signals = detector.detect_signals(high_sred_text)
    routine_signals = detector.detect_signals(routine_text)
    
    assert high_signals.score > 0.5
    assert routine_signals.score < 0.3
```

## Deployment Steps

1. Install dependencies:
   ```bash
   pip install spacy
   python -m spacy download en_core_web_sm
   ```

2. Run database migration (from Phase 1)

3. Backfill existing documents (optional):
   ```python
   # Script to backfill SR&ED signals for existing docs
   from app.tasks.sred_detection_tasks import detect_sred_signals_batch
   from app.models.models import Document
   
   # Get all document IDs
   doc_ids = db.query(Document.id).all()
   
   # Process in batches of 100
   batch_size = 100
   for i in range(0, len(doc_ids), batch_size):
        batch = doc_ids[i:i+batch_size]
       detect_sred_signals_batch.delay([str(id) for id in batch])
   ```

4. Verify in database:
   ```sql
   SELECT 
     id,
     filename,
     sred_signals->>'score' as sred_score,
     temporal_metadata->>'project_names' as projects
   FROM documents
   WHERE (sred_signals->>'score')::float > 0.5
   ORDER BY (sred_signals->>'score')::float DESC
   LIMIT 10;
   ```

## Next Steps

After Phase 2 is complete:
- Documents will have SR&ED scores
- Temporal/entity metadata will be available
- Ready for Phase 3: Project Discovery Algorithm
