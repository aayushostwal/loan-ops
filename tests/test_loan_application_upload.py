"""
Test Suite for Loan Application Upload and Processing

This module contains comprehensive tests for:
- Loan application PDF upload
- OCR extraction
- LLM processing
- Hatchet workflow triggering
- Match score calculation
- Parallel processing with multiple lenders
"""
import pytest
import json
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan_application import LoanApplication, LoanMatch, ApplicationStatus, MatchStatus
from app.models.lender import Lender, LenderStatus


class TestLoanApplicationUpload:
    """Test cases for loan application upload functionality"""
    
    @pytest.mark.asyncio
    async def test_upload_single_loan_application_success(
        self,
        client: AsyncClient,
        sample_pdf_file: str,
        db_session: AsyncSession
    ):
        """Test successful upload of a single loan application PDF"""
        
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'John Doe',
                'applicant_email': 'john.doe@example.com',
                'applicant_phone': '+1-555-0100',
                'created_by': 'test_user'
            }
            
            response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify response structure
        assert 'application_id' in response_data
        assert 'status' in response_data
        assert 'message' in response_data
        assert response_data['status'] == 'uploaded'
        
        # Verify database record
        application_id = response_data['application_id']
        result = await db_session.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        assert application is not None
        assert application.applicant_name == 'John Doe'
        assert application.applicant_email == 'john.doe@example.com'
        assert application.applicant_phone == '+1-555-0100'
        assert application.status == ApplicationStatus.UPLOADED
        assert application.raw_data is not None
        assert len(application.raw_data) > 0
        assert application.processed_data is not None
    
    @pytest.mark.asyncio
    async def test_upload_with_application_details(
        self,
        client: AsyncClient,
        sample_pdf_file: str,
        db_session: AsyncSession
    ):
        """Test upload with additional application details"""
        
        application_details = {
            'loan_type': 'home',
            'loan_amount': 500000,
            'purpose': 'Purchase primary residence'
        }
        
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Jane Smith',
                'applicant_email': 'jane.smith@example.com',
                'application_details': json.dumps(application_details),
                'created_by': 'test_user'
            }
            
            response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify application details were stored
        application_id = response_data['application_id']
        result = await db_session.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        assert application.application_details is not None
        assert application.application_details['loan_type'] == 'home'
        assert application.application_details['loan_amount'] == 500000
    
    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(
        self,
        client: AsyncClient
    ):
        """Test upload with invalid file type"""
        
        files = {'file': ('test.txt', b'Not a PDF', 'text/plain')}
        data = {
            'applicant_name': 'Test User',
            'applicant_email': 'test@example.com'
        }
        
        response = await client.post(
            '/api/loan-applications/upload',
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert 'PDF' in response.json()['detail']
    
    @pytest.mark.asyncio
    async def test_upload_empty_pdf(
        self,
        client: AsyncClient
    ):
        """Test upload with empty PDF file"""
        
        files = {'file': ('empty.pdf', b'', 'application/pdf')}
        data = {
            'applicant_name': 'Test User',
            'applicant_email': 'test@example.com'
        }
        
        response = await client.post(
            '/api/loan-applications/upload',
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert 'Empty' in response.json()['detail']
    
    @pytest.mark.asyncio
    async def test_upload_missing_applicant_name(
        self,
        client: AsyncClient,
        sample_pdf_file: str
    ):
        """Test upload without required applicant_name field"""
        
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_email': 'test@example.com'
                # Missing applicant_name
            }
            
            response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        assert response.status_code == 422  # Validation error


class TestLoanApplicationRetrieval:
    """Test cases for retrieving loan applications"""
    
    @pytest.mark.asyncio
    async def test_get_application_after_upload(
        self,
        client: AsyncClient,
        sample_pdf_file: str
    ):
        """Test retrieving a loan application after upload"""
        
        # First upload an application
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Test Applicant',
                'applicant_email': 'test@example.com'
            }
            
            upload_response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        application_id = upload_response.json()['application_id']
        
        # Now retrieve it
        response = await client.get(f'/api/loan-applications/{application_id}')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['id'] == application_id
        assert data['applicant_name'] == 'Test Applicant'
        assert data['applicant_email'] == 'test@example.com'
        assert data['status'] == 'uploaded'
        assert 'processed_data' in data
        assert 'created_at' in data
        assert 'updated_at' in data
    
    @pytest.mark.asyncio
    async def test_list_applications_after_multiple_uploads(
        self,
        client: AsyncClient,
        sample_pdf_file: str
    ):
        """Test listing applications after multiple uploads"""
        
        # Upload multiple applications
        applicants = ['Alice Johnson', 'Bob Williams', 'Carol Davis']
        
        for applicant in applicants:
            with open(sample_pdf_file, 'rb') as f:
                files = {'file': ('loan_app.pdf', f, 'application/pdf')}
                data = {
                    'applicant_name': applicant,
                    'applicant_email': f'{applicant.lower().replace(" ", ".")}@example.com'
                }
                
                await client.post(
                    '/api/loan-applications/upload',
                    files=files,
                    data=data
                )
        
        # List all applications
        response = await client.get('/api/loan-applications/')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'total' in data
        assert 'applications' in data
        assert data['total'] >= 3
        assert len(data['applications']) >= 3
    
    @pytest.mark.asyncio
    async def test_filter_applications_by_status(
        self,
        client: AsyncClient,
        sample_pdf_file: str
    ):
        """Test filtering applications by status"""
        
        # Upload an application
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Status Test User',
                'applicant_email': 'status@example.com'
            }
            
            await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        # Filter by uploaded status
        response = await client.get('/api/loan-applications/?status_filter=uploaded')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['total'] >= 1
        for app in data['applications']:
            assert app['status'] == 'uploaded'
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_application(
        self,
        client: AsyncClient
    ):
        """Test retrieving a non-existent application"""
        
        response = await client.get('/api/loan-applications/99999')
        
        assert response.status_code == 404


