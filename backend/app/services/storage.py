# app/services/storage.py - File storage service with S3 integration

import os
import boto3
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, BinaryIO
from uuid import UUID
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.core.config import settings

class StorageService:
    """Service for handling file storage operations with S3"""
    
    def __init__(self):
        """Initialize S3 client"""
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if settings.AWS_REGION == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                        )
                    print(f"Created S3 bucket: {self.bucket_name}")
                except ClientError as create_error:
                    print(f"Error creating bucket: {create_error}")
            else:
                print(f"Error checking bucket: {e}")
    
    def generate_file_path(self, company_id: UUID, matter_id: UUID, file_id: UUID, filename: str) -> str:
        """
        Generate organized file path for storage
        Format: companies/{company_id}/matters/{matter_id}/documents/{file_id}/{filename}
        """
        return f"companies/{company_id}/matters/{matter_id}/documents/{file_id}/{filename}"
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def validate_file(self, filename: str, file_size: int, file_content: bytes = None) -> dict:
        """
        Validate uploaded file
        Returns validation result with any errors
        """
        errors = []
        
        # Check file size (50MB limit)
        max_size = 50 * 1024 * 1024  # 50MB in bytes
        if file_size > max_size:
            errors.append(f"File size ({file_size:,} bytes) exceeds maximum allowed size (50MB)")
        
        # Check file extension
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.msg', '.eml'}
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            errors.append(f"File extension '{file_ext}' not allowed. Allowed: {', '.join(allowed_extensions)}")
        
        # Additional MIME type validation if content is provided
        if file_content:
            mime_type = self.get_mime_type(filename)
            allowed_mime_types = {
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'text/plain',
                'application/vnd.ms-outlook',
                'message/rfc822'
            }
            
            # Note: We're checking based on extension for now
            # In production, you might want to use python-magic for content-based detection
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'file_extension': file_ext,
            'mime_type': self.get_mime_type(filename),
            'file_size': file_size
        }
    
    async def upload_file(
        self,
        file_content: bytes,
        storage_path: str,
        content_type: str = None,
        metadata: dict = None
    ) -> dict:
        """
        Upload file to S3
        Returns upload result with S3 key and metadata
        """
        try:
            # Prepare upload parameters
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': storage_path,
                'Body': file_content,
            }
            
            if content_type:
                upload_params['ContentType'] = content_type
            
            if metadata:
                # Convert metadata to string values (S3 requirement)
                s3_metadata = {k: str(v) for k, v in metadata.items()}
                upload_params['Metadata'] = s3_metadata
            
            # Upload file
            self.s3_client.put_object(**upload_params)
            
            return {
                'success': True,
                'storage_path': storage_path,
                'bucket': self.bucket_name,
                'size': len(file_content)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to storage: {error_code}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during file upload: {str(e)}"
            )
    
    async def get_file(self, storage_path: str) -> bytes:
        """Download file from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return response['Body'].read()
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found in storage"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to retrieve file from storage: {error_code}"
                )
    
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return True
        except ClientError as e:
            # Log error but don't raise - file might already be deleted
            print(f"Error deleting file {storage_path}: {e}")
            return False
    
    def generate_presigned_url(
        self,
        storage_path: str,
        expiration: int = 3600,
        http_method: str = 'GET'
    ) -> str:
        """
        Generate presigned URL for secure file access
        Default expiration: 1 hour
        """
        try:
            url = self.s3_client.generate_presigned_url(
                http_method,
                Params={'Bucket': self.bucket_name, 'Key': storage_path},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate download URL: {e}"
            )
    
    def check_file_exists(self, storage_path: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return True
        except ClientError:
            return False
    
    def get_file_info(self, storage_path: str) -> dict:
        """Get file metadata from S3"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return {
                'content_length': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found in storage"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get file info: {error_code}"
                )

# Create global storage service instance
storage_service = StorageService()