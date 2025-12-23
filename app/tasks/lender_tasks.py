"""
Lender Processing Tasks

Async Celery tasks for processing lender documents.
"""
import logging
from typing import Any, Dict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio

from app.celery_app import celery_app
from app.models.lender import Lender, LenderStatus
from app.services.llm_service import LLMService
from app.db import DATABASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create async engine for task processing
task_engine = create_async_engine(DATABASE_URL, echo=False)
TaskAsyncSession = sessionmaker(
    task_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def _process_lender_document_async(lender_id: int) -> Dict[str, Any]:
    """
    Async function to process lender document.
    
    Args:
        lender_id: ID of the Lender record to process
    
    Returns:
        Dict containing processing results
    """
    logger.info(f"Starting async processing for Lender ID: {lender_id}")
    
    try:
        async with TaskAsyncSession() as session:
            # Fetch lender record
            result = await session.execute(
                select(Lender).where(Lender.id == lender_id)
            )
            lender = result.scalar_one_or_none()
            
            if not lender:
                logger.error(f"Lender ID {lender_id} not found")
                return {
                    "success": False,
                    "error": "Lender not found"
                }
            
            # Update status to processing
            lender.status = LenderStatus.PROCESSING
            await session.commit()
            
            logger.info(f"Processing Lender: {lender.lender_name}")
            
            # Check if raw data exists
            if not lender.raw_data:
                logger.error(f"No raw data available for Lender ID {lender_id}")
                lender.status = LenderStatus.FAILED
                await session.commit()
                return {
                    "success": False,
                    "error": "No raw data available"
                }
            
            # Initialize LLM service
            llm_service = LLMService()
            
            # Process raw text using LLM
            logger.info("Calling LLM service for text processing...")
            processed_data = await llm_service.process_raw_text(
                raw_text=lender.raw_data,
                lender_name=lender.lender_name,
                policy_details=lender.policy_details
            )
            
            # Validate and enrich data
            enriched_data = await llm_service.validate_and_enrich_data(
                processed_data=processed_data,
                raw_text=lender.raw_data
            )
            
            # Update lender record with processed data
            lender.processed_data = enriched_data
            lender.status = LenderStatus.COMPLETED
            
            await session.commit()
            
            logger.info(
                f"Successfully completed processing for Lender ID {lender_id}. "
                f"Status: {lender.status.value}"
            )
            
            return {
                "success": True,
                "lender_id": lender_id,
                "status": lender.status.value,
                "processed_data": enriched_data
            }
            
    except Exception as e:
        logger.error(
            f"Error processing Lender ID {lender_id}: {str(e)}",
            exc_info=True
        )
        
        # Update status to failed
        try:
            async with TaskAsyncSession() as session:
                await session.execute(
                    update(Lender)
                    .where(Lender.id == lender_id)
                    .values(status=LenderStatus.FAILED)
                )
                await session.commit()
        except Exception as update_error:
            logger.error(f"Failed to update status: {str(update_error)}")
        
        return {
            "success": False,
            "error": str(e),
            "lender_id": lender_id
        }


@celery_app.task(name="process_lender_document", bind=True, max_retries=3)
def process_lender_document(self, lender_id: int) -> Dict[str, Any]:
    """
    Celery task to process a lender document.
    
    This task:
    1. Fetches the lender record with raw OCR data
    2. Processes the raw data using LLM
    3. Updates the record with processed data
    4. Updates the status accordingly
    
    Args:
        lender_id: ID of the Lender record to process
    
    Returns:
        Dict containing processing results
    """
    logger.info(f"Celery task started for Lender ID: {lender_id}")
    
    try:
        # Run async function in event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_process_lender_document_async(lender_id))
        
        logger.info(f"Celery task completed for Lender ID: {lender_id}")
        return result
        
    except Exception as e:
        logger.error(
            f"Celery task failed for Lender ID {lender_id}: {str(e)}",
            exc_info=True
        )
        
        # Retry the task if retries are available
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying task (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds
        
        return {
            "success": False,
            "error": str(e),
            "lender_id": lender_id,
            "retries_exhausted": True
        }

