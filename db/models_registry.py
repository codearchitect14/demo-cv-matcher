"""
Import all models to ensure they are registered with SQLAlchemy Base
This file should be imported before creating tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.candidate import Candidate
from models.job import Job, JobMandatorySkill
from models.application import Application
from models.interaction import InteractionLog
from models.recruiter import Recruiter
from models.audit import AuditLog
from models.skill import Skill
from models.job_skill import JobSkill
from models.candidate_skill import CandidateSkill

# Register all models
ALL_MODELS = [
    Candidate,
    Job,
    JobMandatorySkill,
    Application,
    InteractionLog,
    Recruiter,
    AuditLog,
    Skill,
    JobSkill,
    CandidateSkill,
]
