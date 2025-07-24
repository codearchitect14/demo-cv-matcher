from .base import BaseModel
from .candidate import Candidate, CandidateExperience
from .job import Job, JobMandatorySkill
from .application import Application, ApplicationStatusEnum
from .interaction import InteractionLog, InteractionTypeEnum

# Import all models to ensure they are registered with SQLAlchemy
__all__ = [
    "BaseModel",
    "Candidate",
    "CandidateExperience", 
    "Job",
    "JobMandatorySkill",
    "Application",
    "ApplicationStatusEnum",
    "InteractionLog",
    "InteractionTypeEnum"
]