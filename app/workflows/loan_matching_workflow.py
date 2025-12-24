"""
Loan Matching Workflow using Hatchet

This module defines the Hatchet workflow for parallel processing of loan applications
against multiple lenders.
"""
import logging
import asyncio
from typing import Dict, Any, List
from sqlalchemy import select, update

from app.models.loan_application import LoanApplication, LoanMatch, ApplicationStatus, MatchStatus
from app.models.lender import Lender, LenderStatus
from app.services.match_service import MatchService
from app.db import WorkflowAsyncSession
from .hatchet_config import hatchet_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Match service instance
match_service = MatchService()

# Create workflow decorator only if hatchet_client is available
loan_matching_workflow = None
if hatchet_client:
    loan_matching_workflow = hatchet_client.workflow(name="loan-matching", on_events=["loan:application:uploaded"])

async def _calculate_single_match(application_id: int, lender_id: int) -> Dict[str, Any]:
    """Calculate match score for a single lender"""
    try:
        logger.info(f"Calculating match: Application {application_id} vs Lender {lender_id}")
        
        async with WorkflowAsyncSession() as db:
            # Fetch application
            application = await db.get(LoanApplication, application_id)
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            # Fetch lender
            lender = await db.get(Lender, lender_id)
            if not lender:
                raise ValueError(f"Lender {lender_id} not found")
            
            # Update match status to processing
            await db.execute(
                update(LoanMatch)
                .where(
                    LoanMatch.loan_application_id == application_id,
                    LoanMatch.lender_id == lender_id
                )
                .values(status=MatchStatus.PROCESSING)
            )
            await db.commit()
            
            # Calculate match score
            match_result = await match_service.calculate_match_score(
                application_data=application.processed_data or {},
                lender_data=lender.processed_data or {},
                lender_name=lender.lender_name,
                application_id=application_id,
                lender_id=lender_id
            )
            
            # Update match record with results
            await db.execute(
                update(LoanMatch)
                .where(
                    LoanMatch.loan_application_id == application_id,
                    LoanMatch.lender_id == lender_id
                )
                .values(
                    match_score=match_result["match_score"],
                    match_analysis=match_result["match_analysis"],
                    status=MatchStatus.COMPLETED
                )
            )
            await db.commit()
            
            logger.info(
                f"Match completed: Application {application_id} vs Lender {lender_id} "
                f"- Score: {match_result['match_score']}"
            )
            
            return {
                "success": True,
                "application_id": application_id,
                "lender_id": lender_id,
                "match_score": match_result["match_score"]
            }
            
    except Exception as e:
        logger.error(
            f"Match calculation failed for Application {application_id} "
            f"and Lender {lender_id}: {str(e)}",
            exc_info=True
        )
        
        # Update match status to failed
        try:
            async with WorkflowAsyncSession() as db:
                await db.execute(
                    update(LoanMatch)
                    .where(
                        LoanMatch.loan_application_id == application_id,
                        LoanMatch.lender_id == lender_id
                    )
                    .values(
                        status=MatchStatus.FAILED,
                        error_message=str(e)
                    )
                )
                await db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update match status: {str(update_error)}")
        
        return {
            "success": False,
            "application_id": application_id,
            "lender_id": lender_id,
            "error": str(e)
        }


# Define workflow steps
if loan_matching_workflow:
    @loan_matching_workflow.task()
    async def prepare_matching(context):
        """Step 1: Prepare matching by fetching lenders and creating match records"""
        logger.info("Step 1: Preparing matching")
        
        application_id = context.workflow_input().get("application_id")
        
        if not application_id:
            raise ValueError("application_id is required in workflow input")
        
        async with WorkflowAsyncSession() as db:
            # Fetch all active lenders
            result = await db.execute(
                select(Lender).where(Lender.status == LenderStatus.COMPLETED)
            )
            lenders = result.scalars().all()
            
            if not lenders:
                logger.warning("No active lenders found")
                return {
                    "application_id": application_id,
                    "lender_ids": [],
                    "message": "No active lenders available"
                }
            
            lender_ids = [lender.id for lender in lenders]
            
            # Create match records
            for lender_id in lender_ids:
                match = LoanMatch(
                    loan_application_id=application_id,
                    lender_id=lender_id,
                    status=MatchStatus.PENDING
                )
                db.add(match)
            
            await db.commit()
            logger.info(f"Created {len(lender_ids)} match records for application {application_id}")
            
            # Update application status to processing
            await db.execute(
                update(LoanApplication)
                .where(LoanApplication.id == application_id)
                .values(status=ApplicationStatus.PROCESSING)
            )
            await db.commit()
            
            logger.info(f"Prepared matching for {len(lender_ids)} lenders")
            
            return {
                "application_id": application_id,
                "lender_ids": lender_ids,
                "lender_count": len(lender_ids)
            }
    
    @loan_matching_workflow.task(parents=[prepare_matching])
    async def calculate_matches(context):
        """Step 2: Calculate match scores in parallel for all lenders"""
        logger.info("Step 2: Calculating matches in parallel")
        
        prepare_result = context.step_output("prepare_matching")
        application_id = prepare_result["application_id"]
        lender_ids = prepare_result["lender_ids"]
        
        if not lender_ids:
            logger.warning("No lenders to match against")
            return {
                "application_id": application_id,
                "matches": [],
                "success_count": 0,
                "failure_count": 0
            }
        
        # Calculate matches in parallel using asyncio
        logger.info(f"Starting parallel match calculation for {len(lender_ids)} lenders")
        
        tasks = [
            _calculate_single_match(application_id, lender_id)
            for lender_id in lender_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        matches = []
        success_count = 0
        failure_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Match calculation raised exception: {str(result)}")
                failure_count += 1
            elif isinstance(result, dict):
                matches.append(result)
                if result.get("success"):
                    success_count += 1
                else:
                    failure_count += 1
        
        logger.info(
            f"Parallel matching completed: {success_count} succeeded, "
            f"{failure_count} failed"
        )
        
        return {
            "application_id": application_id,
            "matches": matches,
            "success_count": success_count,
            "failure_count": failure_count,
            "total_count": len(lender_ids)
        }
    
    @loan_matching_workflow.task(parents=[calculate_matches])
    async def finalize_matching(context):
        """Step 3: Finalize matching and update application status"""
        logger.info("Step 3: Finalizing matching")
        
        match_result = context.step_output("calculate_matches")
        application_id = match_result["application_id"]
        success_count = match_result["success_count"]
        failure_count = match_result["failure_count"]
        
        # Update application status to completed
        async with WorkflowAsyncSession() as db:
            await db.execute(
                update(LoanApplication)
                .where(LoanApplication.id == application_id)
                .values(status=ApplicationStatus.COMPLETED)
            )
            await db.commit()
        
        logger.info(
            f"Matching finalized for application {application_id}. "
            f"Matches: {success_count} successful, {failure_count} failed"
        )
        
        return {
            "application_id": application_id,
            "status": "completed",
            "success_count": success_count,
            "failure_count": failure_count,
            "message": f"Matching completed with {success_count} successful matches"
        }
    
    logger.info("Loan matching workflow registered with Hatchet")
