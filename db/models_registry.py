"""
Import all models to ensure they are registered with SQLAlchemy Base
This file should be imported before creating tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    Candidate,
    CandidateExperience,
    Job, 
    JobMandatorySkill,
    Application,
    InteractionLog
)

# Export for easy access
ALL_MODELS = [
    Candidate,
    CandidateExperience,
    Job,
    JobMandatorySkill, 
    Application,
    InteractionLog
]
