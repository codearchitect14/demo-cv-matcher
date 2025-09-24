import logging
from typing import Dict, Any, Tuple

from services.matching_service import matching_service

logger = logging.getLogger(__name__)

def calculate_match_score(candidate: Dict[str, Any], job: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """Unified scorer wrapper that returns score and explanation breakdown.

    Returns (match_score, breakdown_dict)
    """
    try:
        result = matching_service.calculate_match_score_with_breakdown(candidate, job)
        score = float(result.get("match_score", 0.0))
        breakdown = result.get("breakdown", {}) or {}
        return score, breakdown
    except Exception as e:
        logger.error(
            f"[ScoringError] job_id={job.get('id')} candidate_id={candidate.get('id')} error={str(e)}"
        )
        return 0.0, {}


