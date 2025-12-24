import os
import logging
from dotenv import load_dotenv
from hatchet_sdk import Hatchet

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

hatchet_client_token = os.getenv("HATCHET_CLIENT_TOKEN")
logger.info(f"HATCHET_CLIENT_TOKEN: {'SET ✓' if hatchet_client_token else 'NOT SET ✗'}")

hatchet_client = None

if hatchet_client_token:
    hatchet_client = Hatchet(debug=True)
    logger.info("Hatchet client initialized")
else:
    logger.warning("HATCHET_CLIENT_TOKEN not set. Workflows will not be registered.")