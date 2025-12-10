# app/api/v1/endpoints/documents.py - Document upload and management endpoints

import logging
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Union
from uuid import UUID, uuid4
import os
import json
import math
from datetime import datetime, timedelta, date

from app.db.session import get_db
from app.schemas.documents import (
    Document, DocumentWithMatter, DocumentUploadResponse, DocumentListResponse,
    QuickDocumentUpload, StandardDocumentUpload, ContractUpload,
    PleadingUpload, CorrespondenceUpload, DiscoveryUpload, ExhibitUpload,
    DocumentDownloadResponse, FileValidationResult
)
from app.models.models import Document as DocumentModel, Matter, MatterAccess, User
from app.api.deps import get_current_user
from app.services.storage import storage_service
from app.services.document_intelligence import document_intelligence_service
from app.services.usage_tracker import UsageTracker
from app.services.document_processor import get_document_processor
from app.tasks.document_processing import process_document_pipeline
from app.core.rate_limit import limiter, get_rate_limit

router = APIRouter()
logger = logging.getLogger(__name__)

# Pre-upload Analysis Endpoint

@router.post("/analyze", response_model=dict)
@limiter.limit(get_rate_limit("document_analyze"))
async def analyze_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze a document file and return auto-detected metadata.
    Used for pre-upload suggestions to improve user experience.
    """
    try:
        # Read file content for analysis
        content = await file.read()
        
        # Reset file position for potential subsequent uploads
        await file.seek(0)
        
        # Detect metadata from filename and content
        detected = document_intelligence_service.detect_comprehensive(
            filename=file.filename,
            content=content.decode('utf-8', errors='ignore') if content else None
        )
        
        return {
            "detected_metadata": {
                "document_type": detected.document_type,
                "document_title": detected.document_title,
                "document_date": detected.document_date.isoformat() if detected.document_date else None,
                "author": detected.author,
                "recipient": detected.recipient,
                "subject": detected.subject,
                "contract_type": detected.contract_type,
                "court_jurisdiction": detected.court_jurisdiction,
                "case_number": detected.case_number,
                "opposing_party": detected.opposing_party,
                "discovery_type": detected.discovery_type,
                "exhibit_number": detected.exhibit_number,
                "confidence_score": detected.confidence_score
            },
            "suggestions": {
                "use_detected_title": detected.document_title is not None,
                "use_detected_date": detected.document_date is not None,
                "use_detected_type": detected.document_type is not None,
                "auto_fill_available": detected.confidence_score > 0.5
            },
            "file_info": {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content) if content else 0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error analyzing document: {str(e)}"
        )

# Document Upload Endpoints

@router.post("/upload/quick", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("document_upload"))
async def quick_upload_document(
    request: Request,
    file: UploadFile = File(...),
    matter_id: str = Form(...),
    document_type: str = Form(...),
    document_title: str = Form(...),
    document_date: str = Form(...),
    confidentiality_level: str = Form(default="standard_confidential"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Quick document upload with minimal required fields.
    Upload mode: ~60 seconds, 5 required fields.
    """
    # Parse form data into schema
    try:
        from datetime import datetime
        upload_data = QuickDocumentUpload(
            matter_id=UUID(matter_id),
            document_type=document_type,
            document_title=document_title,
            document_date=datetime.strptime(document_date, "%Y-%m-%d").date(),
            confidentiality_level=confidentiality_level
        )
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid form data: {str(e)}"
        )
    
    return await _process_document_upload(file, upload_data, current_user, db)

