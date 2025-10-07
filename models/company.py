from sqlalchemy import Column, String, Integer, Text, Index, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class Company(BaseModel):
    """Company model for multi-tenancy support"""
    __tablename__ = "companies"
    
    # Add composite indexes for better query performance
    __table_args__ = (
        Index('idx_company_name', 'name'),
        Index('idx_company_domain', 'domain'),
        Index('idx_company_is_active', 'is_active'),
        Index('idx_company_created_at', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Company Information
    name = Column(String(255), nullable=False, unique=True, index=True)
    domain = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Company Settings
    max_recruiters = Column(Integer, nullable=False, default=10)  # Maximum recruiters allowed
    max_jobs = Column(Integer, nullable=False, default=100)  # Maximum active jobs allowed
    
    # Contact Information
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    
    # System fields
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)  # PENDING, ACTIVE, REJECTED, SUSPENDED
    subscription_plan = Column(String(50), nullable=False, default="basic")  # basic, premium, enterprise
    
    # Relationships
    recruiters = relationship("Recruiter", back_populates="company", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")