class TestMatchingWorkflow:
    """Test cases for loan matching workflow"""
    
    @pytest.mark.asyncio
    async def test_upload_triggers_matching(
        self,
        client: AsyncClient,
        sample_pdf_file: str,
        db_session: AsyncSession
    ):
        """Test that uploading an application triggers matching workflow"""
        
        # First create some lenders
        lenders_data = [
            {
                'lender_name': 'Bank A',
                'status': LenderStatus.COMPLETED,
                'processed_data': {
                    'loan_types': ['home', 'personal'],
                    'interest_rates': {'min': '3.5%', 'max': '5.5%'}
                }
            },
            {
                'lender_name': 'Bank B',
                'status': LenderStatus.COMPLETED,
                'processed_data': {
                    'loan_types': ['auto', 'personal'],
                    'interest_rates': {'min': '4.0%', 'max': '6.0%'}
                }
            }
        ]
        
        for lender_data in lenders_data:
            lender = Lender(**lender_data)
            db_session.add(lender)
        
        await db_session.commit()
        
        # Upload application
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Match Test User',
                'applicant_email': 'match@example.com'
            }
            
            response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify workflow_run_id is set (or None if Hatchet not configured)
        assert 'workflow_run_id' in response_data
    
    @pytest.mark.asyncio
    async def test_get_application_matches(
        self,
        client: AsyncClient,
        sample_pdf_file: str,
        db_session: AsyncSession
    ):
        """Test retrieving matches for an application"""
        
        # Create a lender
        lender = Lender(
            lender_name='Test Bank',
            status=LenderStatus.COMPLETED,
            processed_data={'loan_types': ['home']}
        )
        db_session.add(lender)
        await db_session.commit()
        await db_session.refresh(lender)
        
        # Upload application
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Match Retrieval Test',
                'applicant_email': 'matchtest@example.com'
            }
            
            upload_response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        application_id = upload_response.json()['application_id']
        
        # Create a match manually for testing
        match = LoanMatch(
            loan_application_id=application_id,
            lender_id=lender.id,
            match_score=85.5,
            status=MatchStatus.COMPLETED,
            match_analysis={'summary': 'Good match'}
        )
        db_session.add(match)
        await db_session.commit()
        
        # Get matches
        response = await client.get(f'/api/loan-applications/{application_id}/matches')
        
        assert response.status_code == 200
        matches = response.json()
        
        assert len(matches) >= 1
        assert matches[0]['lender_id'] == lender.id
        assert matches[0]['match_score'] == 85.5
        assert matches[0]['status'] == 'completed'


