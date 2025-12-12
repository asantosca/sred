"""
OCR service for scanned document processing.

Provides text extraction from scanned PDFs and images using:
1. AWS Textract (primary, production) - high accuracy, handles tables well
2. Tesseract (fallback, local dev) - free, works offline

The service automatically falls back to Tesseract when Textract is unavailable
(no AWS credentials or LocalStack without Textract support).
"""

import asyncio
import io
import logging
import re
import time
from typing import Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

from app.core.config import settings

logger = logging.getLogger(__name__)


# Minimum average characters per page to consider a PDF as having extractable text
MIN_CHARS_PER_PAGE = 100


def is_likely_scanned_pdf(extracted_text: str, page_count: int) -> bool:
    """
    Determine if a PDF is likely scanned based on extracted text density.

    Args:
        extracted_text: Text extracted via pdfplumber
        page_count: Number of pages in the PDF

    Returns:
        True if the PDF appears to be scanned (insufficient extractable text)
    """
    if page_count == 0:
        return True

    # Strip page markers like "[Page 1]" before counting
    clean_text = re.sub(r'\[Page \d+\]', '', extracted_text)
    clean_text = clean_text.strip()

    avg_chars_per_page = len(clean_text) / page_count

    is_scanned = avg_chars_per_page < MIN_CHARS_PER_PAGE

    if is_scanned:
        logger.info(
            f"PDF detected as scanned: {avg_chars_per_page:.0f} chars/page "
            f"(threshold: {MIN_CHARS_PER_PAGE})"
        )

    return is_scanned


class TesseractOCRService:
    """
    OCR service using Tesseract for local/fallback text extraction.

    Requires system dependencies:
    - tesseract-ocr
    - poppler-utils (for pdf2image)
    """

    def __init__(self):
        """Initialize Tesseract service."""
        self._pytesseract = None
        self._convert_from_bytes = None
        self._available = None

    def _lazy_init(self):
        """Lazy initialize dependencies."""
        if self._pytesseract is not None:
            return

        try:
            import pytesseract
            from pdf2image import convert_from_bytes

            # Test that tesseract is actually installed
            pytesseract.get_tesseract_version()

            self._pytesseract = pytesseract
            self._convert_from_bytes = convert_from_bytes
            self._available = True
            logger.info("Tesseract OCR initialized successfully")

        except Exception as e:
            self._available = False
            logger.warning(f"Tesseract OCR not available: {e}")

    def is_available(self) -> bool:
        """Check if Tesseract is available on the system."""
        if self._available is None:
            self._lazy_init()
        return self._available

    def extract_text_from_pdf_bytes(self, file_content: bytes) -> Dict:
        """
        Extract text from PDF bytes using Tesseract OCR.

        Args:
            file_content: Raw PDF bytes

        Returns:
            Dictionary with extraction results:
            {
                'success': bool,
                'text': str,
                'pages_processed': int,
                'confidence_avg': float,
                'error': str (if success=False)
            }
        """
        self._lazy_init()

        if not self._available:
            return {
                'success': False,
                'text': '',
                'pages_processed': 0,
                'confidence_avg': None,
                'error': 'Tesseract OCR is not available on this system'
            }

        try:
            # Convert PDF to images
            logger.info("Converting PDF to images for OCR...")
            images = self._convert_from_bytes(file_content, dpi=300)
            logger.info(f"Converted PDF to {len(images)} page images")

            all_text_parts = []
            all_confidences = []
            pages_processed = 0

            for page_num, image in enumerate(images, start=1):
                try:
                    # Get OCR data with confidence scores
                    ocr_data = self._pytesseract.image_to_data(
                        image,
                        output_type=self._pytesseract.Output.DICT,
                        config='--psm 1'  # Automatic page segmentation with OSD
                    )

                    # Extract text and confidence
                    page_text_parts = []
                    for i, text in enumerate(ocr_data['text']):
                        if text.strip():
                            page_text_parts.append(text)
                            conf = ocr_data['conf'][i]
                            if conf > 0:  # -1 means no confidence available
                                all_confidences.append(conf)

                    page_text = ' '.join(page_text_parts)
                    all_text_parts.append(f"[Page {page_num}]\n{page_text}")
                    pages_processed += 1

                    logger.debug(f"OCR page {page_num}: {len(page_text)} chars")

                except Exception as page_error:
                    logger.warning(f"Failed to OCR page {page_num}: {page_error}")
                    all_text_parts.append(f"[Page {page_num}]\n[OCR failed]")

            full_text = "\n\n".join(all_text_parts)
            confidence_avg = sum(all_confidences) / len(all_confidences) if all_confidences else 0

            logger.info(
                f"Tesseract extracted text from {pages_processed} pages, "
                f"avg confidence: {confidence_avg:.1f}%"
            )

            return {
                'success': True,
                'text': full_text,
                'pages_processed': pages_processed,
                'confidence_avg': confidence_avg,
                'error': None
            }

        except Exception as e:
            error_msg = f"Tesseract OCR failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'text': '',
                'pages_processed': 0,
                'confidence_avg': None,
                'error': error_msg
            }


