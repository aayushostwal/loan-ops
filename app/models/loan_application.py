"""
Loan Application Model

This module defines the LoanApplication model for storing loan application PDFs
and LoanMatch model for storing match results with lenders.
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base


class ApplicationStatus(enum.Enum):
    """Enumeration for Loan Application processing status"""
    UPLOADED = "uploaded"  # PDF uploaded, raw data extracted
    PROCESSING = "processing"  # Being processed against lenders
    COMPLETED = "completed"  # Processing completed successfully
    FAILED = "failed"  # Processing failed


class MatchStatus(enum.Enum):
    """Enumeration for Match processing status"""
    PENDING = "pending"  # Match calculation pending
    PROCESSING = "processing"  # Currently calculating match
    COMPLETED = "completed"  # Match score calculated
    FAILED = "failed"  # Match calculation failed


class LoanApplication(Base):
    """
    Loan Application Model
    
    Stores loan application PDF information including:
    - Raw OCR text data from application
    - Applicant information
    - Processing status
    - Metadata and audit fields
    """
    __tablename__ = "loan_applications"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Applicant Information
    applicant_name = Column(String(255), nullable=False, index=True, comment="Name of the applicant")
    applicant_email = Column(String(255), nullable=True, comment="Email of the applicant")
    applicant_phone = Column(String(50), nullable=True, comment="Phone number of the applicant")
    
    # Application Details - JSON field for structured application information
    application_details = Column(
        JSON, 
        nullable=True, 
        comment="Structured application details extracted from the document"
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
        Enum(ApplicationStatus),
        default=ApplicationStatus.UPLOADED,
        nullable=False,
        index=True,
        comment="Current processing status of the application"
    )
    
    # Hatchet Workflow ID
    workflow_run_id = Column(
        String(255),
        nullable=True,
        comment="Hatchet workflow run ID for tracking"
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
    
    # Relationship to matches
    matches = relationship("LoanMatch", back_populates="loan_application", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LoanApplication(id={self.id}, applicant='{self.applicant_name}', status='{self.status}')>"


class LoanMatch(Base):
    """
    Loan Match Model
    
    Stores match results between loan applications and lenders including:
    - Match score calculated by LLM
    - Matching criteria analysis
    - Processing status
    """
    __tablename__ = "loan_matches"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign Keys
    loan_application_id = Column(
        Integer, 
        ForeignKey("loan_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to loan application"
    )
    
    lender_id = Column(
        Integer, 
        ForeignKey("lenders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to lender"
    )
    
    # Match Score (0-100)
    match_score = Column(
        Float,
        nullable=True,
        comment="Match score between 0-100 (higher is better)"
    )
    
    # Match Analysis - JSON field containing detailed matching criteria
    match_analysis = Column(
        JSON,
        nullable=True,
        comment="Detailed analysis of matching criteria"
    )
    
    # Processing Status
    status = Column(
        Enum(MatchStatus),
        default=MatchStatus.PENDING,
        nullable=False,
        index=True,
        comment="Current processing status of the match"
    )
    
    # Error Information
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if matching failed"
    )
    
    # Audit Fields
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
    
    # Relationships
    loan_application = relationship("LoanApplication", back_populates="matches")
    lender = relationship("app.models.lender.Lender")
    
    def __repr__(self):
        return f"<LoanMatch(id={self.id}, app_id={self.loan_application_id}, lender_id={self.lender_id}, score={self.match_score})>"

