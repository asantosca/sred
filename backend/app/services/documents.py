# app/services/documents.py - Document management service

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status, UploadFile
import uuid
import logging
from typing import List, Optional

from app.models.models import Document, Group, UserGroup
from app.schemas.documents import DocumentUpload, DocumentUpdate
from app.services.s3 import s3_service

logger = logging.getLogger(__name__)

# Allowed file types
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.rtf'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

class DocumentService:
    """Service for managing documents"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def upload_document(
        self,
        file: UploadFile,
        upload_data: DocumentUpload,
        company_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Document:
        """Upload a document to S3 and create database record"""
        
        # Validate file
        self._validate_file(file)
        
        # Validate access groups belong to company
        if upload_data.access_groups:
            await self._validate_groups(upload_data.access_groups, company_id)
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        try:
            # Create document ID
            document_id = uuid.uuid4()
            
            # Upload to S3
            s3_path = s3_service.upload_file(
                file_content=file_content,
                company_id=company_id,
                document_id=document_id,
                filename=file.filename,
                content_type=file.content_type
            )
            
            # Create database record
            document = Document(
                id=document_id,
                filename=file.filename,
                original_filename=file.filename,
                file_size=file_size,
                content_type=file.content_type,
                s3_path=s3_path,
                company_id=company_id,
                uploaded_by=user_id,
                access_groups_json=[str(gid) for gid in upload_data.access_groups],
                tags=upload_data.tags,
                processing_status="uploaded"
            )
            
            self.db.add(document)
            await self.db.commit()
            
            logger.info(f"Document uploaded: {document_id} by user {user_id}")
            
            # TODO: Trigger background processing (text extraction, embeddings)
            
            return document
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to upload document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload document"
            )
    
    async def list_documents(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        is_admin: bool,
        page: int = 1,
        page_size: int = 20,
        tags: Optional[List[str]] = None
    ) -> tuple[List[Document], int]:
        """List documents accessible to user"""
        
        # Get user's groups
        user_groups_result = await self.db.execute(
            select(UserGroup.group_id).where(UserGroup.user_id == user_id)
        )
        user_group_ids = [str(row[0]) for row in user_groups_result]
        
        # Build query
        query = select(Document).where(Document.company_id == company_id)
        
        # Filter by tags if provided
        if tags:
            # Documents that have ANY of the specified tags
            query = query.where(
                or_(*[Document.tags.contains([tag]) for tag in tags])
            )
        
        # Access control: admin sees all, others see only their accessible docs
        if not is_admin:
            # User can see documents that:
            # 1. Have empty access_groups (public to company)
            # 2. Have user's group in access_groups
            query = query.where(
                or_(
                    Document.access_groups_json == [],
                    *[Document.access_groups_json.contains([gid]) for gid in user_group_ids]
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        offset = (page - 1) * page_size
        query = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        documents = result.scalars().all()
        
        return documents, total
    
    async def get_document(
        self,
        document_id: uuid.UUID,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        is_admin: bool
    ) -> Document:
        """Get document by ID with access control"""
        
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.company_id == company_id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check access
        if not is_admin:
            if not await self._user_can_access_document(document, user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document"
                )
        
        return document
    
    async def update_document(
        self,
        document_id: uuid.UUID,
        company_id: uuid.UUID,
        update_data: DocumentUpdate
    ) -> Document:
        """Update document metadata"""
        
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.company_id == company_id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Update fields
        if update_data.access_groups is not None:
            await self._validate_groups(update_data.access_groups, company_id)
            document.access_groups_json = [str(gid) for gid in update_data.access_groups]
        
        if update_data.tags is not None:
            document.tags = update_data.tags
        
        try:
            await self.db.commit()
            logger.info(f"Updated document: {document_id}")
            return document
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update document"
            )
    
    async def delete_document(
        self,
        document_id: uuid.UUID,
        company_id: uuid.UUID
    ) -> bool:
        """Delete document from S3 and database"""
        
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.company_id == company_id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        try:
            # Delete from S3
            s3_service.delete_file(document.s3_path)
            
            # Delete from database
            await self.db.delete(document)
            await self.db.commit()
            
            logger.info(f"Deleted document: {document_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
    
    def _validate_file(self, file: UploadFile):
        """Validate file type and name"""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Check file extension
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    async def _validate_groups(self, group_ids: List[uuid.UUID], company_id: uuid.UUID):
        """Validate that groups belong to company"""
        if not group_ids:
            return
        
        result = await self.db.execute(
            select(Group).where(
                Group.id.in_(group_ids),
                Group.company_id == company_id
            )
        )
        groups = result.scalars().all()
        
        if len(groups) != len(group_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more groups not found in your company"
            )
    
    async def _user_can_access_document(self, document: Document, user_id: uuid.UUID) -> bool:
        """Check if user can access document"""
        
        # Empty access_groups means all company users can access
        if not document.access_groups_json:
            return True
        
        # Get user's groups
        result = await self.db.execute(
            select(UserGroup.group_id).where(UserGroup.user_id == user_id)
        )
        user_group_ids = [str(row[0]) for row in result]
        
        # Check if user has any of the required groups
        return any(gid in document.access_groups_json for gid in user_group_ids)