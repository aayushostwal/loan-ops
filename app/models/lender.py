"""
Lender Model

This module defines the Lender model for storing PDF document data with OCR processing.
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON
from sqlalchemy.sql import func
from app.models import Base


class LenderStatus(enum.Enum):
    """Enumeration for Lender document processing status"""
    UPLOADED = "uploaded"  # PDF uploaded, raw data extracted
    PROCESSING = "processing"  # Being processed by async worker
    COMPLETED = "completed"  # Processing completed successfully
    FAILED = "failed"  # Processing failed


class Lender(Base):
    """
    Lender Model
    
    Stores PDF document information including:
    - Raw OCR text data
    - Processed data from LLM
    - Metadata and audit fields
    """
    __tablename__ = "lenders"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Lender Information
    lender_name = Column(String(255), nullable=False, index=True, comment="Name of the lender")
    
    # Policy Details - JSON field for structured policy information
    policy_details = Column(
        JSON, 
        nullable=True, 
        comment="Structured policy details extracted from the document"
    )
    
    # Raw Data - Stores the raw OCR extracted text from PDF
    raw_data = Column(
        Text, 
        nullable=True, 
        comment="Raw OCR text extracted from PDF document"
    )
    
    # Processed Data - JSON field containing LLM processed information
    processed_data = Column(
        JSON, 
        nullable=True, 
        comment="Processed and structured data from LLM"
    )
    
    # Processing Status
    status = Column(
        Enum(LenderStatus),
        default=LenderStatus.UPLOADED,
        nullable=False,
        index=True,
        comment="Current processing status of the document"
    )
    
    # Audit Fields
    created_by = Column(
        String(255), 
        nullable=True, 
        comment="User who created this record"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when record was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when record was last updated"
    )
    
    # Optional: Store original filename
    original_filename = Column(
        String(500),
        nullable=True,
        comment="Original PDF filename"
    )
    
    def __repr__(self):
        return f"<Lender(id={self.id}, name='{self.lender_name}', status='{self.status}')>"

