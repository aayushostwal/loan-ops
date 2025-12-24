"""Workflows package for Hatchet integration"""

from app.workflows.lender_processing_workflow import LenderProcessingWorkflow, get_hatchet_client as get_lender_hatchet_client
from app.workflows.loan_matching_workflow import LoanMatchingWorkflow, get_hatchet_client as get_loan_hatchet_client

__all__ = [
    "LenderProcessingWorkflow",
    "LoanMatchingWorkflow",
    "get_lender_hatchet_client",
    "get_loan_hatchet_client",
]