@router.post("/upload/standard", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def standard_upload_document(
    file: UploadFile = File(...),
    metadata: str = Form(..., description="JSON metadata for standard upload"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Standard document upload with enhanced metadata.
    Upload mode: ~2-3 minutes, includes security and basic metadata.
    """
    # Parse JSON metadata
    try:
        metadata_dict = json.loads(metadata)
        upload_data = StandardDocumentUpload(**metadata_dict)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metadata JSON: {str(e)}"
        )
    
    return await _process_document_upload(file, upload_data, current_user, db)

@router.post("/upload/contract", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    file: UploadFile = File(...),
    metadata: str = Form(..., description="JSON metadata for contract upload"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload contract document with contract-specific fields."""
    try:
        metadata_dict = json.loads(metadata)
        upload_data = ContractUpload(**metadata_dict)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid contract metadata: {str(e)}"
        )
    
    return await _process_document_upload(file, upload_data, current_user, db)

@router.post("/upload/pleading", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_pleading(
    file: UploadFile = File(...),
    metadata: str = Form(..., description="JSON metadata for pleading upload"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload pleading document with court-specific fields."""
    try:
        metadata_dict = json.loads(metadata)
        upload_data = PleadingUpload(**metadata_dict)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid pleading metadata: {str(e)}"
        )
    
    return await _process_document_upload(file, upload_data, current_user, db)

@router.post("/upload/correspondence", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_correspondence(
    file: UploadFile = File(...),
    metadata: str = Form(..., description="JSON metadata for correspondence upload"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload correspondence document with communication-specific fields."""
    try:
        metadata_dict = json.loads(metadata)
        upload_data = CorrespondenceUpload(**metadata_dict)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid correspondence metadata: {str(e)}"
        )
    
    return await _process_document_upload(file, upload_data, current_user, db)

@router.post("/upload/discovery", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_discovery(
    file: UploadFile = File(...),
    metadata: str = Form(..., description="JSON metadata for discovery upload"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload discovery document with discovery-specific fields."""
    try:
        metadata_dict = json.loads(metadata)
        upload_data = DiscoveryUpload(**metadata_dict)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid discovery metadata: {str(e)}"
        )
    
    return await _process_document_upload(file, upload_data, current_user, db)

@router.post("/upload/exhibit", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_exhibit(
    file: UploadFile = File(...),
    metadata: str = Form(..., description="JSON metadata for exhibit upload"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload exhibit document with exhibit-specific fields."""
    try:
        metadata_dict = json.loads(metadata)
        upload_data = ExhibitUpload(**metadata_dict)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid exhibit metadata: {str(e)}"
        )
    
    return await _process_document_upload(file, upload_data, current_user, db)

# Helper function for processing uploads
async def _process_document_upload(
    file: UploadFile,
    upload_data: Union[QuickDocumentUpload, StandardDocumentUpload, ContractUpload, 
                      PleadingUpload, CorrespondenceUpload, DiscoveryUpload, ExhibitUpload],
    current_user: User,
    db: AsyncSession
) -> DocumentUploadResponse:
    """
    Core document upload processing logic.
    Handles validation, storage, and database operations.
    """
    
    # 1. Validate user has upload access to the matter
    matter_access_query = select(MatterAccess).where(
        and_(
            MatterAccess.matter_id == upload_data.matter_id,
            MatterAccess.user_id == current_user.id,
            MatterAccess.can_upload == True
        )
    )
    matter_access_result = await db.execute(matter_access_query)
    matter_access = matter_access_result.scalar()
    
    if not matter_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No upload permission for this matter"
        )
    
    # 2. Validate matter exists and belongs to user's company
    matter_query = select(Matter).where(
        and_(
            Matter.id == upload_data.matter_id,
            Matter.company_id == current_user.company_id
        )
    )
    matter_result = await db.execute(matter_query)
    matter = matter_result.scalar()
    
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found"
        )
    
    # 3. Read and validate file
    try:
        file_content = await file.read()
        file_size = len(file_content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )

        # Initialize usage tracker
        usage_tracker = UsageTracker(db)

        # Check document count limit
        if not await usage_tracker.check_document_limit(current_user.company_id):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "Document limit reached",
                    "message": "Your plan's document limit has been reached. Please contact your administrator to upgrade.",
                    "limit_type": "documents"
                }
            )

        # Check document size limit
        if not await usage_tracker.check_document_size_limit(current_user.company_id, file_size):
            stats = await usage_tracker.get_plan_limits(current_user.company_id)
            max_mb = stats.get('max_document_size_mb', 10) if stats else 10
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": "Document too large",
                    "message": f"Document size ({file_size / (1024*1024):.1f} MB) exceeds plan limit ({max_mb} MB).",
                    "limit_type": "document_size",
                    "file_size_mb": round(file_size / (1024*1024), 2),
                    "max_size_mb": max_mb
                }
            )

        # Check storage limit
        if not await usage_tracker.check_storage_limit(current_user.company_id, file_size):
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail={
                    "error": "Storage limit reached",
                    "message": "Your plan's storage limit has been reached. Delete old documents or contact your administrator.",
                    "limit_type": "storage"
                }
            )

        # Validate file
        validation_result = storage_service.validate_file(
            filename=file.filename,
            file_size=file_size,
            file_content=file_content
        )

        if not validation_result['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File validation failed: {'; '.join(validation_result['errors'])}"
            )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading uploaded file: {str(e)}"
        )
    
    # 4. Auto-detect metadata to enhance upload data
    detected_enhancements = []
    auto_detection_applied = False
    
    try:
        detected = document_intelligence_service.detect_comprehensive(
            filename=file.filename,
            content=file_content.decode('utf-8', errors='ignore') if file_content else None
        )
        
        # Enrich upload data with detected metadata if fields are missing
        # Only apply detection if user hasn't provided specific values
        
        # For quick uploads, enhance basic fields if they're generic
        if hasattr(upload_data, 'document_title') and (
            upload_data.document_title.lower() in ['document', 'untitled', file.filename] or
            not upload_data.document_title.strip()
        ):
            if detected.document_title:
                upload_data.document_title = detected.document_title
                detected_enhancements.append('document_title')
                auto_detection_applied = True
        
        # Apply type-specific enhancements for richer upload modes
        if hasattr(upload_data, 'author') and not getattr(upload_data, 'author', None):
            if detected.author:
                setattr(upload_data, 'author', detected.author)
                detected_enhancements.append('author')
                auto_detection_applied = True
        
        if hasattr(upload_data, 'recipient') and not getattr(upload_data, 'recipient', None):
            if detected.recipient:
                setattr(upload_data, 'recipient', detected.recipient)
                detected_enhancements.append('recipient')
                auto_detection_applied = True
        
        if hasattr(upload_data, 'subject') and not getattr(upload_data, 'subject', None):
            if detected.subject:
                setattr(upload_data, 'subject', detected.subject)
                detected_enhancements.append('subject')
                auto_detection_applied = True
        
        # Apply court-specific fields for pleadings
        if hasattr(upload_data, 'court_jurisdiction') and not getattr(upload_data, 'court_jurisdiction', None):
            if detected.court_jurisdiction:
                setattr(upload_data, 'court_jurisdiction', detected.court_jurisdiction)
                detected_enhancements.append('court_jurisdiction')
                auto_detection_applied = True
        
        if hasattr(upload_data, 'case_number') and not getattr(upload_data, 'case_number', None):
            if detected.case_number:
                setattr(upload_data, 'case_number', detected.case_number)
                detected_enhancements.append('case_number')
                auto_detection_applied = True
        
        if hasattr(upload_data, 'opposing_party') and not getattr(upload_data, 'opposing_party', None):
            if detected.opposing_party:
                setattr(upload_data, 'opposing_party', detected.opposing_party)
                detected_enhancements.append('opposing_party')
                auto_detection_applied = True
        
        # Apply contract-specific fields
        if hasattr(upload_data, 'contract_type') and not getattr(upload_data, 'contract_type', None):
            if detected.contract_type:
                setattr(upload_data, 'contract_type', detected.contract_type)
                detected_enhancements.append('contract_type')
                auto_detection_applied = True
        
        # Apply discovery-specific fields
        if hasattr(upload_data, 'discovery_type') and not getattr(upload_data, 'discovery_type', None):
            if detected.discovery_type:
                setattr(upload_data, 'discovery_type', detected.discovery_type)
                detected_enhancements.append('discovery_type')
                auto_detection_applied = True
        
        # Apply exhibit-specific fields
        if hasattr(upload_data, 'exhibit_number') and not getattr(upload_data, 'exhibit_number', None):
            if detected.exhibit_number:
                setattr(upload_data, 'exhibit_number', detected.exhibit_number)
                detected_enhancements.append('exhibit_number')
                auto_detection_applied = True
        
    except Exception as e:
        # Log detection error but don't fail upload
        print(f"Auto-detection failed for {file.filename}: {str(e)}")
        # Continue with upload using original data
    
    # 5. Calculate file hash and check for duplicates
    file_hash = storage_service.calculate_file_hash(file_content)
    
    # Check for duplicate file in the same matter
    duplicate_query = select(DocumentModel).where(
        and_(
            DocumentModel.matter_id == upload_data.matter_id,
            DocumentModel.file_hash == file_hash
        )
    )
    duplicate_result = await db.execute(duplicate_query)
    existing_doc = duplicate_result.scalar()
    
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate file detected. Existing document: {existing_doc.document_title}"
        )
    
    # 5. Generate document ID and storage path
    document_id = uuid4()
    storage_path = storage_service.generate_file_path(
        company_id=current_user.company_id,
        matter_id=upload_data.matter_id,
        file_id=document_id,
        filename=file.filename
    )
    
    # 6. Upload file to S3
    upload_result = await storage_service.upload_file(
        file_content=file_content,
        storage_path=storage_path,
        content_type=validation_result['mime_type'],
        metadata={
            'document_id': str(document_id),
            'matter_id': str(upload_data.matter_id),
            'company_id': str(current_user.company_id),
            'uploaded_by': str(current_user.id),
            'document_title': upload_data.document_title,
            'document_type': upload_data.document_type
        }
    )
    
    if not upload_result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage"
        )
    
    # 7. Create document record in database
    try:
        # Set computed privilege flag
        is_privileged = (
            getattr(upload_data, 'privilege_attorney_client', False) or
            getattr(upload_data, 'privilege_work_product', False) or
            getattr(upload_data, 'privilege_settlement', False)
        )
        
        # Create document model
        document = DocumentModel(
            id=document_id,
            matter_id=upload_data.matter_id,
            filename=file.filename,
            original_filename=file.filename,
            file_extension=validation_result['file_extension'],
            file_size_bytes=file_size,
            storage_path=storage_path,
            file_hash=file_hash,
            mime_type=validation_result['mime_type'],
            document_type=upload_data.document_type,
            document_title=upload_data.document_title,
            document_date=upload_data.document_date,
            document_status=getattr(upload_data, 'document_status', 'draft'),
            confidentiality_level=upload_data.confidentiality_level,
            is_privileged=is_privileged,
            processing_status='pending',
            text_extracted=False,
            indexed_for_search=False,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        # Set optional fields if present in upload_data
        for field_name in [
            'document_subtype', 'privilege_attorney_client', 'privilege_work_product',
            'privilege_settlement', 'description', 'internal_notes', 'tags',
            'author', 'recipient', 'date_received', 'filed_date',
            # Contract fields
            'contract_type', 'contract_value', 'contract_effective_date',
            'contract_expiration_date', 'governing_law',
            # Pleading fields
            'court_jurisdiction', 'case_number', 'opposing_party', 
            'judge_name', 'opposing_counsel',
            # Correspondence fields
            'correspondence_type', 'cc', 'subject',
            # Discovery fields
            'discovery_type', 'propounding_party', 'responding_party',
            'discovery_number', 'response_due_date', 'response_status',
            # Exhibit fields
            'exhibit_number', 'related_to_document_id'
        ]:
            if hasattr(upload_data, field_name):
                value = getattr(upload_data, field_name)
                if value is not None:
                    setattr(document, field_name, value)
        
        db.add(document)
        await db.commit()
        await db.refresh(document)

        # Increment usage tracking after successful upload
        await usage_tracker.increment_document_count(current_user.company_id, file_size)

        # Trigger background task for full RAG pipeline (text extraction → chunking → embedding)
        try:
            task = process_document_pipeline.delay(str(document.id), str(current_user.company_id))
            logger.info(f"Triggered background processing for document {document.id}, task ID: {task.id}")
        except Exception as task_error:
            # Log error but don't fail the upload - can be retried manually later
            logger.error(f"Failed to trigger background task for document {document.id}: {str(task_error)}")
            # Document is saved, task can be retried via admin endpoint later

        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_size_bytes=document.file_size_bytes,
            document_title=document.document_title,
            document_type=document.document_type,
            matter_id=document.matter_id,
            storage_path=document.storage_path,
            file_hash=document.file_hash,
            upload_status="success",
            message="Document uploaded successfully" + (
                f" (Auto-detection enhanced {len(detected_enhancements)} fields)" 
                if auto_detection_applied else ""
            ),
            auto_detection_applied=auto_detection_applied,
            detected_enhancements=detected_enhancements
        )
        
    except Exception as e:
        # Rollback database changes
        await db.rollback()
        
        # Try to delete uploaded file
        try:
            await storage_service.delete_file(storage_path)
        except:
            pass  # File cleanup is best effort
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document metadata: {str(e)}"
        )

