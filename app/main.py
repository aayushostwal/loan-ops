# app/main.py
import logging
from fastapi import FastAPI
from app.routers import lender_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Kaaj - Lender Management System",
    description="API for managing lender documents with OCR and LLM processing",
    version="1.0.0"
)

# Include routers
app.include_router(lender_routes.router)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}
