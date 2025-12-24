"""
Hatchet Worker Script

This script initializes and starts a Hatchet worker process that handles:
- Lender document processing workflows
- Loan application matching workflows
"""
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Worker PID:%(process)d] - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def start_worker():
    from app.workflows.hatchet_config import hatchet_client
    from app.workflows.lender_processing_workflow import lender_processing_workflow
    from app.workflows.loan_matching_workflow import loan_matching_workflow

    worker = hatchet_client.worker("kaaj-worker", workflows=[lender_processing_workflow, loan_matching_workflow])
    
    worker.start()

if __name__ == "__main__":
    start_worker()