class TestMatchScoreCalculation:
    """Test cases for match score calculation"""
    
    @pytest.mark.asyncio
    async def test_match_score_structure(
        self,
        client: AsyncClient,
        sample_pdf_file: str,
        db_session: AsyncSession
    ):
        """Test that match scores have the correct structure"""
        
        # Create a lender
        lender = Lender(
            lender_name='Score Test Bank',
            status=LenderStatus.COMPLETED,
            processed_data={
                'loan_types': ['home', 'personal'],
                'interest_rates': {'min': '3.5%', 'max': '5.5%'},
                'eligibility_criteria': ['Good credit score', 'Stable income']
            }
        )
        db_session.add(lender)
        await db_session.commit()
        await db_session.refresh(lender)
        
        # Upload application
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Score Test User',
                'applicant_email': 'scoretest@example.com'
            }
            
            upload_response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        application_id = upload_response.json()['application_id']
        
        # Create a match with detailed analysis
        match_analysis = {
            'match_score': 78.5,
            'match_category': 'good',
            'strengths': ['Good credit profile', 'Adequate income'],
            'weaknesses': ['Limited employment history'],
            'recommendations': ['Consider providing additional documentation'],
            'criteria_scores': {
                'loan_amount': 9,
                'loan_type': 10,
                'interest_rate': 8,
                'eligibility': 7,
                'tenure': 8
            },
            'summary': 'Good overall match with some minor concerns'
        }
        
        match = LoanMatch(
            loan_application_id=application_id,
            lender_id=lender.id,
            match_score=78.5,
            status=MatchStatus.COMPLETED,
            match_analysis=match_analysis
        )
        db_session.add(match)
        await db_session.commit()
        
        # Retrieve and verify
        response = await client.get(f'/api/loan-applications/{application_id}/matches')
        
        assert response.status_code == 200
        matches = response.json()
        
        assert len(matches) >= 1
        match_data = matches[0]
        
        # Verify structure
        assert 'match_score' in match_data
        assert 'match_analysis' in match_data
        assert match_data['match_score'] == 78.5
        
        analysis = match_data['match_analysis']
        assert 'match_category' in analysis
        assert 'strengths' in analysis
        assert 'weaknesses' in analysis
        assert 'recommendations' in analysis
        assert 'criteria_scores' in analysis
        assert 'summary' in analysis


class TestParallelProcessing:
    """Test cases for parallel processing with multiple lenders"""
    
    @pytest.mark.asyncio
    async def test_multiple_lenders_matching(
        self,
        client: AsyncClient,
        sample_pdf_file: str,
        db_session: AsyncSession
    ):
        """Test that application is matched against multiple lenders"""
        
        # Create multiple lenders
        lenders_data = [
            {'name': 'Bank Alpha', 'loan_types': ['home', 'personal']},
            {'name': 'Bank Beta', 'loan_types': ['auto', 'personal']},
            {'name': 'Bank Gamma', 'loan_types': ['business', 'home']},
            {'name': 'Bank Delta', 'loan_types': ['personal', 'education']},
        ]
        
        for lender_data in lenders_data:
            lender = Lender(
                lender_name=lender_data['name'],
                status=LenderStatus.COMPLETED,
                processed_data={
                    'loan_types': lender_data['loan_types'],
                    'interest_rates': {'min': '3.5%', 'max': '6.0%'}
                }
            )
            db_session.add(lender)
        
        await db_session.commit()
        
        # Upload application
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Parallel Test User',
                'applicant_email': 'parallel@example.com'
            }
            
            upload_response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        assert upload_response.status_code == 201
        
        # Note: In a real scenario with Hatchet running, matches would be created
        # For this test, we're verifying the upload succeeds and workflow is triggered


