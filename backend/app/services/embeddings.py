"""
Embedding generation service for RAG pipeline.

Generates vector embeddings using OpenAI's text-embedding-3-small model.
Supports batch processing and automatic retry logic for API failures.
"""

import logging
from typing import List, Dict, Optional
import time

from openai import OpenAI, OpenAIError, RateLimitError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(self):
        """Initialize the embedding service with OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.warning(
                "OPENAI_API_KEY not set. Embedding generation will fail. "
                "Set OPENAI_API_KEY environment variable."
            )

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.dimensions = settings.OPENAI_EMBEDDING_DIMENSIONS

        logger.info(
            f"Initialized EmbeddingService with model={self.model}, "
            f"dimensions={self.dimensions}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        reraise=True
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding vector

        Raises:
            OpenAIError: If API call fails after retries
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions
            )

            embedding = response.data[0].embedding

            logger.debug(
                f"Generated embedding for text (length={len(text)}, "
                f"embedding_dim={len(embedding)})"
            )

            return embedding

        except RateLimitError as e:
            logger.warning(f"Rate limit hit, will retry: {str(e)}")
            raise
        except APITimeoutError as e:
            logger.warning(f"API timeout, will retry: {str(e)}")
            raise
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {str(e)}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        reraise=True
    )
    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        OpenAI API supports up to 2048 inputs per request, but we use smaller
        batches for better error handling and to avoid timeouts.

        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process per API call (default: 100)

        Returns:
            List of embedding vectors in the same order as input texts

        Raises:
            OpenAIError: If API call fails after retries
            ValueError: If texts list is empty or contains empty strings
        """
        if not texts:
            raise ValueError("Cannot generate embeddings for empty list")

        # Filter out empty texts and track indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)
            else:
                logger.warning(f"Skipping empty text at index {i}")

        if not valid_texts:
            raise ValueError("All provided texts are empty")

        all_embeddings = []
        total_batches = (len(valid_texts) + batch_size - 1) // batch_size

        logger.info(
            f"Generating embeddings for {len(valid_texts)} texts in "
            f"{total_batches} batches (batch_size={batch_size})"
        )

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(valid_texts))
            batch_texts = valid_texts[start_idx:end_idx]

            try:
                logger.debug(
                    f"Processing batch {batch_num + 1}/{total_batches} "
                    f"({len(batch_texts)} texts)"
                )

                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch_texts,
                    dimensions=self.dimensions
                )

                # Extract embeddings in correct order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                # Small delay between batches to avoid rate limits
                if batch_num < total_batches - 1:
                    time.sleep(0.1)

            except RateLimitError as e:
                logger.warning(
                    f"Rate limit hit on batch {batch_num + 1}/{total_batches}, "
                    f"will retry: {str(e)}"
                )
                raise
            except APITimeoutError as e:
                logger.warning(
                    f"API timeout on batch {batch_num + 1}/{total_batches}, "
                    f"will retry: {str(e)}"
                )
                raise
            except OpenAIError as e:
                logger.error(
                    f"OpenAI API error on batch {batch_num + 1}/{total_batches}: "
                    f"{str(e)}"
                )
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error on batch {batch_num + 1}/{total_batches}: "
                    f"{str(e)}",
                    exc_info=True
                )
                raise

        logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
        return all_embeddings

    def get_embedding_metadata(self) -> Dict[str, any]:
        """
        Get metadata about the embedding configuration.

        Returns:
            Dictionary with model name, dimensions, and other config info
        """
        return {
            "model": self.model,
            "dimensions": self.dimensions,
            "provider": "openai",
            "api_configured": bool(settings.OPENAI_API_KEY)
        }


# Singleton instance
embedding_service = EmbeddingService()
