# app/services/sred_signal_detector.py
"""
SR&ED Signal Detection Service

Detects SR&ED eligibility signals in document text using keyword taxonomy.
Based on CRA SR&ED eligibility criteria (Five-Question Test).
"""

import re
import logging
from typing import Dict, List, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SREDSignals:
    """SR&ED eligibility signals found in text"""
    uncertainty_count: int = 0
    systematic_count: int = 0
    failure_count: int = 0
    advancement_count: int = 0
    routine_count: int = 0
    score: float = 0.0
    keyword_matches: Dict[str, List[str]] = field(default_factory=lambda: {
        "uncertainty": [],
        "systematic": [],
        "failure": [],
        "advancement": [],
        "routine": []
    })

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return {
            "uncertainty_keywords": self.uncertainty_count,
            "systematic_keywords": self.systematic_count,
            "failure_keywords": self.failure_count,
            "advancement_keywords": self.advancement_count,
            "routine_keywords": self.routine_count,
            "score": round(self.score, 4),
            "keyword_matches": self.keyword_matches
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
        "unpredictable", "indeterminate",

        # Problem statements
        "no existing solution", "no available technology",
        "no clear path", "couldn't find", "failed to locate",
        "existing methods inadequate", "current approaches insufficient",
        "no established method", "no known solution",

        # Investigation triggers
        "needed to determine", "attempted to resolve",
        "tried to understand", "explored whether",
        "investigated if", "researched how",
        "sought to discover", "aimed to find out",

        # SR&ED-specific language (from CRA docs)
        "technological uncertainty", "scientific uncertainty",
        "knowledge gap", "unproven technology",
        "technical challenge", "technical obstacle",
        "technical limitation", "beyond current capability"
    }

    SYSTEMATIC_INVESTIGATION_KEYWORDS = {
        # Hypothesis-driven
        "hypothesis", "hypotheses", "hypothesized",
        "proposed that", "theorized", "postulated",
        "assumed that", "predicted that",

        # Experimental approach
        "experiment", "experimental", "tested", "trial",
        "pilot", "proof of concept", "prototype",
        "baseline", "benchmark", "control group",
        "test case", "test scenario", "validation",

        # Iterative process
        "iteration", "iterated", "refined", "revised",
        "approach 1", "approach 2", "method a", "method b",
        "first attempt", "second attempt", "alternative approach",
        "compared", "evaluated", "analyzed results",
        "modified approach", "adjusted parameters",

        # Measurement & analysis
        "measured", "quantified", "metrics", "performance data",
        "statistical analysis", "correlation", "regression",
        "data analysis", "results showed", "findings indicate",

        # SR&ED-specific
        "systematic investigation", "systematic approach",
        "methodical", "structured experimentation",
        "scientific method", "empirical testing"
    }

    FAILURE_KEYWORDS = {
        # Direct failure statements
        "failed", "failure", "unsuccessful", "didn't work",
        "did not work", "not successful", "proved inadequate",
        "fell short", "underperformed",

        # Negative results
        "abandoned", "rejected", "discarded", "discontinued",
        "dead end", "proved unfeasible", "not viable",
        "scrapped", "ruled out",

        # Iteration due to problems
        "had to redesign", "forced to reconsider",
        "went back to drawing board", "started over",
        "tried again", "another attempt",
        "reworked", "overhauled",

        # Performance issues
        "performance degraded", "didn't meet requirements",
        "insufficient accuracy", "unacceptable latency",
        "below target", "worse than expected",
        "too slow", "too inaccurate", "unreliable",
        "exceeded limits", "out of spec"
    }

    ADVANCEMENT_KEYWORDS = {
        # Achievement language
        "achieved", "accomplished", "succeeded", "breakthrough",
        "solved", "resolved", "overcame",
        "completed", "attained",

        # Novelty
        "novel", "new", "first time", "unprecedented",
        "original", "innovative", "unique approach",
        "never before", "no prior work",
        "pioneering", "groundbreaking",

        # Improvement
        "improved", "enhancement", "advancement", "progress",
        "better than", "exceeded", "outperformed",
        "state of the art", "cutting edge",
        "optimized", "superior performance",

        # SR&ED-specific
        "technological advancement", "scientific advancement",
        "knowledge generation", "contributed to knowledge base",
        "new understanding", "discovered that"
    }

    # Disqualifying keywords (routine work)
    ROUTINE_WORK_KEYWORDS = {
        "routine maintenance", "standard procedure",
        "regular updates", "normal operation",
        "business as usual", "typical workflow",
        "common practice", "well-established method",
        "off the shelf", "out of the box",
        "vendor documentation", "standard implementation",
        "following instructions", "per manual",
        "standard configuration", "default settings",
        "routine debugging", "standard testing"
    }

    def __init__(self):
        """Initialize the detector with compiled regex patterns"""
        self.uncertainty_pattern = self._compile_pattern(self.UNCERTAINTY_KEYWORDS)
        self.systematic_pattern = self._compile_pattern(self.SYSTEMATIC_INVESTIGATION_KEYWORDS)
        self.failure_pattern = self._compile_pattern(self.FAILURE_KEYWORDS)
        self.advancement_pattern = self._compile_pattern(self.ADVANCEMENT_KEYWORDS)
        self.routine_pattern = self._compile_pattern(self.ROUTINE_WORK_KEYWORDS)
        logger.info("SREDSignalDetector initialized with keyword patterns")

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
        if not text or len(text.strip()) < 10:
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
            routine_count=len(routine_matches),
            score=score,
            keyword_matches={
                "uncertainty": list(set(m.lower() for m in uncertainty_matches))[:10],
                "systematic": list(set(m.lower() for m in systematic_matches))[:10],
                "failure": list(set(m.lower() for m in failure_matches))[:10],
                "advancement": list(set(m.lower() for m in advancement_matches))[:10],
                "routine": list(set(m.lower() for m in routine_matches))[:10]
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
        routine_penalty = routine * 3.0

        # Normalize by text length (per 1000 characters)
        # Cap normalization factor to avoid tiny scores for very long docs
        norm_factor = max(text_length / 1000, 1.0)
        normalized_score = (positive_score - routine_penalty) / norm_factor

        # Scale to 0-1 range (empirically tuned)
        # A score of ~5 normalized signals per 1000 chars = 1.0
        scaled_score = normalized_score / 5.0

        # Require minimum signals to get score > 0.5
        min_signals = (uncertainty >= 1 and systematic >= 1)
        if not min_signals and scaled_score > 0.5:
            scaled_score = 0.5

        # Clamp to 0-1
        return max(min(scaled_score, 1.0), 0.0)

    def detect_signals_batch(self, texts: List[str]) -> List[SREDSignals]:
        """Batch process multiple texts"""
        return [self.detect_signals(text) for text in texts]

    def get_eligibility_assessment(self, signals: SREDSignals) -> Dict:
        """
        Generate a human-readable eligibility assessment based on signals.

        Returns dict with:
        - eligibility_level: 'high', 'medium', 'low', 'unlikely'
        - strengths: list of positive indicators
        - weaknesses: list of concerns
        - recommendation: suggested next steps
        """
        strengths = []
        weaknesses = []

        # Assess uncertainty
        if signals.uncertainty_count >= 3:
            strengths.append("Strong evidence of technological uncertainty")
        elif signals.uncertainty_count >= 1:
            strengths.append("Some uncertainty indicators present")
        else:
            weaknesses.append("No clear technological uncertainty identified")

        # Assess systematic approach
        if signals.systematic_count >= 5:
            strengths.append("Clear systematic investigation methodology")
        elif signals.systematic_count >= 2:
            strengths.append("Evidence of experimental approach")
        else:
            weaknesses.append("Limited evidence of systematic investigation")

        # Assess failures (positive for SR&ED)
        if signals.failure_count >= 3:
            strengths.append("Documented failures and iterations (strong SR&ED indicator)")
        elif signals.failure_count >= 1:
            strengths.append("Some iteration/failure documented")

        # Assess advancement
        if signals.advancement_count >= 2:
            strengths.append("Claims of technological advancement")
        elif signals.advancement_count >= 1:
            strengths.append("Potential advancement identified")
        else:
            weaknesses.append("Advancement claims unclear")

        # Assess routine work (negative)
        if signals.routine_count >= 3:
            weaknesses.append("Significant routine/standard work indicators")
        elif signals.routine_count >= 1:
            weaknesses.append("Some routine work language present")

        # Determine eligibility level
        if signals.score >= 0.7 and len(weaknesses) <= 1:
            eligibility_level = "high"
            recommendation = "Strong SR&ED candidate. Proceed with detailed review."
        elif signals.score >= 0.4 and signals.uncertainty_count >= 1:
            eligibility_level = "medium"
            recommendation = "Potential SR&ED work. Requires further documentation review."
        elif signals.score >= 0.2:
            eligibility_level = "low"
            recommendation = "Weak SR&ED indicators. May need additional supporting documentation."
        else:
            eligibility_level = "unlikely"
            recommendation = "Unlikely to qualify for SR&ED based on this document alone."

        return {
            "eligibility_level": eligibility_level,
            "score": round(signals.score, 2),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendation": recommendation,
            "signal_summary": {
                "uncertainty": signals.uncertainty_count,
                "systematic": signals.systematic_count,
                "failure": signals.failure_count,
                "advancement": signals.advancement_count,
                "routine": signals.routine_count
            }
        }


# Singleton instance for use across the application
sred_signal_detector = SREDSignalDetector()