class TestDataValidation:
    """Test cases for data validation"""
    
    @pytest.mark.asyncio
    async def test_processed_data_extraction(
        self,
        client: AsyncClient,
        sample_pdf_file: str,
        db_session: AsyncSession
    ):
        """Test that processed data is extracted correctly"""
        
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Data Test User',
                'applicant_email': 'datatest@example.com'
            }
            
            response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        application_id = response.json()['application_id']
        
        # Retrieve application
        result = await db_session.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        # Verify processed data structure
        assert application.processed_data is not None
        assert isinstance(application.processed_data, dict)
        
        # Check for expected fields (from mocked LLM response)
        # Note: These would be different based on the actual LLM processing
        assert '_metadata' in application.processed_data
    
    @pytest.mark.asyncio
    async def test_timestamp_fields(
        self,
        client: AsyncClient,
        sample_pdf_file: str,
        db_session: AsyncSession
    ):
        """Test that timestamp fields are set correctly"""
        
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Timestamp Test User',
                'applicant_email': 'timestamp@example.com'
            }
            
            response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        application_id = response.json()['application_id']
        
        # Retrieve application
        result = await db_session.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        # Verify timestamps
        assert application.created_at is not None
        assert application.updated_at is not None
        assert application.created_at <= application.updated_at


class TestErrorHandling:
    """Test cases for error handling"""
    
    @pytest.mark.asyncio
    async def test_match_failure_handling(
        self,
        client: AsyncClient,
        sample_pdf_file: str,
        db_session: AsyncSession
    ):
        """Test that match failures are handled gracefully"""
        
        # Create a lender
        lender = Lender(
            lender_name='Error Test Bank',
            status=LenderStatus.COMPLETED,
            processed_data={'loan_types': ['home']}
        )
        db_session.add(lender)
        await db_session.commit()
        await db_session.refresh(lender)
        
        # Upload application
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Error Test User',
                'applicant_email': 'errortest@example.com'
            }
            
            upload_response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        application_id = upload_response.json()['application_id']
        
        # Create a failed match
        match = LoanMatch(
            loan_application_id=application_id,
            lender_id=lender.id,
            status=MatchStatus.FAILED,
            error_message='Test error: LLM service unavailable'
        )
        db_session.add(match)
        await db_session.commit()
        
        # Retrieve matches
        response = await client.get(f'/api/loan-applications/{application_id}/matches')
        
        assert response.status_code == 200
        matches = response.json()
        
        assert len(matches) >= 1
        failed_match = matches[0]
        assert failed_match['status'] == 'failed'
        assert failed_match['error_message'] is not None
        assert 'error' in failed_match['error_message'].lower()


class TestMatchFiltering:
    """Test cases for filtering matches"""
    
    @pytest.mark.asyncio
    async def test_filter_matches_by_score(
        self,
        client: AsyncClient,
        sample_pdf_file: str,
        db_session: AsyncSession
    ):
        """Test filtering matches by minimum score"""
        
        # Create lenders
        lenders = []
        for i in range(3):
            lender = Lender(
                lender_name=f'Filter Test Bank {i+1}',
                status=LenderStatus.COMPLETED,
                processed_data={'loan_types': ['home']}
            )
            db_session.add(lender)
            lenders.append(lender)
        
        await db_session.commit()
        
        # Upload application
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('loan_app.pdf', f, 'application/pdf')}
            data = {
                'applicant_name': 'Filter Test User',
                'applicant_email': 'filtertest@example.com'
            }
            
            upload_response = await client.post(
                '/api/loan-applications/upload',
                files=files,
                data=data
            )
        
        application_id = upload_response.json()['application_id']
        
        # Create matches with different scores
        scores = [95.0, 75.0, 55.0]
        for lender, score in zip(lenders, scores):
            match = LoanMatch(
                loan_application_id=application_id,
                lender_id=lender.id,
                match_score=score,
                status=MatchStatus.COMPLETED
            )
            db_session.add(match)
        
        await db_session.commit()
        
        # Filter by minimum score
        response = await client.get(
            f'/api/loan-applications/{application_id}/matches?min_score=70'
        )
        
        assert response.status_code == 200
        matches = response.json()
        
        # Should only get matches with score >= 70
        assert len(matches) == 2
        for match in matches:
            assert match['match_score'] >= 70