# File validation endpoint
@router.post("/validate", response_model=FileValidationResult)
async def validate_file_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Validate file before upload without saving.
    Useful for client-side validation feedback.
    """
    try:
        file_content = await file.read()
        file_size = len(file_content)
        
        validation_result = storage_service.validate_file(
            filename=file.filename,
            file_size=file_size,
            file_content=file_content
        )
        
        return FileValidationResult(**validation_result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error validating file: {str(e)}"
        )

# Document listing endpoint
@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    matter_id: Optional[UUID] = Query(None, description="Filter by matter ID"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    search: Optional[str] = Query(None, description="Search in title, type, or content"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List documents with filtering and pagination.
    Users can only see documents from matters they have access to.
    """
    # Build base query - documents from matters user has access to
    # Select both document and matter fields for DocumentWithMatter response
    query = (
        select(
            DocumentModel,
            Matter.matter_number,
            Matter.client_name,
            Matter.matter_status
        )
        .join(Matter, DocumentModel.matter_id == Matter.id)
        .join(MatterAccess, Matter.id == MatterAccess.matter_id)
        .where(
            and_(
                Matter.company_id == current_user.company_id,
                MatterAccess.user_id == current_user.id
            )
        )
    )
    
    # Apply filters
    if matter_id:
        query = query.where(DocumentModel.matter_id == matter_id)
    
    if document_type:
        query = query.where(DocumentModel.document_type == document_type)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                DocumentModel.document_title.ilike(search_term),
                DocumentModel.document_type.ilike(search_term),
                DocumentModel.document_subtype.ilike(search_term),
                DocumentModel.description.ilike(search_term),
                DocumentModel.internal_notes.ilike(search_term),
                DocumentModel.author.ilike(search_term),
                DocumentModel.recipient.ilike(search_term),
                DocumentModel.subject.ilike(search_term),
                DocumentModel.opposing_party.ilike(search_term),
                DocumentModel.case_number.ilike(search_term),
                DocumentModel.court_jurisdiction.ilike(search_term),
                DocumentModel.filename.ilike(search_term),
                DocumentModel.original_filename.ilike(search_term)
            )
        )
    
    # Count total records
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(DocumentModel.created_at.desc())

    # Execute query
    result = await db.execute(query)
    rows = result.all()

    # Build DocumentWithMatter objects from query results
    documents_with_matter = []
    for row in rows:
        doc, matter_number, client_name, matter_status = row
        doc_dict = Document.model_validate(doc).model_dump()
        doc_dict['matter_number'] = matter_number
        doc_dict['client_name'] = client_name
        doc_dict['matter_status'] = matter_status
        documents_with_matter.append(DocumentWithMatter(**doc_dict))

    # Calculate pagination info
    pages = math.ceil(total / size) if total > 0 else 1

    return DocumentListResponse(
        documents=documents_with_matter,
        total=total,
        page=page,
        size=size,
        pages=pages,
        matter_id=matter_id
    )

