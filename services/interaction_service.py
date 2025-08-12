from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import logging

from models.interaction import InteractionLog
from models.application import Application
from models.candidate import Candidate
from models.job import Job
from db.crud.interaction import interaction as interaction_crud
from db.crud.application import application as application_crud

logger = logging.getLogger(__name__)

class InteractionType:
    """Interaction types for tracking user behavior"""
    VIEW = "viewed"
    APPLIED = "applied"
    REJECTED = "rejected"
    ACCEPT = "accepted"
    SAVE = "saved"
    SHARE = "shared"

class InteractionService:
    """Service for tracking and analyzing user interactions for personalization"""
    
    def __init__(self):
        """Initialize interaction service"""
        pass
    
    async def log_interaction(
        self,
        db: AsyncSession,
        candidate_id: int,
        job_id: int,
        interaction_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InteractionLog:
        """
        Log a candidate interaction with a job
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            job_id: Job ID
            interaction_type: Type of interaction (view, apply, reject, etc.)
            metadata: Additional interaction data
            
        Returns:
            Created interaction log entry
        """
        try:
            interaction = InteractionLog(
                user_id=candidate_id,  # Changed from candidate_id to user_id
                job_id=job_id,
                interaction_type=interaction_type
            )
            
            db.add(interaction)
            await db.commit()
            await db.refresh(interaction)
            
            logger.info(f"Logged {interaction_type} interaction: Candidate {candidate_id} -> Job {job_id}")
            return interaction
            
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            await db.rollback()
            raise
    
    async def log_application(
        self,
        db: AsyncSession,
        candidate_id: int,
        job_id: int,
        status: str = "applied",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Application:
        """
        Log a job application and related interaction
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            job_id: Job ID
            status: Application status
            metadata: Additional application data
            
        Returns:
            Created application record
        """
        try:
            # Create application record
            application = Application(
                candidate_id=candidate_id,
                job_id=job_id,
                status=status,
            )
            
            db.add(application)
            await db.commit()
            await db.refresh(application)
            
            # Log interaction
            await self.log_interaction(
                db=db,
                candidate_id=candidate_id,
                job_id=job_id,
                interaction_type=InteractionType.APPLIED
            )
            
            logger.info(f"Logged application: Candidate {candidate_id} -> Job {job_id} ({status})")
            return application
            
        except Exception as e:
            logger.error(f"Failed to log application: {e}")
            await db.rollback()
            raise
    
    async def get_user_interactions(
        self,
        db: AsyncSession,
        candidate_id: int,
        days_back: int = 30,
        interaction_types: Optional[List[str]] = None
    ) -> List[InteractionLog]:
        """
        Get candidate interactions for personalization analysis
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            days_back: Number of days to look back
            interaction_types: Filter by specific interaction types
            
        Returns:
            List of candidate interactions
        """
        try:
            query = select(InteractionLog).where(
                InteractionLog.user_id == candidate_id,  # Changed from candidate_id to user_id
                InteractionLog.created_at >= datetime.utcnow() - timedelta(days=days_back)
            )
            
            if interaction_types:
                query = query.where(InteractionLog.interaction_type.in_(interaction_types))
            
            query = query.order_by(InteractionLog.created_at.desc())
            
            result = await db.execute(query)
            interactions = result.scalars().all()
            
            logger.info(f"Retrieved {len(interactions)} interactions for candidate {candidate_id}")
            return interactions
            
        except Exception as e:
            logger.error(f"Failed to get candidate interactions: {e}")
            return []
    
    async def get_user_behavior_patterns(
        self,
        db: AsyncSession,
        candidate_id: int,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze user behavior patterns
        
        Args:
            db: Database session
            candidate_id: User ID
            days_back: Days to look back
            
        Returns:
            Dictionary with behavior patterns
        """
        try:
            # Get user interactions
            interactions = await self.get_user_interactions(db, candidate_id, days_back)
            
            if not interactions:
                return {
                    "total_interactions": 0,
                    "total_applications": 0,
                    "application_rate": 0.0,
                    "engagement_score": 0,
                    "preferred_domains": {},
                    "preferred_locations": {},
                    "salary_preferences": {"avg": 0},
                    "interaction_types": {}
                }
            
            # Filter applications
            applications = [i for i in interactions if i.interaction_type == "applied"]
            
            # Calculate application rate
            application_rate = len(applications) / len(interactions) if interactions else 0
            
            # Get most recent application
            most_recent_application = None
            if applications:
                most_recent_application = max(applications, key=lambda x: x.created_at)
            
            # Calculate average time between view and apply
            view_apply_times = []
            for interaction in interactions:
                if interaction.interaction_type == "applied":
                    # Find corresponding view
                    view_interaction = next(
                        (i for i in interactions 
                         if i.interaction_type == "viewed" 
                         and i.job_id == interaction.job_id
                         and i.created_at < interaction.created_at), 
                        None
                    )
                    if view_interaction:
                        time_diff = (interaction.created_at - view_interaction.created_at).total_seconds() / 3600  # hours
                        view_apply_times.append(time_diff)
            
            avg_view_to_apply_hours = sum(view_apply_times) / len(view_apply_times) if view_apply_times else 0
            
            # Count interaction types
            interaction_types = {}
            for interaction in interactions:
                interaction_types[interaction.interaction_type] = interaction_types.get(interaction.interaction_type, 0) + 1
            
            # Get job details for domain/location analysis
            job_ids = list(set([i.job_id for i in interactions]))
            domains = {}
            locations = {}
            salaries = []
            
            if job_ids:
                # Get jobs with eager loading
                result = await db.execute(
                    select(Job).options(selectinload(Job.mandatory_skills)).where(Job.id.in_(job_ids))
                )
                jobs = result.scalars().all()
                
                # Create job lookup
                job_lookup = {job.id: job for job in jobs}
                
                for interaction in interactions:
                    job = job_lookup.get(interaction.job_id)
                    if job:
                        # Domain analysis
                        domains[job.domain] = domains.get(job.domain, 0) + 1
                        locations[job.location] = locations.get(job.location, 0) + 1
                        
                        # Salary analysis (for applications only)
                        if interaction.interaction_type == "applied":
                            avg_salary = (job.salary_min + job.salary_max) / 2
                            salaries.append(avg_salary)
            
            # Calculate engagement score
            # Weight different interaction types
            weights = {
                "viewed": 1, "applied": 5, "saved": 3, "shared": 2, "rejected": -1
            }
            engagement_score = sum(
                weights.get(interaction.interaction_type, 0) 
                for interaction in interactions
            )
            
            # Calculate salary preferences
            salary_preferences = {"avg": sum(salaries) / len(salaries) if salaries else 0}
            
            patterns = {
                "total_interactions": len(interactions),
                "total_applications": len(applications),
                "application_rate": application_rate,
                "most_recent_application": most_recent_application.created_at.isoformat() if most_recent_application else None,
                "avg_view_to_apply_hours": avg_view_to_apply_hours,
                "engagement_score": engagement_score,
                "preferred_domains": domains,
                "preferred_locations": locations,
                "salary_preferences": salary_preferences,
                "interaction_types": interaction_types
            }
            
            logger.info(f"Analyzed behavior patterns for candidate {candidate_id}")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze behavior patterns: {e}")
            return {
                "total_interactions": 0,
                "total_applications": 0,
                "application_rate": 0.0,
                "engagement_score": 0,
                "preferred_domains": {},
                "preferred_locations": {},
                "salary_preferences": {"avg": 0},
                "interaction_types": {}
            }
    
    async def get_similar_users(
        self,
        db: AsyncSession,
        candidate_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find candidates with similar behavior patterns
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            limit: Number of similar candidates to return
            
        Returns:
            List of similar candidates with similarity scores
        """
        try:
            # Get target candidate patterns
            target_patterns = await self.get_user_behavior_patterns(db, candidate_id)
            
            # Get all candidates
            result = await db.execute(select(Candidate))
            candidates = result.scalars().all()
            
            similar_users = []
            
            for candidate in candidates:
                if candidate.id == candidate_id:
                    continue
                
                # Get candidate patterns
                candidate_patterns = await self.get_user_behavior_patterns(db, candidate.id)
                
                # Calculate similarity score
                similarity = self._calculate_behavior_similarity(target_patterns, candidate_patterns)
                
                if similarity > 0.3:  # Only include reasonably similar candidates
                    similar_users.append({
                        "candidate_id": candidate.id,
                        "name": candidate.name,
                        "similarity_score": similarity,
                        "patterns": candidate_patterns
                    })
            
            # Sort by similarity and return top matches
            similar_users.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar_users[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar users: {e}")
            return []
    
    def _calculate_behavior_similarity(
        self,
        patterns1: Dict[str, Any],
        patterns2: Dict[str, Any]
    ) -> float:
        """
        Calculate similarity between two behavior patterns
        
        Args:
            patterns1: First candidate's behavior patterns
            patterns2: Second candidate's behavior patterns
            
        Returns:
            Similarity score (0-1)
        """
        try:
            # Domain similarity
            domains1 = set(patterns1.get("preferred_domains", {}).keys())
            domains2 = set(patterns2.get("preferred_domains", {}).keys())
            domain_similarity = len(domains1 & domains2) / len(domains1 | domains2) if domains1 | domains2 else 0
            
            # Location similarity
            locations1 = set(patterns1.get("preferred_locations", {}).keys())
            locations2 = set(patterns2.get("preferred_locations", {}).keys())
            location_similarity = len(locations1 & locations2) / len(locations1 | locations2) if locations1 | locations2 else 0
            
            # Salary similarity
            salary1 = patterns1.get("salary_preferences", {})
            salary2 = patterns2.get("salary_preferences", {})
            
            if salary1.get("avg") and salary2.get("avg"):
                salary_diff = abs(salary1["avg"] - salary2["avg"])
                max_salary = max(salary1["avg"], salary2["avg"])
                salary_similarity = 1 - (salary_diff / max_salary) if max_salary > 0 else 0
            else:
                salary_similarity = 0
            
            # Engagement similarity
            engagement1 = patterns1.get("engagement_score", 0)
            engagement2 = patterns2.get("engagement_score", 0)
            
            if engagement1 != 0 or engagement2 != 0:
                engagement_diff = abs(engagement1 - engagement2)
                max_engagement = max(abs(engagement1), abs(engagement2))
                engagement_similarity = 1 - (engagement_diff / max_engagement) if max_engagement > 0 else 0
            else:
                engagement_similarity = 0
            
            # Weighted average
            weights = {
                "domain": 0.3,
                "location": 0.2,
                "salary": 0.3,
                "engagement": 0.2
            }
            
            total_similarity = (
                domain_similarity * weights["domain"] +
                location_similarity * weights["location"] +
                salary_similarity * weights["salary"] +
                engagement_similarity * weights["engagement"]
            )
            
            return total_similarity
            
        except Exception as e:
            logger.error(f"Failed to calculate behavior similarity: {e}")
            return 0.0

# Global instance
interaction_service = InteractionService() 