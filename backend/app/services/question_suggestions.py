# app/services/question_suggestions.py - Question improvement suggestions

from typing import List, Optional

LEGAL_TERMS = [
    'section', 'clause', 'paragraph', 'article', 'subsection',
    'exhibit', 'schedule', 'appendix', 'provision', 'term'
]


class QuestionSuggestionService:
    """
    Generates suggestions to help users improve their questions.

    Uses two signals:
    1. Matter Mode: similarity scores from RAG retrieval
    2. Discovery Mode: Claude's self-reported confidence
    """

    def generate_suggestions(
        self,
        question: str,
        has_matter: bool,
        avg_similarity: Optional[float],
        confidence: str,
        question_quality_score: float
    ) -> List[str]:
        """
        Generate improvement suggestions based on available signals.

        Args:
            question: The user's original question
            has_matter: Whether a matter is selected (enables RAG)
            avg_similarity: Average similarity score from retrieval (None if no matter)
            confidence: Claude's self-reported confidence (HIGH/MEDIUM/LOW)
            question_quality_score: Pre-computed question quality (0.0-1.0)

        Returns:
            List of up to 3 suggestion strings
        """
        suggestions = []
        words = question.split()
        has_legal_terms = any(term in question.lower() for term in LEGAL_TERMS)

        # Matter mode with low retrieval quality
        if has_matter and avg_similarity is not None and avg_similarity < 0.6:
            if len(words) < 5:
                suggestions.append(
                    "Try adding more detail to your question"
                )
            if not has_legal_terms:
                suggestions.append(
                    "Include specific section or clause references"
                )
            if avg_similarity < 0.4:
                suggestions.append(
                    "Your documents may not cover this topic - try rephrasing "
                    "with terms from your contracts"
                )

        # Low confidence from Claude (applies to both modes)
        if confidence == "LOW":
            if not has_matter:
                suggestions.append(
                    "Select a matter to search your documents for specific answers"
                )
            if len(suggestions) < 3:
                suggestions.append(
                    "Be more specific about what information you need"
                )

        # No matter selected - always suggest selecting one (for any confidence)
        if not has_matter and len(suggestions) == 0:
            suggestions.append(
                "For answers based on your documents, select a matter"
            )

        # General quality issues (fallback)
        if question_quality_score < 0.4 and len(suggestions) < 2:
            if len(words) < 3:
                suggestions.append(
                    "Adding more context helps get better answers"
                )
            elif not has_legal_terms and not any(char.isdigit() for char in question):
                suggestions.append(
                    "Including party names, dates, or section numbers can improve results"
                )

        return suggestions[:3]  # Max 3 suggestions