# Advanced document search endpoint
@router.post("/search", response_model=DocumentListResponse)
async def advanced_document_search(
    matter_id: Optional[UUID] = None,
    query_text: Optional[str] = None,
    document_types: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    confidentiality_levels: Optional[List[str]] = None,
    authors: Optional[List[str]] = None,
    recipients: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    case_numbers: Optional[List[str]] = None,
    include_privileged: bool = True,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Advanced document search with multiple filters and criteria.
    Provides sophisticated search within matters and across user's accessible documents.
    """
    
    # Build base query with user access control
    query = select(DocumentModel).join(
        MatterAccess, and_(
            MatterAccess.matter_id == DocumentModel.matter_id,
            MatterAccess.user_id == current_user.id,
            MatterAccess.can_view == True
        )
    ).join(
        Matter, and_(
            Matter.id == DocumentModel.matter_id,
            Matter.company_id == current_user.company_id
        )
    )
    
    # Apply filters
    if matter_id:
        query = query.where(DocumentModel.matter_id == matter_id)
    
    if query_text:
        search_term = f"%{query_text}%"
        query = query.where(
            or_(
                DocumentModel.document_title.ilike(search_term),
                DocumentModel.description.ilike(search_term),
                DocumentModel.internal_notes.ilike(search_term),
                DocumentModel.author.ilike(search_term),
                DocumentModel.recipient.ilike(search_term),
                DocumentModel.subject.ilike(search_term),
                DocumentModel.opposing_party.ilike(search_term),
                DocumentModel.filename.ilike(search_term)
            )
        )
    
    if document_types:
        query = query.where(DocumentModel.document_type.in_(document_types))
    
    if date_from:
        query = query.where(DocumentModel.document_date >= date_from)
    
    if date_to:
        query = query.where(DocumentModel.document_date <= date_to)
    
    if confidentiality_levels:
        query = query.where(DocumentModel.confidentiality_level.in_(confidentiality_levels))
    
    if authors:
        author_conditions = [DocumentModel.author.ilike(f"%{author}%") for author in authors]
        query = query.where(or_(*author_conditions))
    
    if recipients:
        recipient_conditions = [DocumentModel.recipient.ilike(f"%{recipient}%") for recipient in recipients]
        query = query.where(or_(*recipient_conditions))
    
    if case_numbers:
        case_conditions = [DocumentModel.case_number.ilike(f"%{case}%") for case in case_numbers]
        query = query.where(or_(*case_conditions))
    
    if not include_privileged:
        query = query.where(DocumentModel.is_privileged == False)
    
    # Count total records
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(
        DocumentModel.document_date.desc(),
        DocumentModel.created_at.desc()
    )
    
    # Execute query
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Calculate pagination info
    pages = math.ceil(total / size) if total > 0 else 1
    
    return DocumentListResponse(
        documents=[Document.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        size=size,
        pages=pages,
        matter_id=matter_id
    )

# Duplicate detection endpoint
@router.post("/check-duplicates", response_model=dict)
async def check_for_duplicates(
    file: UploadFile = File(...),
    matter_id: Optional[UUID] = Query(None, description="Limit search to specific matter"),
    check_scope: str = Query("matter", description="Scope: 'matter' or 'company'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check for duplicate files before upload.
    Compares file hash against existing documents.
    """
    try:
        # Read file content and calculate hash
        file_content = await file.read()
        await file.seek(0)  # Reset file position
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file provided"
            )
        
        file_hash = storage_service.calculate_file_hash(file_content)
        
        # Build query based on scope
        if check_scope == "matter" and matter_id:
            # Check within specific matter
            query = select(DocumentModel).join(
                MatterAccess, and_(
                    MatterAccess.matter_id == DocumentModel.matter_id,
                    MatterAccess.user_id == current_user.id,
                    MatterAccess.can_view == True
                )
            ).where(
                and_(
                    DocumentModel.matter_id == matter_id,
                    DocumentModel.file_hash == file_hash
                )
            )
        else:
            # Check across all accessible documents in company
            query = select(DocumentModel).join(
                MatterAccess, and_(
                    MatterAccess.matter_id == DocumentModel.matter_id,
                    MatterAccess.user_id == current_user.id,
                    MatterAccess.can_view == True
                )
            ).join(
                Matter, and_(
                    Matter.id == DocumentModel.matter_id,
                    Matter.company_id == current_user.company_id
                )
            ).where(DocumentModel.file_hash == file_hash)
        
        result = await db.execute(query)
        duplicates = result.scalars().all()
        
        if duplicates:
            duplicate_info = []
            for doc in duplicates:
                # Get matter info for each duplicate
                matter_query = select(Matter).where(Matter.id == doc.matter_id)
                matter_result = await db.execute(matter_query)
                matter = matter_result.scalar()
                
                duplicate_info.append({
                    "document_id": str(doc.id),
                    "document_title": doc.document_title,
                    "document_type": doc.document_type,
                    "matter_id": str(doc.matter_id),
                    "matter_number": matter.matter_number if matter else "Unknown",
                    "client_name": matter.client_name if matter else "Unknown",
                    "upload_date": doc.created_at.isoformat(),
                    "filename": doc.filename,
                    "file_size": doc.file_size_bytes
                })
            
            return {
                "has_duplicates": True,
                "duplicate_count": len(duplicates),
                "duplicates": duplicate_info,
                "file_hash": file_hash,
                "uploaded_file": {
                    "filename": file.filename,
                    "size": len(file_content),
                    "content_type": file.content_type
                },
                "recommendation": "Consider reviewing existing documents before uploading"
            }
        else:
            return {
                "has_duplicates": False,
                "duplicate_count": 0,
                "duplicates": [],
                "file_hash": file_hash,
                "uploaded_file": {
                    "filename": file.filename,
                    "size": len(file_content),
                    "content_type": file.content_type
                },
                "recommendation": "No duplicates found. Safe to upload."
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error checking for duplicates: {str(e)}"
        )

