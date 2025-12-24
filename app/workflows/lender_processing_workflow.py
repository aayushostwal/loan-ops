"""
Lender Processing Workflow using Hatchet

This module defines the Hatchet workflow for processing lender documents.
"""
import logging
import os
from typing import Dict, Any
from sqlalchemy import select, update

from app.models.lender import Lender, LenderStatus
from app.services.llm_service import LLMService
from app.db import WorkflowAsyncSession

from .hatchet_config import hatchet_client
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# LLM service instance
llm_service = LLMService()

# Create workflow decorator only if hatchet_client is available
lender_processing_workflow = None
if hatchet_client:
    lender_processing_workflow = hatchet_client.workflow(name="lender-processing", on_events=["lender:document:uploaded"])
class LenderProcessingInput(BaseModel):
    lender_id: int

if lender_processing_workflow:
    @lender_processing_workflow.task()
    async def process_lender_document(input: LenderProcessingInput, ctx):
        """Process lender document with LLM"""
        return await _process_lender_document(input.lender_id)



async def _process_lender_document(lender_id):
    logger.info(f"Starting processing for Lender ID: {lender_id}")
    
    try:
        async with WorkflowAsyncSession() as db:
            # Fetch lender record
            lender = await db.get(Lender, lender_id)
            
            if not lender:
                logger.error(f"Lender ID {lender_id} not found")
                return {
                    "success": False,
                    "error": "Lender not found"
                }
            
            # Update status to processing
            lender.status = LenderStatus.PROCESSING
            await db.commit()
            
            logger.info(f"Processing Lender: {lender.lender_name}")
            
            # Check if raw data exists
            if not lender.raw_data:
                logger.error(f"No raw data available for Lender ID {lender_id}")
                lender.status = LenderStatus.FAILED
                await db.commit()
                return {
                    "success": False,
                    "error": "No raw data available"
                }
            
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
            
            await db.commit()
            
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
            async with WorkflowAsyncSession() as db:
                await db.execute(
                    update(Lender).where(Lender.id == lender_id).values(status=LenderStatus.FAILED)
                )
                await db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update status: {str(update_error)}")
        
        return {
            "success": False,
            "error": str(e),
            "lender_id": lender_id
        } 



