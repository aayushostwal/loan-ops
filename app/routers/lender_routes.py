"""
Lender API Routes

API endpoints for lender document management and PDF processing.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.lender import Lender, LenderStatus
from app.services.ocr_service import OCRService
from app.db import engine

# Import Hatchet client getter
try:
    from app.workflows.lender_processing_workflow import get_hatchet_client
except ImportError:
    # Fallback if Hatchet is not installed
    def get_hatchet_client():
        return None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/lenders", tags=["lenders"])

# Initialize OCR service
ocr_service = OCRService()


# Pydantic models for request/response
class LenderResponse(BaseModel):
    """Response model for Lender data"""
    id: int
    lender_name: str
    policy_details: Optional[dict] = None
    processed_data: Optional[dict] = None
    status: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    original_filename: Optional[str] = None
    
    class Config:
        from_attributes = True


class LenderListResponse(BaseModel):
    """Response model for list of lenders"""
    total: int
    lenders: List[LenderResponse]


class UploadResponse(BaseModel):
    """Response model for PDF upload"""
    message: str
    lender_id: int
    status: str
    task_id: Optional[str] = None


# Dependency to get database session
async def get_db():
    """Database session dependency"""
    async with AsyncSession(engine) as session:
        try:
            yield session
        finally:
            await session.close()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF Document",
    description="Upload a PDF document for OCR processing and LLM analysis"
)
async def upload_pdf_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    lender_name: str = Form(..., description="Name of the lender"),
    policy_details: Optional[str] = Form(None, description="Optional policy details as JSON string"),
    created_by: Optional[str] = Form(None, description="User creating this record"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a PDF document and extract text using OCR.
    
    This endpoint:
    1. Validates the uploaded PDF file
    2. Extracts text using OCR (Tesseract)
    3. Stores the raw data in the database
    4. Triggers an async task for LLM processing
    
    Args:
        file: PDF file (multipart/form-data)
        lender_name: Name of the lender
        policy_details: Optional JSON string with policy details
        created_by: User who is uploading the document
        db: Database session (injected)
    
    Returns:
        UploadResponse with lender_id and task_id
    """
    logger.info(f"Received PDF upload request for lender: {lender_name}")
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Invalid file type: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Read file content
        logger.debug(f"Reading file: {file.filename}")
        pdf_content = await file.read()
        
        if not pdf_content:
            logger.error("Empty PDF file uploaded")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty PDF file"
            )
        
        logger.info(f"PDF file size: {len(pdf_content)} bytes")
        
        # Extract text using OCR
        logger.info("Starting OCR text extraction...")
        try:
            raw_text = await ocr_service.extract_text_from_pdf(pdf_content)
        except Exception as ocr_error:
            logger.error(f"OCR extraction failed: {str(ocr_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OCR processing failed: {str(ocr_error)}"
            )
        
        if not raw_text.strip():
            logger.warning("No text extracted from PDF")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text could be extracted from the PDF. The document may be empty or corrupted."
            )
        
        logger.info(f"OCR extraction successful. Extracted {len(raw_text)} characters")
        
        # Parse policy details if provided
        policy_dict = None
        if policy_details:
            try:
                import json
                policy_dict = json.loads(policy_details)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in policy_details, ignoring")
        
        # Create Lender record
        lender = Lender(
            lender_name=lender_name,
            policy_details=policy_dict,
            raw_data=raw_text,
            status=LenderStatus.UPLOADED,
            created_by=created_by,
            original_filename=file.filename
        )
        
        db.add(lender)
        await db.commit()
        await db.refresh(lender)
        
        logger.info(f"Created Lender record with ID: {lender.id}")
        
        # Trigger Hatchet workflow for processing
        workflow_run_id = None
        try:
            hatchet_client = get_hatchet_client()
            
            if hatchet_client:
                logger.info(f"Triggering Hatchet workflow for Lender ID: {lender.id}")
                
                # Trigger workflow
                workflow_run = hatchet_client.admin.run_workflow(
                    "lender-processing",
                    {
                        "lender_id": lender.id,
                        "lender_name": lender_name
                    }
                )
                
                workflow_run_id = workflow_run.workflow_run_id
                
                logger.info(f"Hatchet workflow triggered. Run ID: {workflow_run_id}")
            else:
                logger.warning("Hatchet client not available. Skipping workflow trigger.")
                
        except Exception as workflow_error:
            logger.error(f"Failed to trigger Hatchet workflow: {str(workflow_error)}")
            # Don't fail the request if workflow trigger fails
        
        logger.info(
            f"Upload successful. Lender ID: {lender.id}, Workflow Run ID: {workflow_run_id}"
        )
        
        return UploadResponse(
            message="PDF uploaded successfully. Processing started.",
            lender_id=lender.id,
            status=lender.status.value,
            task_id=workflow_run_id  # Now contains workflow_run_id instead of Celery task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get(
    "/{lender_id}",
    response_model=LenderResponse,
    summary="Get Lender by ID",
    description="Retrieve a specific lender record by ID"
)
async def get_lender(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a lender record by ID.
    
    Args:
        lender_id: ID of the lender
        db: Database session (injected)
    
    Returns:
        LenderResponse with full lender data
    """
    logger.info(f"Fetching Lender ID: {lender_id}")
    
    try:
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            logger.warning(f"Lender ID {lender_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lender with ID {lender_id} not found"
            )
        
        return LenderResponse(
            id=lender.id,
            lender_name=lender.lender_name,
            policy_details=lender.policy_details,
            processed_data=lender.processed_data,
            status=lender.status.value,
            created_by=lender.created_by,
            created_at=lender.created_at,
            updated_at=lender.updated_at,
            original_filename=lender.original_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch lender: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch lender: {str(e)}"
        )


@router.get(
    "/",
    response_model=LenderListResponse,
    summary="List All Lenders",
    description="Retrieve all lender records with optional filtering"
)
async def list_lenders(
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all lenders with optional filtering.
    
    Args:
        status_filter: Optional status filter (uploaded, processing, completed, failed)
        limit: Maximum number of records to return (default: 100)
        offset: Number of records to skip (default: 0)
        db: Database session (injected)
    
    Returns:
        LenderListResponse with list of lenders
    """
    logger.info(f"Listing lenders (status={status_filter}, limit={limit}, offset={offset})")
    
    try:
        # Build query
        query = select(Lender)
        
        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = LenderStatus(status_filter.lower())
                query = query.where(Lender.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )
        
        # Get total count
        count_result = await db.execute(query)
        total = len(count_result.all())
        
        # Apply pagination
        query = query.limit(limit).offset(offset).order_by(Lender.created_at.desc())
        
        # Execute query
        result = await db.execute(query)
        lenders = result.scalars().all()
        
        logger.info(f"Found {len(lenders)} lenders (total: {total})")
        
        return LenderListResponse(
            total=total,
            lenders=[
                LenderResponse(
                    id=lender.id,
                    lender_name=lender.lender_name,
                    policy_details=lender.policy_details,
                    processed_data=lender.processed_data,
                    status=lender.status.value,
                    created_by=lender.created_by,
                    created_at=lender.created_at,
                    updated_at=lender.updated_at,
                    original_filename=lender.original_filename
                )
                for lender in lenders
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list lenders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list lenders: {str(e)}"
        )


@router.delete(
    "/{lender_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Lender",
    description="Delete a lender record by ID"
)
async def delete_lender(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a lender record.
    
    Args:
        lender_id: ID of the lender to delete
        db: Database session (injected)
    """
    logger.info(f"Deleting Lender ID: {lender_id}")
    
    try:
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            logger.warning(f"Lender ID {lender_id} not found for deletion")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lender with ID {lender_id} not found"
            )
        
        await db.delete(lender)
        await db.commit()
        
        logger.info(f"Successfully deleted Lender ID: {lender_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete lender: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lender: {str(e)}"
        )

