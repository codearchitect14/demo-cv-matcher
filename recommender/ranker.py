from typing import List, Dict, Any, Optional
import numpy as np
import logging

# For ML model (LightGBM or neural net)
try:
    import lightgbm as lgb
except ImportError:
    lgb = None

logger = logging.getLogger(__name__)

class FeatureEngineeringService:
    """Extracts features for candidate-job pairs for ranking"""
    
    def extract_features(self, match: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract features for a candidate-job match
        Args:
            match: Dict with keys like 'similarity_score', 'filter_score', 'candidate', 'job', 'validation', etc.
        Returns:
            Dict of feature_name: value
        """
        features = {}
        # Semantic similarity
        features['semantic_similarity'] = match.get('similarity_score', 0.0)
        # Filter score (from constraints)
        features['filter_score'] = match.get('filter_score', 0.0)
        # Combined score (if available)
        features['combined_score'] = match.get('combined_score', 0.0)
        # Salary match degree (from validation details)
        validation = match.get('validation', {})
        salary_match = validation.get('details', {}).get('salary_match', {})
        features['salary_match_score'] = salary_match.get('score', 0.0)
        # Skill match ratio (fraction of required skills met)
        skills_match = validation.get('details', {}).get('skills_match', {})
        features['skill_match_score'] = skills_match.get('score', 0.0)
        # Location match (binary or score)
        location_match = validation.get('details', {}).get('location_match', {})
        features['location_match_score'] = location_match.get('score', 0.0)
        # Domain match
        domain_match = validation.get('details', {}).get('domain_match', {})
        features['domain_match_score'] = domain_match.get('score', 0.0)
        # Experience match
        experience_match = validation.get('details', {}).get('experience_match', {})
        features['experience_match_score'] = experience_match.get('score', 0.0)
        # Past interaction features (if available)
        features['past_applies'] = match.get('past_applies', 0)
        features['past_rejections'] = match.get('past_rejections', 0)
        features['past_clicks'] = match.get('past_clicks', 0)
        return features

class RankingModelService:
    """ML-based ranking model for candidate-job matching"""
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if model_path and lgb:
            try:
                self.model = lgb.Booster(model_file=model_path)
                logger.info(f"Loaded LightGBM model from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load LightGBM model: {e}")
        else:
            logger.warning("No ML model loaded. Using fallback scoring.")
    
    def predict_score(self, features: Dict[str, float]) -> float:
        """
        Predict match score using ML model or fallback
        Args:
            features: Dict of feature_name: value
        Returns:
            Predicted match score (float)
        """
        if self.model:
            # LightGBM expects 2D array
            feature_vec = np.array([list(features.values())])
            score = float(self.model.predict(feature_vec)[0])
            return score
        else:
            # Fallback: weighted sum of key features
            score = (
                0.5 * features.get('semantic_similarity', 0) +
                0.2 * features.get('filter_score', 0) +
                0.1 * features.get('salary_match_score', 0) +
                0.1 * features.get('skill_match_score', 0) +
                0.05 * features.get('location_match_score', 0) +
                0.05 * features.get('domain_match_score', 0)
            )
            return score

class RecommendationEngine:
    """Ranks and personalizes candidate-job matches"""
    def __init__(self, model_path: Optional[str] = None):
        self.feature_service = FeatureEngineeringService()
        self.ranking_model = RankingModelService(model_path)
    
    def rank_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score and rank matches using ML model
        Args:
            matches: List of candidate-job match dicts
        Returns:
            Ranked list of matches with 'ml_score' field
        """
        for match in matches:
            features = self.feature_service.extract_features(match)
            match['ml_features'] = features
            match['ml_score'] = self.ranking_model.predict_score(features)
        # Sort by ML score descending
        matches.sort(key=lambda x: x['ml_score'], reverse=True)
        return matches

# Global instance
recommendation_engine = RecommendationEngine()
