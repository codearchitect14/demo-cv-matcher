import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import json
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
from pathlib import Path

from models.interaction import InteractionLog, InteractionTypeEnum
from models.application import Application, ApplicationStatusEnum
from models.candidate import Candidate
from models.job import Job
from models.recruiter import Recruiter

logger = logging.getLogger(__name__)

@dataclass
class FeedbackData:
    """Structured feedback data"""
    user_id: int
    user_type: str  # "candidate" or "recruiter"
    job_id: Optional[int]
    candidate_id: Optional[int]
    feedback_type: str  # "positive", "negative", "neutral"
    feedback_score: float  # 0.0 to 1.0
    feedback_text: Optional[str]
    match_score: float
    interaction_type: str
    timestamp: datetime

@dataclass
class ModelPerformance:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    total_feedback: int
    positive_feedback: int
    negative_feedback: int

class FeedbackLoopService:
    """Service for collecting and using feedback to improve recommendations"""
    
    def __init__(self):
        """Initialize the feedback loop service"""
        self.feedback_model = None
        self.vectorizer = None
        self.model_path = Path("models/feedback_model.pkl")
        self.vectorizer_path = Path("models/feedback_vectorizer.pkl")
        
        # Load existing model if available
        self._load_model()
    
    async def record_feedback(
        self,
        user_id: int,
        user_type: str,
        job_id: Optional[int],
        candidate_id: Optional[int],
        feedback_type: str,
        feedback_score: float,
        feedback_text: Optional[str] = None,
        match_score: float = 0.0,
        interaction_type: str = "feedback",
        db: AsyncSession = None
    ) -> bool:
        """Record user feedback for a recommendation"""
        try:
            # Create feedback data
            feedback_data = FeedbackData(
                user_id=user_id,
                user_type=user_type,
                job_id=job_id,
                candidate_id=candidate_id,
                feedback_type=feedback_type,
                feedback_score=feedback_score,
                feedback_text=feedback_text,
                match_score=match_score,
                interaction_type=interaction_type,
                timestamp=datetime.now()
            )
            
            # Store feedback in database
            if db:
                await self._store_feedback_in_db(feedback_data, db)
            
            # Store feedback in file for model training
            await self._store_feedback_in_file(feedback_data)
            
            # Retrain model periodically
            await self._check_and_retrain_model()
            
            logger.info(f"Feedback recorded: {feedback_type} by {user_type} {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False
    
    async def get_feedback_insights(
        self, 
        user_id: Optional[int] = None,
        user_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get insights from feedback data"""
        try:
            feedback_data = await self._load_feedback_data()
            
            # Filter by parameters
            if user_id:
                feedback_data = [f for f in feedback_data if f.user_id == user_id]
            if user_type:
                feedback_data = [f for f in feedback_data if f.user_type == user_type]
            
            # Filter by time
            cutoff_date = datetime.now() - timedelta(days=days)
            feedback_data = [f for f in feedback_data if f.timestamp >= cutoff_date]
            
            # Calculate insights
            insights = {
                'total_feedback': len(feedback_data),
                'positive_feedback': len([f for f in feedback_data if f.feedback_type == 'positive']),
                'negative_feedback': len([f for f in feedback_data if f.feedback_type == 'negative']),
                'neutral_feedback': len([f for f in feedback_data if f.feedback_type == 'neutral']),
                'average_score': np.mean([f.feedback_score for f in feedback_data]) if feedback_data else 0.0,
                'feedback_trend': self._calculate_feedback_trend(feedback_data),
                'top_concerns': self._extract_top_concerns(feedback_data),
                'improvement_areas': self._identify_improvement_areas(feedback_data)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting feedback insights: {e}")
            return {}
    
    async def predict_feedback_probability(
        self, 
        match_score: float, 
        user_type: str,
        interaction_type: str,
        additional_features: Dict[str, Any] = None
    ) -> float:
        """Predict the probability of positive feedback"""
        try:
            if not self.feedback_model:
                return 0.5  # Default neutral probability
            
            # Prepare features
            features = self._prepare_features(
                match_score, user_type, interaction_type, additional_features
            )
            
            # Make prediction
            probability = self.feedback_model.predict_proba([features])[0][1]
            return float(probability)
            
        except Exception as e:
            logger.error(f"Error predicting feedback probability: {e}")
            return 0.5
    
    async def get_model_performance(self) -> ModelPerformance:
        """Get current model performance metrics"""
        try:
            # Load feedback data
            feedback_data = await self._load_feedback_data()
            
            # Calculate basic feedback counts
            total_feedback = len(feedback_data)
            positive_feedback = len([f for f in feedback_data if f.feedback_type == 'positive'])
            negative_feedback = len([f for f in feedback_data if f.feedback_type == 'negative'])
            
            # If no model or insufficient data, return basic metrics
            if not self.feedback_model or len(feedback_data) < 10:
                return ModelPerformance(
                    accuracy=0.0, precision=0.0, recall=0.0, f1_score=0.0,
                    total_feedback=total_feedback,
                    positive_feedback=positive_feedback,
                    negative_feedback=negative_feedback
                )
            
            # Prepare test data for model evaluation
            X_test, y_test = self._prepare_training_data(feedback_data)
            
            # Make predictions
            y_pred = self.feedback_model.predict(X_test)
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted')
            recall = recall_score(y_test, y_pred, average='weighted')
            f1 = f1_score(y_test, y_pred, average='weighted')
            
            return ModelPerformance(
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                total_feedback=total_feedback,
                positive_feedback=positive_feedback,
                negative_feedback=negative_feedback
            )
            
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return ModelPerformance(
                accuracy=0.0, precision=0.0, recall=0.0, f1_score=0.0,
                total_feedback=0, positive_feedback=0, negative_feedback=0
            )
    
    async def _store_feedback_in_db(self, feedback_data: FeedbackData, db: AsyncSession):
        """Store feedback in database"""
        # Create interaction log entry
        interaction = InteractionLog(
            user_id=feedback_data.user_id,
            user_type=feedback_data.user_type,
            job_id=feedback_data.job_id,
            interaction_type=InteractionTypeEnum.VIEWED,  # Use appropriate enum
            timestamp=feedback_data.timestamp
        )
        
        db.add(interaction)
        await db.commit()
    
    async def _store_feedback_in_file(self, feedback_data: FeedbackData):
        """Store feedback in JSON file for model training"""
        feedback_file = Path("data/feedback/feedback_data.json")
        feedback_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing feedback
        existing_feedback = []
        if feedback_file.exists():
            with open(feedback_file, 'r') as f:
                existing_feedback = json.load(f)
        
        # Add new feedback
        feedback_dict = {
            'user_id': feedback_data.user_id,
            'user_type': feedback_data.user_type,
            'job_id': feedback_data.job_id,
            'candidate_id': feedback_data.candidate_id,
            'feedback_type': feedback_data.feedback_type,
            'feedback_score': feedback_data.feedback_score,
            'feedback_text': feedback_data.feedback_text,
            'match_score': feedback_data.match_score,
            'interaction_type': feedback_data.interaction_type,
            'timestamp': feedback_data.timestamp.isoformat()
        }
        
        existing_feedback.append(feedback_dict)
        
        # Save updated feedback
        with open(feedback_file, 'w') as f:
            json.dump(existing_feedback, f, indent=2)
    
    async def _load_feedback_data(self) -> List[FeedbackData]:
        """Load feedback data from file"""
        feedback_file = Path("data/feedback/feedback_data.json")
        
        if not feedback_file.exists():
            return []
        
        try:
            with open(feedback_file, 'r') as f:
                feedback_list = json.load(f)
            
            feedback_data = []
            for item in feedback_list:
                feedback_data.append(FeedbackData(
                    user_id=item['user_id'],
                    user_type=item['user_type'],
                    job_id=item['job_id'],
                    candidate_id=item['candidate_id'],
                    feedback_type=item['feedback_type'],
                    feedback_score=item['feedback_score'],
                    feedback_text=item['feedback_text'],
                    match_score=item['match_score'],
                    interaction_type=item['interaction_type'],
                    timestamp=datetime.fromisoformat(item['timestamp'])
                ))
            
            return feedback_data
            
        except Exception as e:
            logger.error(f"Error loading feedback data: {e}")
            return []
    
    async def _check_and_retrain_model(self):
        """Check if model needs retraining and retrain if necessary"""
        try:
            feedback_data = await self._load_feedback_data()
            
            # Retrain if we have enough new data (e.g., 50 new feedback entries)
            if len(feedback_data) >= 50:
                await self._retrain_model(feedback_data)
                
        except Exception as e:
            logger.error(f"Error checking model retraining: {e}")
    
    async def _retrain_model(self, feedback_data: List[FeedbackData]):
        """Retrain the feedback prediction model"""
        try:
            if len(feedback_data) < 10:
                logger.warning("Not enough feedback data for training")
                return
            
            # Prepare training data
            X, y = self._prepare_training_data(feedback_data)
            
            # Initialize and train model
            self.feedback_model = LogisticRegression(random_state=42)
            self.feedback_model.fit(X, y)
            
            # Save model
            self._save_model()
            
            logger.info(f"Model retrained with {len(feedback_data)} feedback entries")
            
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
    
    def _prepare_training_data(self, feedback_data: List[FeedbackData]) -> Tuple[List[List[float]], List[int]]:
        """Prepare training data for the model"""
        X = []
        y = []
        
        for feedback in feedback_data:
            # Prepare features
            features = self._prepare_features(
                feedback.match_score,
                feedback.user_type,
                feedback.interaction_type,
                {'feedback_text': feedback.feedback_text}
            )
            
            X.append(features)
            
            # Prepare labels (1 for positive, 0 for negative/neutral)
            label = 1 if feedback.feedback_type == 'positive' else 0
            y.append(label)
        
        return X, y
    
    def _prepare_features(
        self, 
        match_score: float, 
        user_type: str, 
        interaction_type: str,
        additional_features: Dict[str, Any] = None
    ) -> List[float]:
        """Prepare features for model prediction"""
        features = []
        
        # Basic features
        features.append(match_score)
        features.append(1.0 if user_type == 'candidate' else 0.0)
        features.append(1.0 if user_type == 'recruiter' else 0.0)
        
        # Interaction type encoding
        interaction_types = ['viewed', 'applied', 'rejected', 'feedback']
        for itype in interaction_types:
            features.append(1.0 if interaction_type == itype else 0.0)
        
        # Additional features
        if additional_features:
            if 'feedback_text' in additional_features and additional_features['feedback_text']:
                # Simple text features (could be enhanced with NLP)
                text = additional_features['feedback_text'].lower()
                features.append(len(text))
                features.append(text.count('good') + text.count('great') + text.count('excellent'))
                features.append(text.count('bad') + text.count('poor') + text.count('terrible'))
            else:
                features.extend([0.0, 0.0, 0.0])
        else:
            features.extend([0.0, 0.0, 0.0])
        
        return features
    
    def _load_model(self):
        """Load trained model from file"""
        try:
            if self.model_path.exists() and self.vectorizer_path.exists():
                with open(self.model_path, 'rb') as f:
                    self.feedback_model = pickle.load(f)
                with open(self.vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                logger.info("Feedback model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load feedback model: {e}")
    
    def _save_model(self):
        """Save trained model to file"""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.feedback_model, f)
            
            logger.info("Feedback model saved successfully")
        except Exception as e:
            logger.error(f"Error saving feedback model: {e}")
    
    def _calculate_feedback_trend(self, feedback_data: List[FeedbackData]) -> str:
        """Calculate feedback trend over time"""
        if len(feedback_data) < 2:
            return "insufficient_data"
        
        # Sort by timestamp
        sorted_feedback = sorted(feedback_data, key=lambda x: x.timestamp)
        
        # Calculate trend
        recent_feedback = sorted_feedback[-10:]  # Last 10 feedback entries
        recent_positive = len([f for f in recent_feedback if f.feedback_type == 'positive'])
        recent_total = len(recent_feedback)
        
        if recent_total == 0:
            return "insufficient_data"
        
        positive_rate = recent_positive / recent_total
        
        if positive_rate > 0.7:
            return "improving"
        elif positive_rate > 0.5:
            return "stable"
        else:
            return "declining"
    
    def _extract_top_concerns(self, feedback_data: List[FeedbackData]) -> List[str]:
        """Extract top concerns from feedback text"""
        concerns = []
        
        for feedback in feedback_data:
            if feedback.feedback_text and feedback.feedback_type in ['negative', 'neutral']:
                text = feedback.feedback_text.lower()
                
                # Simple keyword extraction
                keywords = ['skill', 'experience', 'location', 'salary', 'culture', 'communication']
                for keyword in keywords:
                    if keyword in text:
                        concerns.append(keyword)
        
        # Count and return top concerns
        from collections import Counter
        concern_counts = Counter(concerns)
        return [concern for concern, count in concern_counts.most_common(5)]
    
    def _identify_improvement_areas(self, feedback_data: List[FeedbackData]) -> List[str]:
        """Identify areas for improvement based on feedback"""
        improvement_areas = []
        
        # Analyze negative feedback patterns
        negative_feedback = [f for f in feedback_data if f.feedback_type == 'negative']
        
        if not negative_feedback:
            return ["no_improvement_needed"]
        
        # Analyze match scores for negative feedback
        low_match_negative = [f for f in negative_feedback if f.match_score < 0.5]
        high_match_negative = [f for f in negative_feedback if f.match_score >= 0.5]
        
        if len(low_match_negative) > len(high_match_negative):
            improvement_areas.append("improve_matching_algorithm")
        
        # Analyze user type patterns
        candidate_negative = [f for f in negative_feedback if f.user_type == 'candidate']
        recruiter_negative = [f for f in negative_feedback if f.user_type == 'recruiter']
        
        if len(candidate_negative) > len(recruiter_negative):
            improvement_areas.append("improve_candidate_experience")
        else:
            improvement_areas.append("improve_recruiter_experience")
        
        return improvement_areas

# Create global instance
feedback_loop_service = FeedbackLoopService() 