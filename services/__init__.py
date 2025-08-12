# File: services/__init__.py
from .candidate_service import CandidateService
from .interaction_service import InteractionService
from .ml_trainer_service import MLTrainerService
from .personalization_service import PersonalizationService

# Create instances
candidate_service = CandidateService()
interaction_service = InteractionService()
ml_trainer_service = MLTrainerService()
personalization_service = PersonalizationService()

__all__ = [
    "candidate_service",
    "interaction_service", 
    "ml_trainer_service",
    "personalization_service"
]