class TextractOCRService:
    """Service for extracting text from scanned documents using AWS Textract."""

    # Maximum wait time for async Textract job (10 minutes)
    MAX_WAIT_TIME = 600

    # Poll interval for checking job status (seconds)
    POLL_INTERVAL = 5

    def __init__(self):
        """Initialize Textract client."""
        self._textract_client = None
        self._s3_client = None
        self._available = None
        self.bucket_name = settings.S3_BUCKET_NAME

    def _lazy_init(self):
        """Lazy initialize AWS clients."""
        if self._textract_client is not None:
            return

        try:
            self._textract_client = boto3.client(
                'textract',
                endpoint_url=settings.AWS_ENDPOINT_URL if settings.AWS_ENDPOINT_URL else None,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self._s3_client = boto3.client(
                's3',
                endpoint_url=settings.AWS_ENDPOINT_URL if settings.AWS_ENDPOINT_URL else None,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self._available = True
        except Exception as e:
            logger.warning(f"Failed to initialize Textract client: {e}")
            self._available = False

    def is_available(self) -> bool:
        """Check if Textract is available (has credentials)."""
        if self._available is None:
            self._lazy_init()

        # Check if we have real AWS credentials (not LocalStack test creds)
        if settings.AWS_ENDPOINT_URL:
            # Using LocalStack - Textract not supported in free tier
            logger.debug("LocalStack detected - Textract not available")
            return False

        if not settings.AWS_ACCESS_KEY_ID or settings.AWS_ACCESS_KEY_ID == 'test':
            logger.debug("No real AWS credentials - Textract not available")
            return False

        return self._available

    async def extract_text_from_s3_document(self, storage_path: str) -> Dict:
        """
        Extract text from a document stored in S3 using Textract.

        Args:
            storage_path: S3 key of the document

        Returns:
            Dictionary with extraction results
        """
        self._lazy_init()

        if not self.is_available():
            return {
                'success': False,
                'text': '',
                'pages_processed': 0,
                'confidence_avg': None,
                'error': 'Textract is not available (no AWS credentials or using LocalStack)'
            }

        try:
            logger.info(f"Starting Textract job for: {storage_path}")

            response = self._textract_client.start_document_text_detection(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': self.bucket_name,
                        'Name': storage_path
                    }
                }
            )

            job_id = response['JobId']
            logger.info(f"Textract job started: {job_id}")

            result = await self._wait_for_job_completion(job_id)

            if result['success']:
                text, pages_processed, confidence_avg = await self._get_all_results(job_id)

                return {
                    'success': True,
                    'text': text,
                    'pages_processed': pages_processed,
                    'confidence_avg': confidence_avg,
                    'error': None
                }
            else:
                return result

        except (NoCredentialsError, BotoCoreError) as e:
            error_msg = f"AWS credentials error: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'text': '',
                'pages_processed': 0,
                'confidence_avg': None,
                'error': error_msg
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = f"Textract API error: {error_code} - {e.response['Error']['Message']}"
            logger.error(error_msg)
            return {
                'success': False,
                'text': '',
                'pages_processed': 0,
                'confidence_avg': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Textract extraction failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'text': '',
                'pages_processed': 0,
                'confidence_avg': None,
                'error': error_msg
            }

    async def _wait_for_job_completion(self, job_id: str) -> Dict:
        """Wait for Textract job to complete with exponential backoff."""
        start_time = time.time()
        poll_interval = self.POLL_INTERVAL

        while True:
            elapsed = time.time() - start_time
            if elapsed > self.MAX_WAIT_TIME:
                return {
                    'success': False,
                    'error': f'Textract job timed out after {self.MAX_WAIT_TIME} seconds'
                }

            try:
                response = self._textract_client.get_document_text_detection(JobId=job_id)
                status = response['JobStatus']

                if status == 'SUCCEEDED':
                    logger.info(f"Textract job {job_id} completed successfully")
                    return {'success': True, 'error': None}

                elif status == 'FAILED':
                    error_msg = response.get('StatusMessage', 'Unknown error')
                    logger.error(f"Textract job {job_id} failed: {error_msg}")
                    return {'success': False, 'error': f'Textract job failed: {error_msg}'}

                elif status == 'PARTIAL_SUCCESS':
                    logger.warning(f"Textract job {job_id} partially succeeded")
                    return {'success': True, 'error': None}

                else:
                    logger.debug(f"Textract job {job_id} status: {status}, waiting...")
                    await asyncio.sleep(poll_interval)
                    poll_interval = min(poll_interval * 1.5, 30)

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ProvisionedThroughputExceededException':
                    logger.warning("Textract rate limited, waiting...")
                    await asyncio.sleep(poll_interval * 2)
                else:
                    raise

    async def _get_all_results(self, job_id: str) -> Tuple[str, int, float]:
        """Get all pages of results from a completed Textract job."""
        all_text_parts = []
        all_confidences = []
        pages_processed = 0
        next_token = None
        current_page = 0

        while True:
            params = {'JobId': job_id}
            if next_token:
                params['NextToken'] = next_token

            response = self._textract_client.get_document_text_detection(**params)

            for block in response.get('Blocks', []):
                if block['BlockType'] == 'PAGE':
                    current_page += 1
                    pages_processed = current_page
                    all_text_parts.append(f"\n[Page {current_page}]\n")

                elif block['BlockType'] == 'LINE':
                    text = block.get('Text', '')
                    confidence = block.get('Confidence', 0)

                    if text:
                        all_text_parts.append(text)
                        all_confidences.append(confidence)

            next_token = response.get('NextToken')
            if not next_token:
                break

        confidence_avg = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        full_text = '\n'.join(all_text_parts)

        logger.info(
            f"Textract extracted {len(all_text_parts)} text blocks from {pages_processed} pages, "
            f"avg confidence: {confidence_avg:.1f}%"
        )

        return full_text, pages_processed, confidence_avg


