"""
Loan Application API Routes

API endpoints for loan application management and processing.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.loan_application import LoanApplication, LoanMatch, ApplicationStatus, MatchStatus
from app.services.ocr_service import OCRService
from app.services.llm_service import LLMService
from app.models.lender import Lender
try:
    from app.workflows.hatchet_config import hatchet_client as hatchet_client_instance
except ImportError:
    hatchet_client_instance = None
from app.db import engine
from app.workflows.loan_matching_workflow import ProcessApplicationDataInput
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/loan-applications", tags=["loan-applications"])

# Initialize services
ocr_service = OCRService()
llm_service = LLMService()


# Pydantic models for request/response
class LoanMatchResponse(BaseModel):
    """Response model for Loan Match data"""
    id: int
    lender_id: int
    lender_name: Optional[str] = None
    match_score: Optional[float] = None
    match_analysis: Optional[dict] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LoanApplicationResponse(BaseModel):
    """Response model for Loan Application data"""
    id: int
    applicant_name: str
    applicant_email: Optional[str] = None
    applicant_phone: Optional[str] = None
    application_details: Optional[dict] = None
    processed_data: Optional[dict] = None
    status: str
    workflow_run_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    original_filename: Optional[str] = None
    matches: Optional[List[LoanMatchResponse]] = None
    
    class Config:
        from_attributes = True


class LoanApplicationListResponse(BaseModel):
    """Response model for list of loan applications"""
    total: int
    applications: List[LoanApplicationResponse]


class UploadApplicationResponse(BaseModel):
    """Response model for loan application upload"""
    message: str
    application_id: int
    status: str
    workflow_run_id: Optional[str] = None


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
    response_model=UploadApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Loan Application PDF",
    description="Upload a loan application PDF for OCR processing and matching against lenders"
)
async def upload_loan_application(
    file: UploadFile = File(..., description="PDF file to upload"),
    applicant_name: str = Form(..., description="Name of the applicant"),
    applicant_email: Optional[str] = Form(None, description="Email of the applicant"),
    applicant_phone: Optional[str] = Form(None, description="Phone number of the applicant"),
    application_details: Optional[str] = Form(None, description="Optional application details as JSON string"),
    created_by: Optional[str] = Form(None, description="User creating this record"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a loan application PDF and process it against all lenders.
    
    This endpoint:
    1. Validates the uploaded PDF file
    2. Extracts text using OCR (Tesseract)
    3. Processes the text using LLM to extract structured data
    4. Stores the application in the database
    5. Triggers Hatchet workflow for parallel matching against all lenders
    
    Args:
        file: PDF file (multipart/form-data)
        applicant_name: Name of the applicant
        applicant_email: Email of the applicant
        applicant_phone: Phone number of the applicant
        application_details: Optional JSON string with application details
        created_by: User who is uploading the document
        db: Database session (injected)
    
    Returns:
        UploadApplicationResponse with application_id and workflow_run_id
    """
    logger.info(f"Received loan application upload request for applicant: {applicant_name}")
    
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
        
        # LLM processing will be handled by the workflow
        # Parse application details if provided
        application_dict = None
        if application_details:
            try:
                import json
                application_dict = json.loads(application_details)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in application_details, ignoring")
        
        # Create LoanApplication record (processed_data will be set by workflow)
        loan_application = LoanApplication(
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            applicant_phone=applicant_phone,
            application_details=application_dict,
            raw_data=raw_text,
            processed_data=None,  # Will be processed by workflow
            status=ApplicationStatus.UPLOADED,
            created_by=created_by,
            original_filename=file.filename
        )
        
        db.add(loan_application)
        await db.commit()
        await db.refresh(loan_application)
        
        logger.info(f"Created LoanApplication record with ID: {loan_application.id}")
        
        # Trigger Hatchet workflow for parallel matching
        workflow_run_id = None
        try:
            if hatchet_client_instance:
                logger.info(f"Triggering Hatchet workflow for Application ID: {loan_application.id}")
                
                from app.workflows.loan_matching_workflow import loan_matching_workflow
                loan_matching_workflow.run_no_wait(ProcessApplicationDataInput(application_id=loan_application.id, raw_text=raw_text, applicant_name=applicant_name))
            else:
                logger.warning("Hatchet client not available. Skipping workflow trigger.")
        except Exception as workflow_error:
            logger.error(f"Failed to trigger Hatchet workflow: {str(workflow_error)}")
            # Don't fail the request if workflow trigger fails
            # The application is still created and can be processed manually
            # The application is still created and can be processed manually
        
        
        return UploadApplicationResponse(message="Loan application uploaded successfully. Matching process started.", application_id=loan_application.id, status=loan_application.status.value)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get(
    "/{application_id}",
    response_model=LoanApplicationResponse,
    summary="Get Loan Application by ID",
    description="Retrieve a specific loan application with its matches"
)
async def get_loan_application(
    application_id: int,
    include_matches: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a loan application by ID with optional matches.
    
    Args:
        application_id: ID of the loan application
        include_matches: Whether to include match results (default: True)
        db: Database session (injected)
    
    Returns:
        LoanApplicationResponse with full application data and matches
    """
    logger.info(f"Fetching Loan Application ID: {application_id}")
    
    try:
        # Build query
        query = select(LoanApplication).where(LoanApplication.id == application_id)
        
        if include_matches:
            query = query.options(selectinload(LoanApplication.matches))
        
        result = await db.execute(query)
        application = result.scalar_one_or_none()
        
        if not application:
            logger.warning(f"Loan Application ID {application_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Loan Application with ID {application_id} not found"
            )
        
        # Build response
        response_data = {
            "id": application.id,
            "applicant_name": application.applicant_name,
            "applicant_email": application.applicant_email,
            "applicant_phone": application.applicant_phone,
            "application_details": application.application_details,
            "processed_data": application.processed_data,
            "status": application.status.value,
            "workflow_run_id": application.workflow_run_id,
            "created_by": application.created_by,
            "created_at": application.created_at,
            "updated_at": application.updated_at,
            "original_filename": application.original_filename
        }
        
        if include_matches and application.matches:
            response_data["matches"] = [
                {
                    "id": match.id,
                    "lender_id": match.lender_id,
                    "lender_name": (await db.execute(select(Lender).where(Lender.id == match.lender_id))).scalar_one_or_none().lender_name,
                    "match_score": match.match_score,
                    "match_analysis": match.match_analysis,
                    "status": match.status.value,
                    "error_message": match.error_message,
                    "created_at": match.created_at,
                    "updated_at": match.updated_at
                }
                for match in application.matches
            ]
        
        return LoanApplicationResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch loan application: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch loan application: {str(e)}"
        )


@router.get(
    "/",
    response_model=LoanApplicationListResponse,
    summary="List All Loan Applications",
    description="Retrieve all loan applications with optional filtering"
)
async def list_loan_applications(
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all loan applications with optional filtering.
    
    Args:
        status_filter: Optional status filter (uploaded, processing, completed, failed)
        limit: Maximum number of records to return (default: 100)
        offset: Number of records to skip (default: 0)
        db: Database session (injected)
    
    Returns:
        LoanApplicationListResponse with list of applications
    """
    logger.info(f"Listing loan applications (status={status_filter}, limit={limit}, offset={offset})")
    
    try:
        # Build query
        query = select(LoanApplication)
        
        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = ApplicationStatus(status_filter.lower())
                query = query.where(LoanApplication.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )
        
        # Get total count
        count_result = await db.execute(query)
        total = len(count_result.all())
        
        # Apply pagination
        query = query.limit(limit).offset(offset).order_by(LoanApplication.created_at.desc())
        
        # Execute query
        result = await db.execute(query)
        applications = result.scalars().all()
        
        logger.info(f"Found {len(applications)} applications (total: {total})")
        
        return LoanApplicationListResponse(
            total=total,
            applications=[
                LoanApplicationResponse(
                    id=app.id,
                    applicant_name=app.applicant_name,
                    applicant_email=app.applicant_email,
                    applicant_phone=app.applicant_phone,
                    application_details=app.application_details,
                    processed_data=app.processed_data,
                    status=app.status.value,
                    workflow_run_id=app.workflow_run_id,
                    created_by=app.created_by,
                    created_at=app.created_at,
                    updated_at=app.updated_at,
                    original_filename=app.original_filename
                )
                for app in applications
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list loan applications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list loan applications: {str(e)}"
        )


@router.get(
    "/{application_id}/matches",
    response_model=List[LoanMatchResponse],
    summary="Get Matches for Application",
    description="Retrieve all match results for a specific loan application"
)
async def get_application_matches(
    application_id: int,
    status_filter: Optional[str] = None,
    min_score: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all matches for a loan application with optional filtering.
    
    Args:
        application_id: ID of the loan application
        status_filter: Optional status filter (pending, processing, completed, failed)
        min_score: Minimum match score to filter by
        db: Database session (injected)
    
    Returns:
        List of LoanMatchResponse objects
    """
    logger.info(f"Fetching matches for Application ID: {application_id}")
    
    try:
        # Verify application exists
        app_result = await db.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = app_result.scalar_one_or_none()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Loan Application with ID {application_id} not found"
            )
        
        # Build query for matches
        query = select(LoanMatch).where(LoanMatch.loan_application_id == application_id)
        
        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = MatchStatus(status_filter.lower())
                query = query.where(LoanMatch.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )
        
        # Apply score filter if provided
        if min_score is not None:
            query = query.where(LoanMatch.match_score >= min_score)
        
        # Order by match score descending
        query = query.order_by(LoanMatch.match_score.desc())
        
        # Execute query
        result = await db.execute(query)
        matches = result.scalars().all()
        
        logger.info(f"Found {len(matches)} matches for application {application_id}")
        
        return [
            LoanMatchResponse(
                id=match.id,
                lender_id=match.lender_id,
                match_score=match.match_score,
                match_analysis=match.match_analysis,
                status=match.status.value,
                error_message=match.error_message,
                created_at=match.created_at,
                updated_at=match.updated_at
            )
            for match in matches
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch matches: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch matches: {str(e)}"
        )


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Loan Application",
    description="Delete a loan application and all its matches"
)
async def delete_loan_application(
    application_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a loan application and all associated matches.
    
    Args:
        application_id: ID of the loan application to delete
        db: Database session (injected)
    """
    logger.info(f"Deleting Loan Application ID: {application_id}")
    
    try:
        result = await db.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            logger.warning(f"Loan Application ID {application_id} not found for deletion")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Loan Application with ID {application_id} not found"
            )
        
        await db.delete(application)
        await db.commit()
        
        logger.info(f"Successfully deleted Loan Application ID: {application_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete loan application: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete loan application: {str(e)}"
        )

