"""Models package"""
from sqlalchemy.orm import DeclarativeBase

# Define Base first to avoid circular imports
class Base(DeclarativeBase):
    pass

# Now import models that depend on Base
from app.models.lender import Lender, LenderStatus
from app.models.loan_application import LoanApplication, LoanMatch, ApplicationStatus, MatchStatus

__all__ = ["Base", "Lender", "LenderStatus", "LoanApplication", "LoanMatch", "ApplicationStatus", "MatchStatus"]

