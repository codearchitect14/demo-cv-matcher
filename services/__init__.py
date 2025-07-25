# File: services/__init__.py
# from .candidate_service import CandidateService
# __all__ = ["CandidateService"]

# Today's date: 25/07/2025
from .candidate_service import CandidateService
from .job_service import JobService
from .application_service import ApplicationService
# from .interaction_service import InteractionService
# from .search_service import SearchService

__all__ = [
    'CandidateService',
    'JobService',
    'ApplicationService'
    # 'InteractionService',
    # 'SearchService'
]