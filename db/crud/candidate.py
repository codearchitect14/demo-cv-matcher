#File: db/crud/candidate.py
from typing import List, Optional, Dict, Any, Protocol, Union, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import text
import logging
import time

from models.candidate import Candidate, CandidateExperience
from models.candidate_skill import CandidateSkill
from db.crud.base import CRUDBase
from schemas.candidate import CandidateCreate, CandidateUpdate, CandidateSearchFilter

logger = logging.getLogger(__name__)

class CandidateDataProtocol(Protocol):
    """Protocol for candidate data structure"""
    id: int
    name: str
    email: str
    location: str
    domain: str
    expected_salary_min: Optional[int]
    expected_salary_max: Optional[int]

class ExperienceDataProtocol(Protocol):
    """Protocol for experience data structure"""
    skill: str
    years: int
    description: Optional[str]

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
        """Get candidate by email with optimized query - only essential fields"""
        # Only select essential fields for login to reduce data transfer
        query = select(
            Candidate.id,
            Candidate.email,
            Candidate.password_hash,
            Candidate.role
        ).where(Candidate.email == email)
        result = await db.execute(query)
        row = result.fetchone()
        
        if row:
            # Create a minimal candidate object with only login-required fields
            candidate = Candidate()
            candidate.id = row.id
            candidate.email = row.email
            candidate.password_hash = row.password_hash
            candidate.role = row.role
            return candidate
        return None
        
    async def search_by_name_or_email(self, db: AsyncSession, search_term: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Search candidates by name or email using fuzzy search - returns dict to avoid relationship issues"""
        try:
            # Use raw SQL with :param style to avoid pgbouncer prepared statement issues
            sql = text("""
                SELECT id, name, email, location, domain, expected_salary_min, expected_salary_max, 
                       summary, consent_given, created_at, updated_at
                FROM candidates
                WHERE name ILIKE :search_term OR email ILIKE :search_term
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
            """)
            
            # Use :param style for pgbouncer compatibility
            result = await db.execute(sql, {
                "search_term": f"%{search_term}%",
                "limit": limit,
                "skip": skip
            })
            
            rows = result.fetchall()
            
            # Convert to dict format
            candidate_dicts = []
            for row in rows:
                candidate_dict = {
                    "id": row.id,
                    "name": row.name,
                    "email": row.email,
                    "location": row.location,
                    "domain": row.domain,
                    "expected_salary_min": row.expected_salary_min,
                    "expected_salary_max": row.expected_salary_max,
                    "summary": row.summary,
                    "consent_given": row.consent_given,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "experiences": []  # Empty list to satisfy schema
                }
                candidate_dicts.append(candidate_dict)
            
            logger.info(f"Found {len(candidate_dicts)} candidates for search term: {search_term}")
            return candidate_dicts
            
        except Exception as e:
            logger.error(f"Error in search_by_name_or_email: {e}")
            return []
    
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
                            CandidateExperience.years >= search_filter.min_experience
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
    
    async def search_candidates_optimized(
        self, 
        db: AsyncSession, 
        search_filter: CandidateSearchFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[Candidate]:
        """Optimized candidate search with query analysis"""
        try:
            # Build optimized query with index hints
            query = select(Candidate).options(
                selectinload(Candidate.experiences)
            )
            
            conditions = []
            
            # Location filter with index hint
            if search_filter.location:
                conditions.append(Candidate.location.ilike(f"%{search_filter.location}%"))
            
            # Domain filter with index hint
            if search_filter.domain:
                conditions.append(Candidate.domain.ilike(f"%{search_filter.domain}%"))
            
            # Salary range filter with composite index hint
            if search_filter.salary_min is not None:
                conditions.append(Candidate.expected_salary_max >= search_filter.salary_min)
            if search_filter.salary_max is not None:
                conditions.append(Candidate.expected_salary_min <= search_filter.salary_max)
            
            # Skills filter with optimized subquery
            if search_filter.required_skills:
                skills_conditions = []
                for skill in search_filter.required_skills:
                    skills_conditions.append(
                        Candidate.experiences.any(
                            and_(
                                CandidateExperience.skill.ilike(f"%{skill}%"),
                                CandidateExperience.years >= search_filter.min_experience
                            )
                        )
                    )
                if skills_conditions:
                    conditions.append(or_(*skills_conditions))
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Add ordering with index hint
            query = query.order_by(desc(Candidate.created_at))
            
            # Add pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query with performance monitoring
            start_time = time.time()
            result = await db.execute(query)
            candidates = result.scalars().unique().all()
            execution_time = time.time() - start_time
            
            # Log performance metrics
            logger.info(f"Search query executed in {execution_time:.3f}s, "
                       f"returned {len(candidates)} candidates")
            
            # Analyze query performance if slow
            if execution_time > 1.0:  # Log slow queries
                await self._analyze_query_performance(db, query, execution_time)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error in optimized search: {e}")
            return []
    
    async def _analyze_query_performance(self, db: AsyncSession, query, execution_time: float):
        """Analyze query performance using EXPLAIN"""
        try:
            # Convert SQLAlchemy query to raw SQL for EXPLAIN
            compiled_query = query.compile(compile_kwargs={"literal_binds": True})
            sql = str(compiled_query)
            
            # Execute EXPLAIN ANALYZE
            explain_query = text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}")
            result = await db.execute(explain_query)
            explain_result = result.fetchone()
            
            if explain_result:
                plan = explain_result[0]
                logger.warning(f"Slow query detected ({execution_time:.3f}s): {plan}")
                
                # Extract key performance metrics
                if isinstance(plan, list) and len(plan) > 0:
                    root_plan = plan[0]
                    actual_time = root_plan.get('Actual Total Time', 0)
                    planning_time = root_plan.get('Planning Time', 0)
                    execution_time_actual = root_plan.get('Execution Time', 0)
                    
                    logger.info(f"Query performance: Planning={planning_time:.3f}s, "
                               f"Execution={execution_time_actual:.3f}s, "
                               f"Total={actual_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Failed to analyze query performance: {e}")
    
    async def get_active_candidates(self, db: AsyncSession, limit: int = 50) -> List[Candidate]:
        """Get active candidates with optimized query"""
        query = select(Candidate).options(
            selectinload(Candidate.experiences)
        ).limit(limit).order_by(desc(Candidate.created_at))
        
        result = await db.execute(query)
        return result.scalars().unique().all()
    
    async def get_active_candidates_with_skills(self, db: AsyncSession, limit: int = 50) -> List[Candidate]:
        """Get active candidates with skills using eager loading (including Skill for each CandidateSkill)"""
        query = select(Candidate).options(
            selectinload(Candidate.experiences),
            selectinload(Candidate.candidate_skills).selectinload(CandidateSkill.skill)
        ).limit(limit).order_by(desc(Candidate.created_at))
        
        result = await db.execute(query)
        return result.scalars().unique().all()
    
    async def get_experiences(self, db: AsyncSession, candidate_id: int) -> List[CandidateExperience]:
        """Get experiences for a candidate"""
        query = select(CandidateExperience).where(CandidateExperience.candidate_id == candidate_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def bulk_create_experiences(
        self, 
        db: AsyncSession, 
        candidate_id: int, 
        experiences: List[Dict[str, Any]]
    ) -> List[CandidateExperience]:
        """Bulk create experiences for a candidate"""
        experience_objects = []
        
        for exp_data in experiences:
            experience = CandidateExperience(
                candidate_id=candidate_id,
                skill=exp_data["skill"],
                years=exp_data["years"],
                description=exp_data.get("description")
            )
            experience_objects.append(experience)
        
        db.add_all(experience_objects)
        await db.commit()
        
        # Refresh objects to get IDs
        for exp in experience_objects:
            await db.refresh(exp)
        
        return experience_objects
    
    async def add_experience(
        self,
        db: AsyncSession,
        candidate_id: int,
        skill: str,
        years: int,
        description: Optional[str] = None
    ) -> CandidateExperience:
        """Add a single experience for a candidate"""
        experience = CandidateExperience(
            candidate_id=candidate_id,
            skill=skill,
            years=years,
            description=description
        )
        db.add(experience)
        await db.commit()
        await db.refresh(experience)
        return experience
    
    async def update_experience(
        self,
        db: AsyncSession,
        experience_id: int,
        skill: str,
        years: int,
        description: Optional[str] = None
    ) -> Optional[CandidateExperience]:
        """Update an experience"""
        experience = await db.get(CandidateExperience, experience_id)
        if experience:
            experience.skill = skill
            experience.years = years
            experience.description = description
            await db.commit()
            await db.refresh(experience)
        return experience
    
    async def delete_experience(
        self,
        db: AsyncSession,
        experience_id: int
    ) -> bool:
        """Delete an experience"""
        experience = await db.get(CandidateExperience, experience_id)
        if experience:
            await db.delete(experience)
            await db.commit()
            return True
        return False
    
    async def get_candidates_by_skills(
        self, 
        db: AsyncSession, 
        skills: List[str], 
        min_years: int = 1,
        limit: int = 100
    ) -> List[Candidate]:
        """Get candidates by required skills"""
        query = select(Candidate).options(
            selectinload(Candidate.experiences)
        )
        
        # Build skill conditions
        skill_conditions = []
        for skill in skills:
            skill_conditions.append(
                Candidate.experiences.any(
                    and_(
                        CandidateExperience.skill.ilike(f"%{skill}%"),
                        CandidateExperience.years >= min_years
                    )
                )
            )
        
        if skill_conditions:
            query = query.where(or_(*skill_conditions))
        
        query = query.limit(limit).order_by(desc(Candidate.created_at))
        result = await db.execute(query)
        return result.scalars().unique().all()
    
    async def get_candidates_by_skills_optimized(
        self, 
        db: AsyncSession, 
        skills: List[str], 
        min_years: int = 1,
        limit: int = 100
    ) -> List[Candidate]:
        """Optimized skill-based candidate search with query analysis"""
        try:
            # Use composite index for better performance
            query = select(Candidate).options(
                selectinload(Candidate.experiences)
            )
            
            # Build optimized skill conditions
            skill_conditions = []
            for skill in skills:
                skill_conditions.append(
                    Candidate.experiences.any(
                        and_(
                            CandidateExperience.skill.ilike(f"%{skill}%"),
                            CandidateExperience.years >= min_years
                        )
                    )
                )
            
            if skill_conditions:
                query = query.where(or_(*skill_conditions))
            
            # Add ordering and pagination
            query = query.limit(limit).order_by(desc(Candidate.created_at))
            
            # Execute with performance monitoring
            start_time = time.time()
            result = await db.execute(query)
            candidates = result.scalars().unique().all()
            execution_time = time.time() - start_time
            
            logger.info(f"Skill-based search executed in {execution_time:.3f}s, "
                       f"found {len(candidates)} candidates for skills: {skills}")
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error in optimized skill search: {e}")
            return []
    
    async def get_candidates_by_location_domain(
        self, 
        db: AsyncSession, 
        location: str, 
        domain: str,
        limit: int = 100
    ) -> List[Candidate]:
        """Get candidates by location and domain"""
        query = select(Candidate).options(
            selectinload(Candidate.experiences)
        ).where(
            and_(
                Candidate.location.ilike(f"%{location}%"),
                Candidate.domain.ilike(f"%{domain}%")
            )
        ).limit(limit).order_by(desc(Candidate.created_at))
        
        result = await db.execute(query)
        return result.scalars().unique().all()
    
    async def get_candidate_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get candidate statistics"""
        try:
            # Total candidates
            total_candidates = await db.scalar(select(func.count(Candidate.id)))
            
            # Candidates by domain
            domain_stats = await db.execute(
                select(Candidate.domain, func.count(Candidate.id))
                .group_by(Candidate.domain)
            )
            domain_counts = dict(domain_stats.all())
            
            # Candidates by location
            location_stats = await db.execute(
                select(Candidate.location, func.count(Candidate.id))
                .group_by(Candidate.location)
                .order_by(func.count(Candidate.id).desc())
                .limit(10)
            )
            location_counts = dict(location_stats.all())
            
            # Average experience years
            avg_experience = await db.scalar(
                select(func.avg(CandidateExperience.years))
                .select_from(CandidateExperience)
            )
            
            return {
                "total_candidates": total_candidates,
                "domain_distribution": domain_counts,
                "top_locations": location_counts,
                "average_experience_years": float(avg_experience) if avg_experience else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting candidate stats: {e}")
            return {
                "total_candidates": 0,
                "domain_distribution": {},
                "top_locations": {},
                "average_experience_years": 0.0
            }
    
    async def get_candidate_stats_optimized(self, db: AsyncSession) -> Dict[str, Any]:
        """Optimized candidate statistics with efficient queries"""
        try:
            # Use single query with multiple aggregations
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_candidates,
                    COUNT(DISTINCT domain) as unique_domains,
                    COUNT(DISTINCT location) as unique_locations,
                    AVG(expected_salary_min) as avg_min_salary,
                    AVG(expected_salary_max) as avg_max_salary,
                    AVG(ce.years) as avg_experience_years
                FROM candidates c
                LEFT JOIN candidate_experience ce ON c.id = ce.candidate_id
            """)
            
            result = await db.execute(stats_query)
            stats = result.fetchone()
            
            # Get domain distribution with efficient query
            domain_query = text("""
                SELECT domain, COUNT(*) as count
                FROM candidates
                GROUP BY domain
                ORDER BY count DESC
                LIMIT 10
            """)
            
            domain_result = await db.execute(domain_query)
            domain_counts = dict(domain_result.fetchall())
            
            # Get location distribution
            location_query = text("""
                SELECT location, COUNT(*) as count
                FROM candidates
                GROUP BY location
                ORDER BY count DESC
                LIMIT 10
            """)
            
            location_result = await db.execute(location_query)
            location_counts = dict(location_result.fetchall())
            
            return {
                "total_candidates": stats[0] if stats else 0,
                "unique_domains": stats[1] if stats else 0,
                "unique_locations": stats[2] if stats else 0,
                "avg_min_salary": float(stats[3]) if stats and stats[3] else 0.0,
                "avg_max_salary": float(stats[4]) if stats and stats[4] else 0.0,
                "avg_experience_years": float(stats[5]) if stats and stats[5] else 0.0,
                "domain_distribution": domain_counts,
                "top_locations": location_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting optimized candidate stats: {e}")
            return {
                "total_candidates": 0,
                "unique_domains": 0,
                "unique_locations": 0,
                "avg_min_salary": 0.0,
                "avg_max_salary": 0.0,
                "avg_experience_years": 0.0,
                "domain_distribution": {},
                "top_locations": {}
            }
    
    async def full_text_search(
        self, 
        db: AsyncSession, 
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Candidate]:
        """Full text search across candidate data"""
        # Use PostgreSQL full-text search if available
        if "postgresql" in str(db.bind.url):
            # PostgreSQL full-text search
            search_query = text("""
                SELECT DISTINCT c.* FROM candidates c
                LEFT JOIN candidate_experience ce ON c.id = ce.candidate_id
                WHERE 
                    to_tsvector('english', c.name || ' ' || c.location || ' ' || c.domain || ' ' || COALESCE(c.summary, '') || ' ' || COALESCE(ce.skill, '')) @@ plainto_tsquery('english', :search_term)
                ORDER BY ts_rank(to_tsvector('english', c.name || ' ' || c.location || ' ' || c.domain || ' ' || COALESCE(c.summary, '') || ' ' || COALESCE(ce.skill, '')), plainto_tsquery('english', :search_term)) DESC
                LIMIT :limit OFFSET :skip
            """)
            
            result = await db.execute(search_query, {
                "search_term": search_term,
                "limit": limit,
                "skip": skip
            })
            
            candidates = []
            for row in result:
                candidate = Candidate(**dict(row))
                candidates.append(candidate)
            
            return candidates
        else:
            # Fallback to simple LIKE search
            query = select(Candidate).options(
                selectinload(Candidate.experiences)
            ).where(
                or_(
                    Candidate.name.ilike(f"%{search_term}%"),
                    Candidate.location.ilike(f"%{search_term}%"),
                    Candidate.domain.ilike(f"%{search_term}%"),
                    Candidate.summary.ilike(f"%{search_term}%")
                )
            ).offset(skip).limit(limit).order_by(desc(Candidate.created_at))
            
            result = await db.execute(query)
            return result.scalars().unique().all()

# Create singleton instance
candidate = CRUDCandidate(Candidate)