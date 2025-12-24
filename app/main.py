# app/main.py
import logging
from fastapi import FastAPI
from app.routers import lender_routes, loan_application_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Kaaj - Loan Management System",
    description="API for managing lender documents and loan applications with OCR, LLM processing, and parallel matching",
    version="2.0.0"
)

# Include routers
app.include_router(lender_routes.router)
app.include_router(loan_application_routes.router)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Kaaj Loan Management System",
        "version": "2.0.0",
        "endpoints": {
            "lenders": "/api/lenders",
            "loan_applications": "/api/loan-applications",
            "docs": "/docs",
            "health": "/health"
        }
    }
