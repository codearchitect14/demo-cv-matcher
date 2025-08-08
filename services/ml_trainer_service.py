from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
import pickle
import os
from pathlib import Path
import json

# ML Libraries
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logging.warning("LightGBM not available. Using fallback scoring.")

try:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available. Using fallback scoring.")

logger = logging.getLogger(__name__)

class MLTrainerService:
    """Service for training and managing ML models for personalization"""
    
    def __init__(self, model_dir: str = "models/ml"):
        """
        Initialize ML trainer service
        
        Args:
            model_dir: Directory to store trained models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_model = None
        self.model_metadata = {}
        self.feature_scaler = None
        self.current_model_path = None
        
        # Model configuration
        self.model_config = {
            "lightgbm": {
                "objective": "binary",
                "metric": "auc",
                "boosting_type": "gbdt",
                "num_leaves": 31,
                "learning_rate": 0.05,
                "feature_fraction": 0.9,
                "bagging_fraction": 0.8,
                "bagging_freq": 5,
                "verbose": -1
            },
            "neural_network": {
                "layers": [64, 32, 16],
                "dropout": 0.2,
                "learning_rate": 0.001,
                "epochs": 100,
                "batch_size": 32
            }
        }
    
    def extract_training_features(
        self,
        interactions: List[Dict[str, Any]],
        user_patterns: Dict[str, Any],
        job_features: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Extract features for ML training from interaction data
        
        Args:
            interactions: User interaction history
            user_patterns: User behavior patterns
            job_features: Job-specific features
            
        Returns:
            Dictionary of features for ML training
        """
        features = {}
        
        # User behavior features
        features["user_total_interactions"] = user_patterns.get("total_interactions", 0)
        features["user_total_applications"] = user_patterns.get("total_applications", 0)
        features["user_application_rate"] = user_patterns.get("application_rate", 0)
        features["user_rejection_rate"] = user_patterns.get("rejection_rate", 0)
        features["user_engagement_score"] = user_patterns.get("engagement_score", 0)
        
        # Domain preferences
        user_domains = user_patterns.get("preferred_domains", {})
        job_domain = job_features.get("domain", "")
        features["domain_match_score"] = user_domains.get(job_domain, 0) / max(sum(user_domains.values()), 1)
        
        # Location preferences
        user_locations = user_patterns.get("preferred_locations", {})
        job_location = job_features.get("location", "")
        features["location_match_score"] = user_locations.get(job_location, 0) / max(sum(user_locations.values()), 1)
        
        # Salary preferences
        user_salary = user_patterns.get("salary_preferences", {})
        job_salary_min = job_features.get("salary_min", 0)
        job_salary_max = job_features.get("salary_max", 0)
        
        if user_salary.get("avg") and job_salary_min:
            salary_diff = abs(user_salary["avg"] - job_salary_min)
            max_salary = max(user_salary["avg"], job_salary_min)
            features["salary_match_score"] = 1 - (salary_diff / max_salary) if max_salary > 0 else 0
        else:
            features["salary_match_score"] = 0
        
        # Semantic features
        features["semantic_similarity"] = job_features.get("similarity_score", 0)
        features["filter_score"] = job_features.get("filter_score", 0)
        features["combined_score"] = job_features.get("combined_score", 0)
        
        # Interaction history features
        recent_interactions = [i for i in interactions if i.get("job_id") == job_features.get("job_id")]
        features["recent_views"] = len([i for i in recent_interactions if i.get("interaction_type") == "viewed"])
        features["recent_applies"] = len([i for i in recent_interactions if i.get("interaction_type") == "applied"])
        features["recent_rejections"] = len([i for i in recent_interactions if i.get("interaction_type") == "rejected"])
        
        # Time-based features
        if recent_interactions:
            latest_interaction = max(recent_interactions, key=lambda x: x.get("created_at", datetime.min))
            time_diff = (datetime.utcnow() - latest_interaction.get("created_at", datetime.utcnow())).days
            features["days_since_last_interaction"] = time_diff
        else:
            features["days_since_last_interaction"] = 999  # Large number for no interaction
        
        # Job-specific features
        features["job_total_years_required"] = job_features.get("total_years_required", 0)
        features["job_skills_count"] = len(job_features.get("mandatory_skills", []))
        
        # User skill match
        user_skills = user_patterns.get("skills", {})
        job_skills = job_features.get("mandatory_skills", [])
        skill_matches = sum(1 for skill in job_skills if skill in user_skills)
        features["skill_match_ratio"] = skill_matches / max(len(job_skills), 1)
        
        return features
    
    def prepare_training_data(
        self,
        interaction_data: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare training data from interaction history
        
        Args:
            interaction_data: List of interaction records with features and labels
            
        Returns:
            Tuple of (features, labels, feature_names)
        """
        if not interaction_data:
            return np.array([]), np.array([]), []
        
        # Extract features and labels
        features_list = []
        labels = []
        
        for record in interaction_data:
            features = record.get("features", {})
            label = record.get("label", 0)  # 1 for positive (apply), 0 for negative (view/reject)
            
            # Convert features to list in consistent order
            feature_names = sorted(features.keys())
            feature_values = [features[name] for name in feature_names]
            
            features_list.append(feature_values)
            labels.append(label)
        
        # Convert to numpy arrays
        X = np.array(features_list)
        y = np.array(labels)
        
        return X, y, feature_names
    
    def train_lightgbm_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray = None,
        y_val: np.ndarray = None,
        feature_names: List[str] = None
    ) -> Optional[Any]:
        """
        Train a LightGBM model for personalization
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            feature_names: Names of features
            
        Returns:
            Trained LightGBM model
        """
        if not LIGHTGBM_AVAILABLE:
            logger.warning("LightGBM not available. Skipping training.")
            return None
        
        try:
            # Prepare training data
            train_data = lgb.Dataset(X_train, label=y_train, feature_name=feature_names)
            
            # Prepare validation data if provided
            valid_data = None
            if X_val is not None and y_val is not None:
                valid_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            # Train model
            model = lgb.train(
                self.model_config["lightgbm"],
                train_data,
                valid_sets=[valid_data] if valid_data else None,
                valid_names=['valid'] if valid_data else None,
                num_boost_round=100,
                callbacks=[lgb.early_stopping(10) if valid_data else None]
            )
            
            logger.info("LightGBM model trained successfully")
            return model
            
        except Exception as e:
            logger.error(f"Failed to train LightGBM model: {e}")
            return None
    
    def train_neural_network(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray = None,
        y_val: np.ndarray = None
    ) -> Optional[Any]:
        """
        Train a neural network model for personalization
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            
        Returns:
            Trained neural network model
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("Scikit-learn not available. Skipping neural network training.")
            return None
        
        try:
            from sklearn.neural_network import MLPClassifier
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val) if X_val is not None else None
            
            # Train neural network
            nn_model = MLPClassifier(
                hidden_layer_sizes=self.model_config["neural_network"]["layers"],
                learning_rate_init=self.model_config["neural_network"]["learning_rate"],
                max_iter=self.model_config["neural_network"]["epochs"],
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1
            )
            
            nn_model.fit(X_train_scaled, y_train)
            
            # Store scaler for later use
            self.feature_scaler = scaler
            
            logger.info("Neural network model trained successfully")
            return nn_model
            
        except Exception as e:
            logger.error(f"Failed to train neural network: {e}")
            return None
    
    def evaluate_model(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_type: str = "lightgbm"
    ) -> Dict[str, float]:
        """
        Evaluate model performance
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            model_type: Type of model (lightgbm or neural_network)
            
        Returns:
            Dictionary of evaluation metrics
        """
        try:
            if model is None:
                return {"error": "No model provided"}
            
            # Make predictions
            if model_type == "lightgbm":
                y_pred_proba = model.predict(X_test)
            elif model_type == "neural_network":
                X_test_scaled = self.feature_scaler.transform(X_test) if self.feature_scaler else X_test
                y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            else:
                return {"error": f"Unknown model type: {model_type}"}
            
            y_pred = (y_pred_proba > 0.5).astype(int)
            
            # Calculate metrics
            metrics = {
                "auc": roc_auc_score(y_test, y_pred_proba),
                "precision": precision_recall_fscore_support(y_test, y_pred, average='binary')[0],
                "recall": precision_recall_fscore_support(y_test, y_pred, average='binary')[1],
                "f1": precision_recall_fscore_support(y_test, y_pred, average='binary')[2]
            }
            
            logger.info(f"Model evaluation completed: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to evaluate model: {e}")
            return {"error": str(e)}
    
    def save_model(
        self,
        model: Any,
        model_type: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Save trained model to disk with versioning
        
        Args:
            model: Trained model
            model_type: Type of model
            metadata: Model metadata
            
        Returns:
            True if saved successfully
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            version = metadata.get("version", "1.0.0")
            model_filename = f"{model_type}_v{version}_{timestamp}.pkl"
            model_path = self.model_dir / model_filename
            
            # Create model metadata with versioning info
            model_metadata = {
                "model_type": model_type,
                "version": version,
                "timestamp": timestamp,
                "created_at": datetime.utcnow().isoformat(),
                "model_filename": model_filename,
                "model_path": str(model_path),
                "feature_names": metadata.get("feature_names", []),
                "training_samples": metadata.get("training_samples", 0),
                "validation_samples": metadata.get("validation_samples", 0),
                "test_samples": metadata.get("test_samples", 0),
                "performance_metrics": metadata.get("performance_metrics", {}),
                "hyperparameters": metadata.get("hyperparameters", {}),
                "data_version": metadata.get("data_version", "unknown"),
                "model_size_mb": 0,  # Will be calculated after saving
                "checksum": "",  # Will be calculated after saving
                **metadata
            }
            
            # Save model with metadata
            model_data = {
                "model": model,
                "metadata": model_metadata,
                "feature_scaler": self.feature_scaler
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            # Calculate model size and checksum
            model_size = model_path.stat().st_size / (1024 * 1024)  # MB
            model_metadata["model_size_mb"] = round(model_size, 2)
            
            # Calculate checksum for integrity
            import hashlib
            with open(model_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            model_metadata["checksum"] = file_hash
            
            # Update model registry
            self._update_model_registry(model_metadata)
            
            # Update current model reference
            self.current_model = model
            self.model_metadata = model_metadata
            self.current_model_path = str(model_path)
            
            logger.info(f"Model saved to {model_path} (v{version}, {model_size:.2f}MB)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    def _update_model_registry(self, model_metadata: Dict[str, Any]):
        """Update model registry with new model information"""
        registry_path = self.model_dir / "model_registry.json"
        
        try:
            if registry_path.exists():
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
            else:
                registry = {"models": [], "current_model": None}
            
            # Add new model to registry
            registry["models"].append(model_metadata)
            
            # Keep only last 10 models to prevent registry bloat
            if len(registry["models"]) > 10:
                registry["models"] = registry["models"][-10:]
            
            # Update current model reference
            registry["current_model"] = model_metadata["model_filename"]
            
            # Save updated registry
            with open(registry_path, 'w') as f:
                json.dump(registry, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update model registry: {e}")
    
    def get_model_versions(self) -> List[Dict[str, Any]]:
        """Get list of all model versions"""
        registry_path = self.model_dir / "model_registry.json"
        
        try:
            if registry_path.exists():
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
                return registry.get("models", [])
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to get model versions: {e}")
            return []
    
    def rollback_model(self, version: str) -> bool:
        """
        Rollback to a specific model version
        
        Args:
            version: Model version to rollback to
            
        Returns:
            True if rollback successful
        """
        try:
            # Find model with specified version
            models = self.get_model_versions()
            target_model = None
            
            for model in models:
                if model.get("version") == version:
                    target_model = model
                    break
            
            if not target_model:
                logger.error(f"Model version {version} not found")
                return False
            
            # Load the target model
            model_path = self.model_dir / target_model["model_filename"]
            if not model_path.exists():
                logger.error(f"Model file {model_path} not found")
                return False
            
            # Verify checksum
            import hashlib
            with open(model_path, 'rb') as f:
                current_checksum = hashlib.md5(f.read()).hexdigest()
            
            if current_checksum != target_model["checksum"]:
                logger.error(f"Model checksum mismatch for version {version}")
                return False
            
            # Load the model
            success = self.load_model(str(model_path))
            if success:
                logger.info(f"Successfully rolled back to model version {version}")
                return True
            else:
                logger.error(f"Failed to load model version {version}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to rollback model: {e}")
            return False
    
    def get_current_model_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded model"""
        if self.model_metadata:
            return {
                "version": self.model_metadata.get("version"),
                "model_type": self.model_metadata.get("model_type"),
                "created_at": self.model_metadata.get("created_at"),
                "performance_metrics": self.model_metadata.get("performance_metrics", {}),
                "training_samples": self.model_metadata.get("training_samples", 0),
                "model_size_mb": self.model_metadata.get("model_size_mb", 0),
                "is_loaded": self.current_model is not None
            }
        else:
            return {"is_loaded": False}
    
    def load_model(self, model_path: str) -> bool:
        """
        Load trained model from disk
        
        Args:
            model_path: Path to saved model
            
        Returns:
            True if loaded successfully
        """
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.current_model = model_data["model"]
            self.model_metadata = model_data["metadata"]
            self.feature_scaler = model_data.get("feature_scaler")
            
            logger.info(f"Model loaded from {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def predict_score(
        self,
        features: Dict[str, float],
        feature_names: List[str] = None
    ) -> float:
        """
        Predict personalization score for a user-job match
        
        Args:
            features: Feature dictionary
            feature_names: Names of features in order
            
        Returns:
            Prediction score (0-1)
        """
        try:
            if self.current_model is None:
                # Fallback scoring
                return self._fallback_scoring(features)
            
            # Prepare features
            if feature_names:
                feature_values = [features.get(name, 0) for name in feature_names]
            else:
                feature_values = list(features.values())
            
            X = np.array([feature_values])
            
            # Make prediction
            if hasattr(self.current_model, 'predict'):
                # LightGBM model
                score = self.current_model.predict(X)[0]
            elif hasattr(self.current_model, 'predict_proba'):
                # Neural network model
                if self.feature_scaler:
                    X = self.feature_scaler.transform(X)
                score = self.current_model.predict_proba(X)[0, 1]
            else:
                return self._fallback_scoring(features)
            
            return max(0, min(1, score))  # Clamp to [0, 1]
            
        except Exception as e:
            logger.error(f"Failed to predict score: {e}")
            return self._fallback_scoring(features)
    
    def _fallback_scoring(self, features: Dict[str, float]) -> float:
        """
        Fallback scoring when no ML model is available
        
        Args:
            features: Feature dictionary
            
        Returns:
            Fallback score (0-1)
        """
        # Simple weighted scoring
        weights = {
            "semantic_similarity": 0.3,
            "filter_score": 0.2,
            "combined_score": 0.2,
            "skill_match_ratio": 0.15,
            "salary_match_score": 0.1,
            "domain_match_score": 0.05
        }
        
        score = 0
        total_weight = 0
        
        for feature_name, weight in weights.items():
            if feature_name in features:
                score += features[feature_name] * weight
                total_weight += weight
        
        return score / total_weight if total_weight > 0 else 0.5

# Global instance
ml_trainer_service = MLTrainerService() 