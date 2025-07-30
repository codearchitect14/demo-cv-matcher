from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import logging
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from services.interaction_service import interaction_service
from services.ml_trainer_service import ml_trainer_service
from models.candidate import Candidate
from models.job import Job
from models.interaction import InteractionLog
from models.application import Application

logger = logging.getLogger(__name__)

class PersonalizationService:
    """Service for personalizing recommendations using user behavior and ML models"""
    
    def __init__(self):
        """Initialize personalization service"""
        self.interaction_service = interaction_service
        self.ml_trainer_service = ml_trainer_service
    
    async def personalize_job_recommendations(
        self,
        db: AsyncSession,
        candidate_id: int,
        job_recommendations: List[Dict[str, Any]],
        use_ml_scoring: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Personalize job recommendations for a user
        
        Args:
            db: Database session
            user_id: User ID
            job_recommendations: List of job recommendations from semantic search
            use_ml_scoring: Whether to use ML-based personalization
            
        Returns:
            List of personalized job recommendations
        """
        try:
            # Get user behavior patterns
            user_patterns = await self.interaction_service.get_user_behavior_patterns(db, candidate_id)
            
            # Get user interaction history
            user_interactions = await self.interaction_service.get_user_interactions(db, candidate_id, days_back=30)
            
            personalized_recommendations = []
            
            for job_rec in job_recommendations:
                job = job_rec["job"]
                
                # Extract features for personalization
                job_features = {
                    "job_id": job.id,
                    "domain": job.domain,
                    "location": job.location,
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "total_years_required": job.total_years_required,
                    "mandatory_skills": [skill.skill for skill in job.mandatory_skills],
                    "similarity_score": job_rec.get("similarity_score", 0),
                    "filter_score": job_rec.get("filter_score", 0),
                    "combined_score": job_rec.get("combined_score", 0)
                }
                
                # Get personalization score
                if use_ml_scoring:
                    personalization_score = await self._get_ml_personalization_score(
                        user_patterns, user_interactions, job_features
                    )
                else:
                    personalization_score = self._get_rule_based_personalization_score(
                        user_patterns, job_features
                    )
                
                # Combine scores
                final_score = self._combine_scores(
                    semantic_score=job_rec.get("similarity_score", 0),
                    filter_score=job_rec.get("filter_score", 0),
                    personalization_score=personalization_score
                )
                
                # Add personalization data to recommendation
                personalized_rec = {
                    **job_rec,
                    "personalization_score": personalization_score,
                    "final_score": final_score,
                    "personalization_reasons": self._get_personalization_reasons(
                        user_patterns, job_features, personalization_score
                    )
                }
                
                personalized_recommendations.append(personalized_rec)
            
            # Sort by final score
            personalized_recommendations.sort(key=lambda x: x["final_score"], reverse=True)
            
            logger.info(f"Personalized {len(personalized_recommendations)} job recommendations for user {candidate_id}")
            return personalized_recommendations
            
        except Exception as e:
            logger.error(f"Failed to personalize job recommendations: {e}")
            return job_recommendations
    
    async def personalize_candidate_recommendations(
        self,
        db: AsyncSession,
        job_id: int,
        candidate_recommendations: List[Dict[str, Any]],
        use_ml_scoring: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Personalize candidate recommendations for a job
        
        Args:
            db: Database session
            job_id: Job ID
            candidate_recommendations: List of candidate recommendations from semantic search
            use_ml_scoring: Whether to use ML-based personalization
            
        Returns:
            List of personalized candidate recommendations
        """
        try:
            # Get job details
            result = await db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalars().first()
            
            if not job:
                return candidate_recommendations
            
            personalized_recommendations = []
            
            for candidate_rec in candidate_recommendations:
                candidate = candidate_rec["candidate"]
                
                # Get candidate behavior patterns
                candidate_patterns = await self.interaction_service.get_user_behavior_patterns(
                    db, candidate.id
                )
                
                # Get candidate interaction history
                candidate_interactions = await self.interaction_service.get_user_interactions(
                    db, candidate.id, days_back=30
                )
                
                # Extract features for personalization
                candidate_features = {
                    "candidate_id": candidate.id,
                    "domain": candidate.domain,
                    "location": candidate.location,
                    "expected_salary_min": candidate.expected_salary_min,
                    "expected_salary_max": candidate.expected_salary_max,
                    "similarity_score": candidate_rec.get("similarity_score", 0),
                    "filter_score": candidate_rec.get("filter_score", 0),
                    "combined_score": candidate_rec.get("combined_score", 0)
                }
                
                # Get personalization score
                if use_ml_scoring:
                    personalization_score = await self._get_ml_personalization_score(
                        candidate_patterns, candidate_interactions, candidate_features
                    )
                else:
                    personalization_score = self._get_rule_based_personalization_score(
                        candidate_patterns, candidate_features
                    )
                
                # Combine scores
                final_score = self._combine_scores(
                    semantic_score=candidate_rec.get("similarity_score", 0),
                    filter_score=candidate_rec.get("filter_score", 0),
                    personalization_score=personalization_score
                )
                
                # Add personalization data to recommendation
                personalized_rec = {
                    **candidate_rec,
                    "personalization_score": personalization_score,
                    "final_score": final_score,
                    "personalization_reasons": self._get_personalization_reasons(
                        candidate_patterns, candidate_features, personalization_score
                    )
                }
                
                personalized_recommendations.append(personalized_rec)
            
            # Sort by final score
            personalized_recommendations.sort(key=lambda x: x["final_score"], reverse=True)
            
            logger.info(f"Personalized {len(personalized_recommendations)} candidate recommendations for job {job_id}")
            return personalized_recommendations
            
        except Exception as e:
            logger.error(f"Failed to personalize candidate recommendations: {e}")
            return candidate_recommendations
    
    async def _get_ml_personalization_score(
        self,
        user_patterns: Dict[str, Any],
        user_interactions: List[InteractionLog],
        item_features: Dict[str, Any]
    ) -> float:
        """
        Get ML-based personalization score
        
        Args:
            user_patterns: User behavior patterns
            user_interactions: User interaction history
            item_features: Job or candidate features
            
        Returns:
            Personalization score (0-1)
        """
        try:
            # Extract features for ML model
            features = self.ml_trainer_service.extract_training_features(
                interactions=[{
                    "job_id": item_features.get("job_id"),
                    "interaction_type": "view",
                    "timestamp": datetime.utcnow()
                }],
                user_patterns=user_patterns,
                job_features=item_features
            )
            
            # Get prediction from ML model
            score = self.ml_trainer_service.predict_score(features)
            
            return score
            
        except Exception as e:
            logger.error(f"Failed to get ML personalization score: {e}")
            return 0.5
    
    def _get_rule_based_personalization_score(
        self,
        user_patterns: Dict[str, Any],
        item_features: Dict[str, Any]
    ) -> float:
        """
        Get rule-based personalization score
        
        Args:
            user_patterns: User behavior patterns
            item_features: Job or candidate features
            
        Returns:
            Personalization score (0-1)
        """
        try:
            score = 0.5  # Base score
            
            # Domain preference
            user_domains = user_patterns.get("preferred_domains", {})
            item_domain = item_features.get("domain", "")
            if item_domain in user_domains:
                domain_weight = user_domains[item_domain] / max(sum(user_domains.values()), 1)
                score += domain_weight * 0.2
            
            # Location preference
            user_locations = user_patterns.get("preferred_locations", {})
            item_location = item_features.get("location", "")
            if item_location in user_locations:
                location_weight = user_locations[item_location] / max(sum(user_locations.values()), 1)
                score += location_weight * 0.15
            
            # Salary preference
            user_salary = user_patterns.get("salary_preferences", {})
            item_salary_min = item_features.get("salary_min") or item_features.get("expected_salary_min")
            
            if user_salary.get("avg") and item_salary_min:
                salary_diff = abs(user_salary["avg"] - item_salary_min)
                max_salary = max(user_salary["avg"], item_salary_min)
                salary_match = 1 - (salary_diff / max_salary) if max_salary > 0 else 0
                score += salary_match * 0.15
            
            # Engagement level
            engagement_score = user_patterns.get("engagement_score", 0)
            engagement_factor = min(engagement_score / 10, 1)  # Normalize engagement
            score += engagement_factor * 0.1
            
            return max(0, min(1, score))  # Clamp to [0, 1]
            
        except Exception as e:
            logger.error(f"Failed to get rule-based personalization score: {e}")
            return 0.5
    
    def _combine_scores(
        self,
        semantic_score: float,
        filter_score: float,
        personalization_score: float
    ) -> float:
        """
        Combine different scores into final recommendation score
        
        Args:
            semantic_score: Semantic similarity score
            filter_score: Business rule filter score
            personalization_score: Personalization score
            
        Returns:
            Combined final score
        """
        # Weighted combination
        weights = {
            "semantic": 0.4,
            "filter": 0.3,
            "personalization": 0.3
        }
        
        final_score = (
            semantic_score * weights["semantic"] +
            filter_score * weights["filter"] +
            personalization_score * weights["personalization"]
        )
        
        return max(0, min(1, final_score))  # Clamp to [0, 1]
    
    def _get_personalization_reasons(
        self,
        user_patterns: Dict[str, Any],
        item_features: Dict[str, Any],
        personalization_score: float
    ) -> List[str]:
        """
        Get human-readable reasons for personalization score
        
        Args:
            user_patterns: User behavior patterns
            item_features: Job or candidate features
            personalization_score: Personalization score
            
        Returns:
            List of personalization reasons
        """
        reasons = []
        
        # Domain preference
        user_domains = user_patterns.get("preferred_domains", {})
        item_domain = item_features.get("domain", "")
        if item_domain in user_domains:
            domain_count = user_domains[item_domain]
            reasons.append(f"Matches your preferred domain ({item_domain}) - {domain_count} previous applications")
        
        # Location preference
        user_locations = user_patterns.get("preferred_locations", {})
        item_location = item_features.get("location", "")
        if item_location in user_locations:
            location_count = user_locations[item_location]
            reasons.append(f"Matches your preferred location ({item_location}) - {location_count} previous applications")
        
        # Salary preference
        user_salary = user_patterns.get("salary_preferences", {})
        item_salary_min = item_features.get("salary_min") or item_features.get("expected_salary_min")
        
        if user_salary.get("avg") and item_salary_min:
            salary_diff = abs(user_salary["avg"] - item_salary_min)
            if salary_diff < user_salary["avg"] * 0.2:  # Within 20%
                reasons.append("Salary range matches your preferences")
        
        # Engagement level
        engagement_score = user_patterns.get("engagement_score", 0)
        if engagement_score > 5:
            reasons.append("Based on your high engagement with similar opportunities")
        
        # Application rate
        application_rate = user_patterns.get("application_rate", 0)
        if application_rate > 0.3:
            reasons.append("High likelihood you'll apply based on your application history")
        
        if not reasons:
            reasons.append("Personalized based on your overall behavior patterns")
        
        return reasons
    
    async def train_personalization_model(
        self,
        db: AsyncSession,
        model_type: str = "lightgbm"
    ) -> Dict[str, Any]:
        """
        Train personalization model using historical interaction data
        
        Args:
            db: Database session
            model_type: Type of model to train (lightgbm or neural_network)
            
        Returns:
            Training results
        """
        try:
            # Get historical interaction data
            training_data = await self._prepare_training_data(db)
            
            if not training_data:
                return {"error": "No training data available"}
            
            # Prepare features and labels
            X, y, feature_names = self.ml_trainer_service.prepare_training_data(training_data)
            
            if len(X) == 0:
                return {"error": "No valid training samples"}
            
            # Split data
            if SKLEARN_AVAILABLE:
                from sklearn.model_selection import train_test_split
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
            else:
                # Simple split
                split_idx = int(len(X) * 0.8)
                X_train, X_test = X[:split_idx], X[split_idx:]
                y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Train model
            if model_type == "lightgbm":
                model = self.ml_trainer_service.train_lightgbm_model(
                    X_train, y_train, X_test, y_test, feature_names
                )
            elif model_type == "neural_network":
                model = self.ml_trainer_service.train_neural_network(
                    X_train, y_train, X_test, y_test
                )
            else:
                return {"error": f"Unknown model type: {model_type}"}
            
            if model is None:
                return {"error": "Model training failed"}
            
            # Evaluate model
            metrics = self.ml_trainer_service.evaluate_model(
                model, X_test, y_test, model_type
            )
            
            # Save model
            metadata = {
                "model_type": model_type,
                "training_date": datetime.utcnow().isoformat(),
                "n_samples": len(X),
                "n_features": len(feature_names),
                "metrics": metrics
            }
            
            saved = self.ml_trainer_service.save_model(model, model_type, metadata)
            
            return {
                "success": True,
                "model_type": model_type,
                "metrics": metrics,
                "saved": saved,
                "n_samples": len(X)
            }
            
        except Exception as e:
            logger.error(f"Failed to train personalization model: {e}")
            return {"error": str(e)}
    
    async def _prepare_training_data(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Prepare training data from historical interactions
        
        Args:
            db: Database session
            
        Returns:
            List of training samples with features and labels
        """
        try:
            # Get all interactions from last 90 days
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            result = await db.execute(
                select(InteractionLog).where(
                    InteractionLog.created_at >= cutoff_date
                ).order_by(InteractionLog.created_at.desc())
            )
            interactions = result.scalars().all()
            
            training_data = []
            
            for interaction in interactions:
                # Get user patterns
                user_patterns = await self.interaction_service.get_user_behavior_patterns(
                    db, interaction.candidate_id
                )
                
                # Get job features with eager loading
                result = await db.execute(
                    select(Job).options(selectinload(Job.mandatory_skills)).where(Job.id == interaction.job_id)
                )
                job = result.scalars().first()
                
                if not job:
                    continue
                
                # Convert job to dict to avoid async issues
                job_features = {
                    "job_id": job.id,
                    "domain": job.domain,
                    "location": job.location,
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "total_years_required": job.total_years_required,
                    "mandatory_skills": [skill.skill for skill in job.mandatory_skills]
                }
                
                # Extract features
                features = self.ml_trainer_service.extract_training_features(
                    interactions=[{
                        "job_id": job.id,
                        "interaction_type": interaction.interaction_type,
                        "created_at": interaction.created_at
                    }],
                    user_patterns=user_patterns,
                    job_features=job_features
                )
                
                # Create label (1 for apply, 0 for view/reject)
                label = 1 if interaction.interaction_type == "applied" else 0
                
                training_data.append({
                    "features": features,
                    "label": label
                })
            
            return training_data
            
        except Exception as e:
            logger.error(f"Failed to prepare training data: {e}")
            return []

# Global instance
personalization_service = PersonalizationService() 