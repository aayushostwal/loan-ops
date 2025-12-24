"""
Test Cases for Lender Upload API

This module contains comprehensive tests for PDF upload, processing, and data validation.

IMPORTANT: These tests use mocked services to avoid external dependencies:
1. OCR Service is mocked to return sample text from the "ADVANTAGE BROKER 2025" PDF
2. LLM Service is mocked to return a predefined structured response
   - This allows deterministic testing without calling OpenAI API
   - The mock response structure matches real LLM output format
3. All assertions are based on the mocked responses defined in conftest.py

The expected_llm_response fixture provides the exact structure returned by the mock.
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
        db_session.expire_all()
        
        # Verify processing result
        assert result["success"] is True
        assert result["lender_id"] == lender_id
        assert result["status"] == "completed"
        
        # Verify database state after processing
        db_result = await db_session.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = db_result.scalar_one()
        
        # Verify status is COMPLETED with mocked LLM
        assert lender.status == LenderStatus.COMPLETED
        
        # Verify processed_data structure from mocked LLM response
        assert lender.processed_data is not None
        assert isinstance(lender.processed_data, dict)
        
        # Assert specific fields from mocked LLM response
        assert "loan_types" in lender.processed_data
        assert lender.processed_data["loan_types"] == ["Fixed Rate", "Variable Rate", "Interest Only"]
        
        assert "interest_rates" in lender.processed_data
        assert lender.processed_data["interest_rates"]["fixed_rate"]["min"] == "3.5%"
        assert lender.processed_data["interest_rates"]["fixed_rate"]["max"] == "4.5%"
        assert lender.processed_data["interest_rates"]["variable_rate"]["min"] == "2.5%"
        assert lender.processed_data["interest_rates"]["variable_rate"]["max"] == "3.5%"
        
        assert "loan_amount_range" in lender.processed_data
        assert lender.processed_data["loan_amount_range"]["min"] == "$50,000"
        assert lender.processed_data["loan_amount_range"]["max"] == "$5,000,000"
        
        assert "contact_information" in lender.processed_data
        assert lender.processed_data["contact_information"]["email"] == "info@samplelender.com"
        assert lender.processed_data["contact_information"]["phone"] == "1800 123 456"
        
        # Verify metadata from mocked LLM
        assert "_metadata" in lender.processed_data
        assert lender.processed_data["_metadata"]["processing_successful"] is True
        assert lender.processed_data["_metadata"]["model"] == "gpt-4o-mini"
        
        # Verify validation data added by validate_and_enrich_data
        assert "_validation" in lender.processed_data
        assert lender.processed_data["_validation"]["completeness_score"] == 1.0
        assert lender.processed_data["_validation"]["field_completeness"]["loan_types"] is True
    
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
    async def test_llm_response_structure(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_pdf_file: str,
        expected_llm_response: dict
    ):
        """Test that LLM processing returns the expected mocked structure."""
        # Upload PDF
        with open(sample_pdf_file, "rb") as f:
            files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
            data = {
                "lender_name": "LLM Response Test",
                "created_by": "test_user"
            }
            
            response = await client.post(
                "/api/lenders/upload",
                files=files,
                data=data
            )
        
        assert response.status_code == 201
        lender_id = response.json()["lender_id"]
        
        # Process the document
        processing_result = await _process_lender_document_async(lender_id)
        
        # Refresh session
        db_session.expire_all()
        
        # Verify processing was successful
        assert processing_result["success"] is True
        
        # Get the processed lender
        result = await db_session.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one()
        
        # Verify status
        assert lender.status == LenderStatus.COMPLETED
        
        # Comprehensive validation of processed_data against expected mock
        processed_data = lender.processed_data
        
        # Compare all top-level keys (excluding _validation which is added by enrichment)
        for key in expected_llm_response.keys():
            assert key in processed_data, f"Missing key: {key}"
            assert processed_data[key] == expected_llm_response[key], \
                f"Mismatch in {key}: expected {expected_llm_response[key]}, got {processed_data[key]}"
        
        # Verify the enrichment added validation data
        assert "_validation" in processed_data
        assert "field_completeness" in processed_data["_validation"]
        assert "completeness_score" in processed_data["_validation"]
        
        # Validate specific nested structures
        assert processed_data["interest_rates"]["fixed_rate"]["min"] == "3.5%"
        assert processed_data["interest_rates"]["variable_rate"]["max"] == "3.5%"
        assert processed_data["loan_amount_range"]["min"] == "$50,000"
        assert processed_data["loan_amount_range"]["max"] == "$5,000,000"
        assert processed_data["tenure"]["min"] == "1 year"
        assert processed_data["tenure"]["max"] == "30 years"
        
        # Validate arrays
        assert len(processed_data["loan_types"]) == 3
        assert len(processed_data["eligibility_criteria"]) == 3
        assert len(processed_data["documents_required"]) == 4
        assert len(processed_data["key_terms"]) == 3
        assert len(processed_data["special_offers"]) == 2
        
        # Validate contact information
        contact = processed_data["contact_information"]
        assert contact["email"] == "info@samplelender.com"
        assert contact["phone"] == "1800 123 456"
        assert contact["website"] == "www.advantagebroker.com"
        
        # Validate metadata
        metadata = processed_data["_metadata"]
        assert metadata["model"] == "gpt-4o-mini"
        assert metadata["temperature"] == 0.2
        assert metadata["tokens_used"] == 850
        assert metadata["processing_successful"] is True
    
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
        db_session.expire_all()
        
        # Step 4: Verify processing result
        assert "success" in processing_result
        assert processing_result["success"] is True
        assert processing_result["lender_id"] == lender_id
        assert processing_result["status"] == "completed"
        
        # Verify processed_data in the result
        assert "processed_data" in processing_result
        processed = processing_result["processed_data"]
        
        # Assert key fields from mocked LLM response
        assert processed["loan_types"] == ["Fixed Rate", "Variable Rate", "Interest Only"]
        assert processed["eligibility_criteria"] == [
            "Minimum credit score: 650",
            "Stable employment history",
            "Valid identification"
        ]
        assert len(processed["documents_required"]) == 4
        assert "Proof of identity" in processed["documents_required"]
        
        # Step 5: Verify final state via API
        get_response = await client.get(f"/api/lenders/{lender_id}")
        assert get_response.status_code == 200
        
        final_data = get_response.json()
        assert final_data["status"] == "completed"
        assert "processed_data" in final_data
        
        # Step 6: Verify final state in database
        result = await db_session.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender_after = result.scalar_one()
        
        assert lender_after.status == LenderStatus.COMPLETED
        assert lender_after.raw_data is not None
        assert lender_after.processed_data is not None
        
        # Detailed assertions on processed data structure
        processed_data = lender_after.processed_data
        assert isinstance(processed_data, dict)
        
        # Verify all expected fields are present
        expected_fields = [
            "loan_types", "interest_rates", "eligibility_criteria",
            "loan_amount_range", "tenure", "processing_fees",
            "documents_required", "key_terms", "contact_information",
            "special_offers", "_metadata", "_validation"
        ]
        for field in expected_fields:
            assert field in processed_data, f"Missing field: {field}"
        
        # Verify specific data values from mock
        assert processed_data["key_terms"] == [
            "LVR up to 95%",
            "Interest only option available",
            "Fixed and variable rate options"
        ]
        assert processed_data["processing_fees"] == "Application fee applies"
        assert processed_data["tenure"]["min"] == "1 year"
        assert processed_data["tenure"]["max"] == "30 years"
    
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
        db_session.expire_all()
        
        # Verify all processing results
        for result in processing_results:
            assert result["success"] is True
            assert "lender_id" in result
            assert result["status"] == "completed"
        
        # Verify all have been processed in database
        result = await db_session.execute(
            select(Lender).where(Lender.id.in_(lender_ids))
        )
        processed_lenders = result.scalars().all()
        
        assert len(processed_lenders) == len(all_pdf_files)
        
        # All should have COMPLETED status with mocked LLM
        for lender in processed_lenders:
            assert lender.status == LenderStatus.COMPLETED
            assert lender.raw_data is not None
            assert lender.processed_data is not None
            
            # Verify each has the mocked LLM response structure
            assert "loan_types" in lender.processed_data
            assert len(lender.processed_data["loan_types"]) == 3
            assert "Fixed Rate" in lender.processed_data["loan_types"]
            
            assert "contact_information" in lender.processed_data
            assert lender.processed_data["contact_information"]["email"] == "info@samplelender.com"
            
            # Verify metadata
            assert "_metadata" in lender.processed_data
            assert lender.processed_data["_metadata"]["processing_successful"] is True
            
            # Verify validation
            assert "_validation" in lender.processed_data
            assert lender.processed_data["_validation"]["completeness_score"] == 1.0


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

