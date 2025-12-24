"""
Simple test to verify Celery mocking works without OCR dependencies.
"""
import pytest
from unittest.mock import patch, MagicMock


def test_celery_mock_imported():
    """Test that Celery can be imported without Redis."""
    # This should not raise any connection errors
    from app.celery_app import celery_app
    assert celery_app is not None


def test_celery_task_mock(mock_celery):
    """Test that Celery tasks are properly mocked."""
    # The mock_celery fixture should provide mocked task methods
    assert 'delay' in mock_celery
    assert 'apply_async' in mock_celery
    assert 'async_result' in mock_celery
    
    # Verify the mock async result
    assert mock_celery['async_result'].id == "test-task-id-12345"
    assert mock_celery['async_result'].state == "PENDING"


@pytest.mark.asyncio
async def test_celery_delay_mock():
    """Test that calling .delay() on a Celery task returns a mock result."""
    # Mock the task before importing
    with patch('app.tasks.lender_tasks.process_lender_document.delay') as mock_delay:
        mock_result = MagicMock()
        mock_result.id = "test-123"
        mock_delay.return_value = mock_result
        
        # Import and call the task
        from app.tasks.lender_tasks import process_lender_document
        
        # Call .delay() - this should NOT connect to Redis
        result = process_lender_document.delay(1)
        
        # Verify it was called and returned our mock
        mock_delay.assert_called_once_with(1)
        assert result.id == "test-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

