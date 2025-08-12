from sqlalchemy import Column, String, Integer, Text, Index, Boolean, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class CompanySize(enum.Enum):
    """Company size enumeration"""
    SMALL_1_10 = "1-10"
    SMALL_11_50 = "11-50"
    MEDIUM_51_200 = "51-200"
    MEDIUM_201_500 = "201-500"
    LARGE_501_1000 = "501-1000"
    LARGE_1000_PLUS = "1000+"

class Domain(enum.Enum):
    """Domain enumeration"""
    IT = "IT"
    HEALTHCARE = "Healthcare"
    FINANCE = "Finance"
    EDUCATION = "Education"
    MANUFACTURING = "Manufacturing"
    RETAIL = "Retail"
    CONSULTING = "Consulting"
    MEDIA = "Media"
    REAL_ESTATE = "Real Estate"
    TRANSPORTATION = "Transportation"
    ENERGY = "Energy"
    TELECOMMUNICATIONS = "Telecommunications"
    OTHER = "Other"

class Recruiter(BaseModel):
    """Recruiter model with role-based access control"""
    __tablename__ = "recruiters"
    
    # Add composite indexes for better query performance
    __table_args__ = (
        Index('idx_recruiter_domain_company_size', 'domain', 'company_size'),
        Index('idx_recruiter_role', 'role'),
        Index('idx_recruiter_email', 'email'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Account Info
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone_number = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    
    # Company Info
    company_name = Column(String(255), nullable=False, index=True)
    domain = Column(String(50), nullable=False, index=True)
    company_size = Column(String(20), nullable=False, index=True)
    company_description = Column(Text, nullable=True)
    
    # System fields
    role = Column(String(20), nullable=False, default="recruiter", index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    email_verified = Column(Boolean, nullable=False, default=False, index=True)
    
    # Relationships
    # jobs = relationship("Job", back_populates="recruiter", cascade="all, delete-orphan")  # Commented out since recruiter_id is commented
    # applications relationship removed - no longer needed since recruiter_id was removed from applications
    # interactions relationship removed - InteractionLog uses generic user_id approach 