class OCRService:
    """
    Unified OCR service that tries Textract first, falls back to Tesseract.

    This is the main entry point for OCR functionality.
    """

    def __init__(self):
        """Initialize OCR services."""
        self.textract = TextractOCRService()
        self.tesseract = TesseractOCRService()

    async def extract_text(
        self,
        file_content: bytes,
        storage_path: Optional[str] = None
    ) -> Dict:
        """
        Extract text from a scanned PDF using the best available OCR engine.

        Tries Textract first (if available and storage_path provided),
        falls back to Tesseract for local development.

        Args:
            file_content: Raw PDF bytes
            storage_path: S3 storage path (required for Textract)

        Returns:
            Dictionary with extraction results including which engine was used
        """
        # Try Textract first if available and we have an S3 path
        if storage_path and self.textract.is_available():
            logger.info("Attempting OCR with AWS Textract")
            result = await self.textract.extract_text_from_s3_document(storage_path)

            if result['success']:
                result['ocr_engine'] = 'textract'
                return result
            else:
                logger.warning(f"Textract failed, falling back to Tesseract: {result['error']}")

        # Fall back to Tesseract
        if self.tesseract.is_available():
            logger.info("Using Tesseract OCR for text extraction")
            result = self.tesseract.extract_text_from_pdf_bytes(file_content)
            result['ocr_engine'] = 'tesseract'
            return result

        # No OCR available
        return {
            'success': False,
            'text': '',
            'pages_processed': 0,
            'confidence_avg': None,
            'ocr_engine': None,
            'error': 'No OCR engine available. Install Tesseract or configure AWS credentials.'
        }


# Singleton instances
textract_ocr_service = TextractOCRService()
tesseract_ocr_service = TesseractOCRService()
ocr_service = OCRService()