# Document status tracking endpoints
@router.patch("/{document_id}/status", response_model=dict)
async def update_document_status(
    document_id: UUID,
    new_status: str = Query(..., description="New document status"),
    notes: Optional[str] = Query(None, description="Optional notes about status change"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update document status with tracking and audit logging.
    Valid statuses: draft, under_review, approved, final, executed, filed, archived
    """
    
    # Validate status
    valid_statuses = ['draft', 'under_review', 'approved', 'final', 'executed', 'filed', 'archived']
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Valid options: {', '.join(valid_statuses)}"
        )
    
    # Check document access
    document_query = select(DocumentModel).join(
        MatterAccess, and_(
            MatterAccess.matter_id == DocumentModel.matter_id,
            MatterAccess.user_id == current_user.id,
            MatterAccess.can_edit == True
        )
    ).join(
        Matter, and_(
            Matter.id == DocumentModel.matter_id,
            Matter.company_id == current_user.company_id
        )
    ).where(DocumentModel.id == document_id)
    
    document_result = await db.execute(document_query)
    document = document_result.scalar()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or no edit permission"
        )
    
    # Store previous status for tracking
    previous_status = document.document_status
    
    if previous_status == new_status:
        return {
            "success": True,
            "message": f"Document already has status '{new_status}'",
            "document_id": str(document_id),
            "previous_status": previous_status,
            "current_status": new_status,
            "changed": False
        }
    
    # Update document status
    document.document_status = new_status
    document.updated_at = datetime.utcnow()
    document.updated_by = current_user.id
    
    # Add status change notes if provided
    if notes:
        status_note = f"Status changed from '{previous_status}' to '{new_status}': {notes}"
        if document.internal_notes:
            document.internal_notes += f"\n\n[{datetime.utcnow().isoformat()}] {status_note}"
        else:
            document.internal_notes = f"[{datetime.utcnow().isoformat()}] {status_note}"
    
    try:
        await db.commit()
        await db.refresh(document)
        
        return {
            "success": True,
            "message": f"Document status updated successfully",
            "document_id": str(document_id),
            "previous_status": previous_status,
            "current_status": new_status,
            "changed": True,
            "updated_at": document.updated_at.isoformat(),
            "updated_by": str(current_user.id)
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document status: {str(e)}"
        )

@router.get("/statuses", response_model=dict)
async def get_document_statuses(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of valid document statuses and their descriptions.
    """
    statuses = {
        "draft": "Document is in draft form, not yet ready for review",
        "under_review": "Document is being reviewed by team members",
        "approved": "Document has been approved but not yet finalized",
        "final": "Document is in final form",
        "executed": "Contract or agreement has been executed/signed",
        "filed": "Document has been filed with court or authorities",
        "archived": "Document is archived and no longer active"
    }
    
    return {
        "valid_statuses": statuses,
        "workflow_order": ["draft", "under_review", "approved", "final", "executed", "filed", "archived"]
    }

@router.get("/{document_id}/status-history", response_model=dict)
async def get_document_status_history(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status change history for a document from internal notes.
    """
    
    # Check document access
    document_query = select(DocumentModel).join(
        MatterAccess, and_(
            MatterAccess.matter_id == DocumentModel.matter_id,
            MatterAccess.user_id == current_user.id,
            MatterAccess.can_view == True
        )
    ).join(
        Matter, and_(
            Matter.id == DocumentModel.matter_id,
            Matter.company_id == current_user.company_id
        )
    ).where(DocumentModel.id == document_id)
    
    document_result = await db.execute(document_query)
    document = document_result.scalar()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or no view permission"
        )
    
    # Parse status history from internal notes
    history = []
    if document.internal_notes:
        import re
        
        # Look for status change entries in internal notes
        pattern = r'\[([^\]]+)\] Status changed from \'([^\']+)\' to \'([^\']+)\'(?:: (.+))?'
        matches = re.findall(pattern, document.internal_notes)
        
        for match in matches:
            timestamp, from_status, to_status, notes = match
            history.append({
                "timestamp": timestamp,
                "from_status": from_status,
                "to_status": to_status,
                "notes": notes.strip() if notes else None
            })
    
    return {
        "document_id": str(document_id),
        "current_status": document.document_status,
        "created_at": document.created_at.isoformat(),
        "last_updated": document.updated_at.isoformat() if document.updated_at else None,
        "status_history": history,
        "total_changes": len(history)
    }

# Document download endpoint
@router.get("/{document_id}/download", response_model=DocumentDownloadResponse)
async def get_document_download_url(
    document_id: UUID,
    expiration: int = Query(3600, ge=300, le=86400, description="URL expiration in seconds (5min - 24hrs)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate presigned download URL for document.
    Requires read access to the matter.
    """
    # Check if user has access to this document
    access_query = (
        select(DocumentModel)
        .join(Matter, DocumentModel.matter_id == Matter.id)
        .join(MatterAccess, Matter.id == MatterAccess.matter_id)
        .where(
            and_(
                DocumentModel.id == document_id,
                Matter.company_id == current_user.company_id,
                MatterAccess.user_id == current_user.id
            )
        )
    )
    access_result = await db.execute(access_query)
    document = access_result.scalar()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    
    # Generate presigned URL
    download_url = storage_service.generate_presigned_url(
        storage_path=document.storage_path,
        expiration=expiration,
        http_method='GET'
    )
    
    return DocumentDownloadResponse(
        download_url=download_url,
        expires_at=datetime.utcnow() + timedelta(seconds=expiration),
        filename=document.original_filename,
        file_size_bytes=document.file_size_bytes,
        mime_type=document.mime_type or 'application/octet-stream'
    )

# Document info endpoint
@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document metadata by ID."""
    # Check access and get document
    access_query = (
        select(DocumentModel)
        .join(Matter, DocumentModel.matter_id == Matter.id)
        .join(MatterAccess, Matter.id == MatterAccess.matter_id)
        .where(
            and_(
                DocumentModel.id == document_id,
                Matter.company_id == current_user.company_id,
                MatterAccess.user_id == current_user.id
            )
        )
    )
    access_result = await db.execute(access_query)
    document = access_result.scalar()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    
    return Document.model_validate(document)

# Document metadata update endpoint
@router.patch("/{document_id}", response_model=Document)
async def update_document(
    document_id: UUID,
    document_title: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    document_date: Optional[date] = Form(None),
    document_status: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    confidentiality_level: Optional[str] = Form(None),
    is_privileged: Optional[bool] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string of array
    internal_notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update document metadata (not the file content).
    Requires edit access to the matter.
    """
    # Check if user has edit access
    access_query = (
        select(DocumentModel, MatterAccess.can_edit)
        .join(Matter, DocumentModel.matter_id == Matter.id)
        .join(MatterAccess, Matter.id == MatterAccess.matter_id)
        .where(
            and_(
                DocumentModel.id == document_id,
                Matter.company_id == current_user.company_id,
                MatterAccess.user_id == current_user.id
            )
        )
    )
    access_result = await db.execute(access_query)
    row = access_result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )

    document, can_edit = row
    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this document"
        )

    # Update fields if provided
    if document_title is not None:
        document.document_title = document_title
    if document_type is not None:
        document.document_type = document_type
    if document_date is not None:
        document.document_date = document_date
    if document_status is not None:
        document.document_status = document_status
    if description is not None:
        document.description = description if description else None
    if confidentiality_level is not None:
        document.confidentiality_level = confidentiality_level
    if is_privileged is not None:
        document.is_privileged = is_privileged
    if tags is not None:
        document.tags = json.loads(tags) if tags else None
    if internal_notes is not None:
        document.internal_notes = internal_notes if internal_notes else None

    # Update audit fields
    document.updated_at = datetime.utcnow()
    document.updated_by = str(current_user.id)

    await db.commit()
    await db.refresh(document)

    return Document.model_validate(document)


# Document deletion endpoint
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete document. Requires delete access to the matter."""
    # Check if user has delete access
    access_query = (
        select(DocumentModel, MatterAccess.can_delete)
        .join(Matter, DocumentModel.matter_id == Matter.id)
        .join(MatterAccess, Matter.id == MatterAccess.matter_id)
        .where(
            and_(
                DocumentModel.id == document_id,
                Matter.company_id == current_user.company_id,
                MatterAccess.user_id == current_user.id
            )
        )
    )
    access_result = await db.execute(access_query)
    result = access_result.first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    
    document, can_delete = result
    
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No delete permission for documents in this matter"
        )
    
    # Delete file from storage
    try:
        await storage_service.delete_file(document.storage_path)
    except Exception as e:
        # Log error but continue with database deletion
        print(f"Warning: Failed to delete file from storage: {e}")
    
    # Delete from database
    await db.delete(document)
    await db.commit()    
    return {"message": "Document deleted successfully", "document_id": str(document_id)}


# Document Processing Status Endpoint
@router.get("/{document_id}/processing-status", response_model=dict)
async def get_document_processing_status(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current processing status of a document.
    
    Returns processing status, whether it's indexed for search, and any error information.
    """
    # Get document and verify access with tenant isolation
    document_query = select(DocumentModel).join(
        MatterAccess, and_(
            MatterAccess.matter_id == DocumentModel.matter_id,
            MatterAccess.user_id == current_user.id,
            MatterAccess.can_view == True
        )
    ).join(
        Matter, and_(
            Matter.id == DocumentModel.matter_id,
            Matter.company_id == current_user.company_id  # Tenant isolation
        )
    ).where(DocumentModel.id == document_id)
    
    document_result = await db.execute(document_query)
    document = document_result.scalar()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    
    # Get chunk count  
    from app.models.models import DocumentChunk
    chunk_count_query = select(func.count()).where(DocumentChunk.document_id == document_id)
    chunk_result = await db.execute(chunk_count_query)
    chunk_count = chunk_result.scalar() or 0
    
    return {
        "document_id": str(document.id),
        "document_title": document.document_title,
        "processing_status": document.processing_status,
        "text_extracted": document.text_extracted,
        "indexed_for_search": document.indexed_for_search,
        "chunk_count": chunk_count,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
        "status_description": {
            "pending": "Waiting to be processed",
            "processing": "Currently being processed",
            "chunked": "Text chunked, generating embeddings",
            "embedded": "Ready for search",
            "failed": "Processing failed, will retry"
        }.get(document.processing_status, "Unknown status")
    }
