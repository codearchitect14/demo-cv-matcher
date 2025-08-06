#File: db/crud/candidate.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import text
import logging

from models.candidate import Candidate, CandidateExperience
from db.crud.base import CRUDBase
from schemas.candidate import CandidateCreate, CandidateUpdate, CandidateSearchFilter

logger = logging.getLogger(__name__)

class CRUDCandidate(CRUDBase[Candidate, CandidateCreate, CandidateUpdate]):
    """Optimized CRUD operations for candidates with eager loading and bulk operations"""
    
    async def get_with_experiences(self, db: AsyncSession, id: int) -> Optional[Candidate]:
        """Get candidate with experiences using eager loading"""
        query = select(Candidate).options(
            selectinload(Candidate.experiences)
        ).where(Candidate.id == id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Candidate]:
        """Get candidate by email with optimized query"""
        query = select(Candidate).where(Candidate.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_multi_with_experiences(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Candidate]:
        """Get multiple candidates with experiences using eager loading"""
        query = select(Candidate).options(
            selectinload(Candidate.experiences)
        )
        
        # Apply filters if provided
        if filters:
            conditions = []
            if filters.get("location"):
                conditions.append(Candidate.location.ilike(f"%{filters['location']}%"))
            if filters.get("domain"):
                conditions.append(Candidate.domain.ilike(f"%{filters['domain']}%"))
            if filters.get("role"):
                conditions.append(Candidate.role == filters["role"])
            if filters.get("salary_min"):
                conditions.append(Candidate.expected_salary_min >= filters["salary_min"])
            if filters.get("salary_max"):
                conditions.append(Candidate.expected_salary_max <= filters["salary_max"])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        query = query.offset(skip).limit(limit).order_by(desc(Candidate.created_at))
        result = await db.execute(query)
        return result.scalars().unique().all()
    
    async def search_candidates(
        self, 
        db: AsyncSession, 
        search_filter: CandidateSearchFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[Candidate]:
        """Advanced candidate search with optimized queries"""
        query = select(Candidate).options(
            selectinload(Candidate.experiences)
        )
        
        conditions = []
        
        # Location filter
        if search_filter.location:
            conditions.append(Candidate.location.ilike(f"%{search_filter.location}%"))
        
        # Domain filter
        if search_filter.domain:
            conditions.append(Candidate.domain.ilike(f"%{search_filter.domain}%"))
        
        # Salary range filter
        if search_filter.salary_min is not None:
            conditions.append(Candidate.expected_salary_max >= search_filter.salary_min)
        if search_filter.salary_max is not None:
            conditions.append(Candidate.expected_salary_min <= search_filter.salary_max)
        
        # Skills filter (requires subquery)
        if search_filter.required_skills:
            skills_conditions = []
            for skill in search_filter.required_skills:
                skills_conditions.append(
                    Candidate.experiences.any(
                        and_(
                            CandidateExperience.skill.ilike(f"%{skill}%"),
                            CandidateExperience.years >= 1
                        )
                    )
                )
            if skills_conditions:
                conditions.append(or_(*skills_conditions))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.offset(skip).limit(limit).order_by(desc(Candidate.created_at))
        result = await db.execute(query)
        return result.scalars().unique().all()
    
    async def get_active_candidates(self, db: AsyncSession, limit: int = 50) -> List[Candidate]:
        """Get candidates with experiences"""
        query = select(Candidate).options(
            selectinload(Candidate.experiences)
        ).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().unique().all()

    async def get_experiences(self, db: AsyncSession, candidate_id: int) -> List[CandidateExperience]:
        """Get candidate experiences with optimized query"""
        query = select(CandidateExperience).where(
            CandidateExperience.candidate_id == candidate_id
        ).order_by(desc(CandidateExperience.years))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def bulk_create_experiences(
        self, 
        db: AsyncSession, 
        candidate_id: int, 
        experiences: List[Dict[str, Any]]
    ) -> List[CandidateExperience]:
        """Bulk create candidate experiences for better performance"""
        experience_objects = [
            CandidateExperience(
                candidate_id=candidate_id,
                skill=exp["skill"],
                years=exp["years"],
                description=exp.get("description")
            )
            for exp in experiences
        ]
        
        db.add_all(experience_objects)
        await db.commit()
        
        # Refresh all objects to get their IDs
        for obj in experience_objects:
            await db.refresh(obj)
        
        return experience_objects
    
    async def get_candidates_by_skills(
        self, 
        db: AsyncSession, 
        skills: List[str], 
        min_years: int = 1,
        limit: int = 100
    ) -> List[Candidate]:
        """Get candidates by required skills with optimized query"""
        query = select(Candidate).options(
            selectinload(Candidate.experiences)
        ).where(
            Candidate.experiences.any(
                and_(
                    CandidateExperience.skill.in_(skills),
                    CandidateExperience.years >= min_years
                )
            )
        ).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().unique().all()
    
    async def get_candidates_by_location_domain(
        self, 
        db: AsyncSession, 
        location: str, 
        domain: str,
        limit: int = 100
    ) -> List[Candidate]:
        """Get candidates by location and domain with optimized query"""
        query = select(Candidate).options(
            selectinload(Candidate.experiences)
        ).where(
            and_(
                Candidate.location.ilike(f"%{location}%"),
                Candidate.domain.ilike(f"%{domain}%")
            )
        ).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().unique().all()
    
    async def get_candidate_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get candidate statistics with optimized queries"""
        # Total candidates
        total_query = select(func.count(Candidate.id))
        total_result = await db.execute(total_query)
        total_candidates = total_result.scalar()
        
        # Candidates by domain
        domain_query = select(
            Candidate.domain,
            func.count(Candidate.id).label('count')
        ).group_by(Candidate.domain).order_by(desc('count'))
        domain_result = await db.execute(domain_query)
        domain_stats = domain_result.all()
        
        # Candidates by location
        location_query = select(
            Candidate.location,
            func.count(Candidate.id).label('count')
        ).group_by(Candidate.location).order_by(desc('count')).limit(10)
        location_result = await db.execute(location_query)
        location_stats = location_result.all()
        
        # Average salary expectations
        salary_query = select(
            func.avg(Candidate.expected_salary_min).label('avg_min'),
            func.avg(Candidate.expected_salary_max).label('avg_max')
        )
        salary_result = await db.execute(salary_query)
        salary_stats = salary_result.first()
        
        return {
            "total_candidates": total_candidates,
            "domain_distribution": [{"domain": d.domain, "count": d.count} for d in domain_stats],
            "location_distribution": [{"location": l.location, "count": l.count} for l in location_stats],
            "salary_stats": {
                "avg_min_salary": float(salary_stats.avg_min) if salary_stats.avg_min else 0,
                "avg_max_salary": float(salary_stats.avg_max) if salary_stats.avg_max else 0
            }
        }
    
    async def full_text_search(
        self, 
        db: AsyncSession, 
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Candidate]:
        """Full-text search for candidates using PostgreSQL text search"""
        # Create text search vector
        search_vector = func.to_tsvector('english', 
            Candidate.name + ' ' + 
            func.coalesce(Candidate.summary, '') + ' ' +
            func.coalesce(Candidate.location, '') + ' ' +
            func.coalesce(Candidate.domain, '')
        )
        
        # Create search query
        search_query = func.plainto_tsquery('english', search_term)
        
        # Calculate relevance score
        relevance = func.ts_rank(search_vector, search_query)
        
        query = select(Candidate).options(
            selectinload(Candidate.experiences)
        ).where(
            search_vector.op('@@')(search_query)
        ).order_by(desc(relevance)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().unique().all()

# Create instance
candidate = CRUDCandidate(Candidate)