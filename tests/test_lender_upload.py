"""
Test Cases for Lender Upload API

This module contains comprehensive tests for PDF upload, processing, and data validation.
"""
import json
import os
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lender import Lender, LenderStatus
from app.tasks.lender_tasks import _process_lender_document_async


class TestLenderUpload:
    """Test suite for lender PDF upload functionality."""
    
    @pytest.mark.asyncio
    async def test_upload_single_pdf_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_pdf_file: str
    ):
        """Test successful upload of a single PDF file."""
        # Prepare form data
        with open(sample_pdf_file, "rb") as f:
            files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
            data = {
                "lender_name": "Test Lender",
                "created_by": "test_user"
            }
            
            # Upload PDF
            response = await client.post(
                "/api/lenders/upload",
                files=files,
                data=data
            )
        
        # Assertions on response
        assert response.status_code == 201
        response_data = response.json()
        
        assert "lender_id" in response_data
        assert "message" in response_data
        assert "status" in response_data
        assert response_data["status"] == "uploaded"
        
        lender_id = response_data["lender_id"]
        
        # Assertions on database
        result = await db_session.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        assert lender is not None
        assert lender.lender_name == "Test Lender"
        assert lender.status == LenderStatus.UPLOADED
        assert lender.raw_data is not None
        assert len(lender.raw_data) > 0
        assert lender.created_by == "test_user"
        assert lender.original_filename == os.path.basename(sample_pdf_file)
        assert lender.processed_data is None  # Not processed yet
    
    @pytest.mark.asyncio
    async def test_upload_with_policy_details(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_pdf_file: str
    ):
        """Test upload with additional policy details."""
        policy_details = {
            "policy_type": "Commercial",
            "coverage_amount": 1000000,
            "term": "12 months"
        }
        
        with open(sample_pdf_file, "rb") as f:
            files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
            data = {
                "lender_name": "Premium Lender",
                "policy_details": json.dumps(policy_details),
                "created_by": "admin"
            }
            
            response = await client.post(
                "/api/lenders/upload",
                files=files,
                data=data
            )
        
        assert response.status_code == 201
        lender_id = response.json()["lender_id"]
        
        # Verify policy details are stored
        result = await db_session.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one()
        
        assert lender.policy_details is not None
        assert lender.policy_details["policy_type"] == "Commercial"
        assert lender.policy_details["coverage_amount"] == 1000000
        assert lender.policy_details["term"] == "12 months"
    
    @pytest.mark.asyncio
    async def test_upload_multiple_pdfs(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        all_pdf_files: list[str]
    ):
        """Test uploading multiple PDF files."""
        uploaded_ids = []
        
        for idx, pdf_file in enumerate(all_pdf_files):
            with open(pdf_file, "rb") as f:
                files = {"file": (os.path.basename(pdf_file), f, "application/pdf")}
                data = {
                    "lender_name": f"Lender {idx + 1}",
                    "created_by": "batch_user"
                }
                
                response = await client.post(
                    "/api/lenders/upload",
                    files=files,
                    data=data
                )
            
            assert response.status_code == 201
            uploaded_ids.append(response.json()["lender_id"])
        
        # Verify all uploads in database
        result = await db_session.execute(select(Lender))
        all_lenders = result.scalars().all()
        
        assert len(all_lenders) == len(all_pdf_files)
        assert all(lender.status == LenderStatus.UPLOADED for lender in all_lenders)
        assert all(lender.raw_data is not None for lender in all_lenders)
    
    @pytest.mark.asyncio
    async def test_upload_and_process(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_pdf_file: str
    ):
        """Test upload followed by manual processing (without Celery)."""
        # Upload PDF
        with open(sample_pdf_file, "rb") as f:
            files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
            data = {
                "lender_name": "Process Test Lender",
                "created_by": "processor"
            }
            
            response = await client.post(
                "/api/lenders/upload",
                files=files,
                data=data
            )
        
        assert response.status_code == 201
        lender_id = response.json()["lender_id"]
        
        # Manually call the processing function (bypassing Celery)
        result = await _process_lender_document_async(lender_id)
        
        # Refresh session to get updated data
        await db_session.expire_all()
        
        # Verify processing result
        assert result["success"] is True
        assert result["lender_id"] == lender_id
        
        # Verify database state after processing
        db_result = await db_session.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = db_result.scalar_one()
        
        # The status might be COMPLETED or FAILED depending on LLM processing
        assert lender.status in [LenderStatus.COMPLETED, LenderStatus.FAILED]
        
        # If completed, processed_data should be populated
        if lender.status == LenderStatus.COMPLETED:
            assert lender.processed_data is not None
            assert isinstance(lender.processed_data, dict)
    
    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(
        self,
        client: AsyncClient,
    ):
        """Test upload with non-PDF file."""
        # Create a fake text file
        files = {"file": ("test.txt", b"Not a PDF", "text/plain")}
        data = {
            "lender_name": "Invalid Upload",
            "created_by": "test_user"
        }
        
        response = await client.post(
            "/api/lenders/upload",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "Only PDF files are allowed" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_empty_pdf(
        self,
        client: AsyncClient,
    ):
        """Test upload with empty file."""
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        data = {
            "lender_name": "Empty Upload",
            "created_by": "test_user"
        }
        
        response = await client.post(
            "/api/lenders/upload",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "Empty PDF file" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_missing_lender_name(
        self,
        client: AsyncClient,
        sample_pdf_file: str
    ):
        """Test upload without required lender_name field."""
        with open(sample_pdf_file, "rb") as f:
            files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
            data = {
                "created_by": "test_user"
                # lender_name is missing
            }
            
            response = await client.post(
                "/api/lenders/upload",
                files=files,
                data=data
            )
        
        assert response.status_code == 422  # Validation error


class TestLenderRetrievalAfterUpload:
    """Test suite for retrieving lender data after upload."""
    
    @pytest.mark.asyncio
    async def test_get_lender_after_upload(
        self,
        client: AsyncClient,
        sample_pdf_file: str
    ):
        """Test retrieving a lender record after upload."""
        # Upload
        with open(sample_pdf_file, "rb") as f:
            files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
            data = {"lender_name": "Retrieve Test", "created_by": "user"}
            
            upload_response = await client.post(
                "/api/lenders/upload",
                files=files,
                data=data
            )
        
        lender_id = upload_response.json()["lender_id"]
        
        # Retrieve
        get_response = await client.get(f"/api/lenders/{lender_id}")
        
        assert get_response.status_code == 200
        lender_data = get_response.json()
        
        assert lender_data["id"] == lender_id
        assert lender_data["lender_name"] == "Retrieve Test"
        assert lender_data["status"] == "uploaded"
        assert lender_data["created_by"] == "user"
        assert lender_data["original_filename"] == os.path.basename(sample_pdf_file)
    
    @pytest.mark.asyncio
    async def test_list_lenders_after_multiple_uploads(
        self,
        client: AsyncClient,
        all_pdf_files: list[str]
    ):
        """Test listing all lenders after multiple uploads."""
        # Upload multiple files
        upload_count = min(3, len(all_pdf_files))  # Upload up to 3 files
        
        for idx in range(upload_count):
            with open(all_pdf_files[idx], "rb") as f:
                files = {"file": (os.path.basename(all_pdf_files[idx]), f, "application/pdf")}
                data = {
                    "lender_name": f"List Test Lender {idx + 1}",
                    "created_by": "batch_user"
                }
                
                await client.post("/api/lenders/upload", files=files, data=data)
        
        # List all lenders
        list_response = await client.get("/api/lenders/")
        
        assert list_response.status_code == 200
        list_data = list_response.json()
        
        assert list_data["total"] >= upload_count
        assert len(list_data["lenders"]) >= upload_count
        
        # Verify all have uploaded status
        uploaded_lenders = [
            l for l in list_data["lenders"]
            if l["lender_name"].startswith("List Test Lender")
        ]
        assert len(uploaded_lenders) == upload_count
        assert all(l["status"] == "uploaded" for l in uploaded_lenders)
    
    @pytest.mark.asyncio
    async def test_filter_lenders_by_status(
        self,
        client: AsyncClient,
        sample_pdf_file: str
    ):
        """Test filtering lenders by status."""
        # Upload a file
        with open(sample_pdf_file, "rb") as f:
            files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
            data = {"lender_name": "Filter Test", "created_by": "user"}
            
            await client.post("/api/lenders/upload", files=files, data=data)
        
        # Filter by uploaded status
        response = await client.get("/api/lenders/?status_filter=uploaded")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 1
        assert all(l["status"] == "uploaded" for l in data["lenders"])


class TestProcessingWorkflow:
    """Test suite for the complete upload and processing workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_assertions(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_pdf_file: str
    ):
        """Test complete workflow: upload -> process -> verify."""
        # Step 1: Upload
        with open(sample_pdf_file, "rb") as f:
            files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
            data = {
                "lender_name": "Workflow Test Lender",
                "created_by": "workflow_user"
            }
            
            upload_response = await client.post(
                "/api/lenders/upload",
                files=files,
                data=data
            )
        
        assert upload_response.status_code == 201
        lender_id = upload_response.json()["lender_id"]
        
        # Step 2: Verify initial state
        result = await db_session.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender_before = result.scalar_one()
        
        assert lender_before.status == LenderStatus.UPLOADED
        assert lender_before.raw_data is not None
        assert lender_before.processed_data is None
        
        # Step 3: Process (manually, without Celery)
        processing_result = await _process_lender_document_async(lender_id)
        
        # Refresh the session
        await db_session.expire_all()
        
        # Step 4: Verify processing result
        assert "success" in processing_result
        assert processing_result["lender_id"] == lender_id
        
        # Step 5: Verify final state via API
        get_response = await client.get(f"/api/lenders/{lender_id}")
        assert get_response.status_code == 200
        
        final_data = get_response.json()
        assert final_data["status"] in ["completed", "failed"]
        
        # Step 6: Verify final state in database
        result = await db_session.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender_after = result.scalar_one()
        
        assert lender_after.status in [LenderStatus.COMPLETED, LenderStatus.FAILED]
        assert lender_after.raw_data is not None
        
        # If completed successfully, verify processed data structure
        if lender_after.status == LenderStatus.COMPLETED:
            assert lender_after.processed_data is not None
            assert isinstance(lender_after.processed_data, dict)
            # Add more specific assertions based on your LLM output structure
    
    @pytest.mark.asyncio
    async def test_process_all_uploaded_pdfs(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        all_pdf_files: list[str]
    ):
        """Test processing all uploaded PDFs."""
        lender_ids = []
        
        # Upload all PDFs
        for idx, pdf_file in enumerate(all_pdf_files):
            with open(pdf_file, "rb") as f:
                files = {"file": (os.path.basename(pdf_file), f, "application/pdf")}
                data = {
                    "lender_name": f"Batch Process Lender {idx + 1}",
                    "created_by": "batch_processor"
                }
                
                response = await client.post(
                    "/api/lenders/upload",
                    files=files,
                    data=data
                )
            
            assert response.status_code == 201
            lender_ids.append(response.json()["lender_id"])
        
        # Process each one
        processing_results = []
        for lender_id in lender_ids:
            result = await _process_lender_document_async(lender_id)
            processing_results.append(result)
        
        # Refresh session
        await db_session.expire_all()
        
        # Verify all have been processed
        result = await db_session.execute(
            select(Lender).where(Lender.id.in_(lender_ids))
        )
        processed_lenders = result.scalars().all()
        
        assert len(processed_lenders) == len(all_pdf_files)
        
        # All should have moved beyond UPLOADED status
        for lender in processed_lenders:
            assert lender.status in [
                LenderStatus.COMPLETED,
                LenderStatus.FAILED,
                LenderStatus.PROCESSING
            ]
            assert lender.raw_data is not None


class TestDataValidation:
    """Test suite for data validation and integrity."""
    
    @pytest.mark.asyncio
    async def test_raw_data_extraction(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_pdf_file: str
    ):
        """Test that OCR correctly extracts text from PDF."""
        with open(sample_pdf_file, "rb") as f:
            files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
            data = {"lender_name": "OCR Test", "created_by": "user"}
            
            response = await client.post(
                "/api/lenders/upload",
                files=files,
                data=data
            )
        
        lender_id = response.json()["lender_id"]
        
        # Verify raw data
        result = await db_session.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one()
        
        assert lender.raw_data is not None
        assert len(lender.raw_data) > 0
        assert isinstance(lender.raw_data, str)
    
    @pytest.mark.asyncio
    async def test_timestamp_fields(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_pdf_file: str
    ):
        """Test that timestamp fields are correctly set."""
        with open(sample_pdf_file, "rb") as f:
            files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
            data = {"lender_name": "Timestamp Test", "created_by": "user"}
            
            response = await client.post(
                "/api/lenders/upload",
                files=files,
                data=data
            )
        
        lender_id = response.json()["lender_id"]
        
        result = await db_session.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one()
        
        assert lender.created_at is not None
        assert lender.updated_at is not None
        assert lender.created_at <= lender.updated_at

