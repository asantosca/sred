# app/services/s3.py - S3 storage service

import boto3
from botocore.exceptions import ClientError
import logging
from typing import Optional
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    """Service for managing document storage in S3"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist (for LocalStack)"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' exists")
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created S3 bucket '{self.bucket_name}'")
            except Exception as e:
                logger.error(f"Failed to create S3 bucket: {e}")
    
    def upload_file(
        self,
        file_content: bytes,
        company_id: uuid.UUID,
        document_id: uuid.UUID,
        filename: str,
        content_type: str
    ) -> str:
        """
        Upload file to S3
        
        Returns: S3 path
        """
        # Create S3 path: {company_id}/{document_id}/original.{ext}
        file_extension = filename.split('.')[-1] if '.' in filename else 'bin'
        s3_key = f"{company_id}/{document_id}/original.{file_extension}"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'document_id': str(document_id)
                }
            )
            
            logger.info(f"Uploaded file to S3: {s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    
    def download_file(self, s3_path: str) -> Optional[bytes]:
        """Download file from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_path
            )
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}")
            return None
    
    def delete_file(self, s3_path: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_path
            )
            logger.info(f"Deleted file from S3: {s3_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from S3: {e}")
            return False
    
    def get_file_url(self, s3_path: str, expires_in: int = 3600) -> str:
        """Generate pre-signed URL for file download"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_path
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

# Global S3 service instance
s3_service = S3Service()