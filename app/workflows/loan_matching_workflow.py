"""
Loan Matching Workflow using Hatchet

This module defines the Hatchet workflow for parallel processing of loan applications
against multiple lenders.
"""
import logging
import asyncio
from typing import Dict, Any, List
from hatchet_sdk import Hatchet, Context
from sqlalchemy import select, update

from app.models.loan_application import LoanApplication, LoanMatch, ApplicationStatus, MatchStatus
from app.models.lender import Lender, LenderStatus
from app.services.match_service import MatchService
from app.db import WorkflowAsyncSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoanMatchingWorkflow:
    """
    Hatchet workflow for matching loan applications with lenders in parallel.
    """
    
    def __init__(self, hatchet_client: Hatchet):
        """
        Initialize the workflow.
        
        Args:
            hatchet_client: Hatchet client instance
        """
        self.hatchet = hatchet_client
        self.match_service = MatchService()
        logger.info("Loan Matching Workflow initialized")
    
    async def _get_all_active_lenders(self) -> List[Dict[str, Any]]:
        """
        Fetch all active lenders from the database.
        
        Returns:
            List of lender dictionaries with id, name, and processed_data
        """
        try:
            async with WorkflowAsyncSession() as session:
                result = await session.execute(
                    select(Lender).where(Lender.status == LenderStatus.COMPLETED)
                )
                lenders = result.scalars().all()
                
                lender_list = [
                    {
                        "id": lender.id,
                        "name": lender.lender_name,
                        "processed_data": lender.processed_data or {}
                    }
                    for lender in lenders
                ]
                
                logger.info(f"Found {len(lender_list)} active lenders")
                return lender_list
                
        except Exception as e:
            logger.error(f"Failed to fetch lenders: {str(e)}", exc_info=True)
            return []
    
    async def _create_match_records(
        self,
        application_id: int,
        lender_ids: List[int]
    ) -> None:
        """
        Create pending match records for all lenders.
        
        Args:
            application_id: ID of the loan application
            lender_ids: List of lender IDs to create matches for
        """
        try:
            async with WorkflowAsyncSession() as session:
                for lender_id in lender_ids:
                    match = LoanMatch(
                        loan_application_id=application_id,
                        lender_id=lender_id,
                        status=MatchStatus.PENDING
                    )
                    session.add(match)
                
                await session.commit()
                logger.info(f"Created {len(lender_ids)} match records for application {application_id}")
                
        except Exception as e:
            logger.error(f"Failed to create match records: {str(e)}", exc_info=True)
            raise
    
    async def _calculate_single_match(
        self,
        application_id: int,
        lender_id: int
    ) -> Dict[str, Any]:
        """
        Calculate match score for a single lender.
        
        Args:
            application_id: ID of the loan application
            lender_id: ID of the lender
        
        Returns:
            Dict containing match results
        """
        try:
            logger.info(f"Calculating match: Application {application_id} vs Lender {lender_id}")
            
            async with WorkflowAsyncSession() as session:
                # Fetch application
                app_result = await session.execute(
                    select(LoanApplication).where(LoanApplication.id == application_id)
                )
                application = app_result.scalar_one_or_none()
                
                if not application:
                    raise ValueError(f"Application {application_id} not found")
                
                # Fetch lender
                lender_result = await session.execute(
                    select(Lender).where(Lender.id == lender_id)
                )
                lender = lender_result.scalar_one_or_none()
                
                if not lender:
                    raise ValueError(f"Lender {lender_id} not found")
                
                # Update match status to processing
                await session.execute(
                    update(LoanMatch)
                    .where(
                        LoanMatch.loan_application_id == application_id,
                        LoanMatch.lender_id == lender_id
                    )
                    .values(status=MatchStatus.PROCESSING)
                )
                await session.commit()
                
                # Calculate match score
                match_result = await self.match_service.calculate_match_score(
                    application_data=application.processed_data or {},
                    lender_data=lender.processed_data or {},
                    lender_name=lender.lender_name,
                    application_id=application_id,
                    lender_id=lender_id
                )
                
                # Update match record with results
                await session.execute(
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
                await session.commit()
                
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
                async with WorkflowAsyncSession() as session:
                    await session.execute(
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
                    await session.commit()
            except Exception as update_error:
                logger.error(f"Failed to update match status: {str(update_error)}")
            
            return {
                "success": False,
                "application_id": application_id,
                "lender_id": lender_id,
                "error": str(e)
            }
    
    def register_workflow(self):
        """
        Register the workflow with Hatchet.
        """
        
        @self.hatchet.workflow(name="loan-matching", on_events=["loan:application:uploaded"])
        class LoanMatchingWorkflowDef:
            """Workflow definition for loan matching"""
            
            @self.hatchet.step(timeout="60s")
            async def prepare_matching(self, context: Context) -> Dict[str, Any]:
                """
                Step 1: Prepare matching by fetching lenders and creating match records.
                """
                logger.info("Step 1: Preparing matching")
                
                application_id = context.workflow_input().get("application_id")
                
                if not application_id:
                    raise ValueError("application_id is required in workflow input")
                
                # Fetch all active lenders
                lenders = await self._get_all_active_lenders()
                
                if not lenders:
                    logger.warning("No active lenders found")
                    return {
                        "application_id": application_id,
                        "lender_ids": [],
                        "message": "No active lenders available"
                    }
                
                lender_ids = [lender["id"] for lender in lenders]
                
                # Create match records
                await self._create_match_records(application_id, lender_ids)
                
                # Update application status to processing
                async with WorkflowAsyncSession() as session:
                    await session.execute(
                        update(LoanApplication)
                        .where(LoanApplication.id == application_id)
                        .values(status=ApplicationStatus.PROCESSING)
                    )
                    await session.commit()
                
                logger.info(f"Prepared matching for {len(lender_ids)} lenders")
                
                return {
                    "application_id": application_id,
                    "lender_ids": lender_ids,
                    "lender_count": len(lender_ids)
                }
            
            @self.hatchet.step(timeout="300s", parents=["prepare_matching"])
            async def calculate_matches(self, context: Context) -> Dict[str, Any]:
                """
                Step 2: Calculate match scores in parallel for all lenders.
                """
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
                    self._calculate_single_match(application_id, lender_id)
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
            
            @self.hatchet.step(timeout="30s", parents=["calculate_matches"])
            async def finalize_matching(self, context: Context) -> Dict[str, Any]:
                """
                Step 3: Finalize matching and update application status.
                """
                logger.info("Step 3: Finalizing matching")
                
                match_result = context.step_output("calculate_matches")
                application_id = match_result["application_id"]
                success_count = match_result["success_count"]
                failure_count = match_result["failure_count"]
                
                # Update application status to completed
                async with WorkflowAsyncSession() as session:
                    await session.execute(
                        update(LoanApplication)
                        .where(LoanApplication.id == application_id)
                        .values(status=ApplicationStatus.COMPLETED)
                    )
                    await session.commit()
                
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
        return LoanMatchingWorkflowDef


# Helper function to initialize Hatchet client
def get_hatchet_client() -> Hatchet:
    """
    Get or create Hatchet client instance.
    
    Returns:
        Hatchet client
    """
    import os
    
    hatchet_client_token = os.getenv("HATCHET_CLIENT_TOKEN")
    
    if not hatchet_client_token:
        logger.warning("HATCHET_CLIENT_TOKEN not set. Using mock mode.")
        # For development/testing without Hatchet server
        return None
    
    hatchet = Hatchet(debug=True)
    logger.info("Hatchet client initialized")
    return hatchet

