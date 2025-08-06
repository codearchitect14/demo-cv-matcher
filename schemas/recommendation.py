from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FeedbackTypeEnum(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class InteractionTypeEnum(str, Enum):
    VIEWED = "viewed"
    APPLIED = "applied"
    REJECTED = "rejected"
    FEEDBACK = "feedback"

class CandidateRecommendationRequest(BaseModel):
    """Request for candidate job recommendations"""
    candidate_id: int = Field(..., description="Candidate ID")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Number of recommendations to return")
    include_explanation: Optional[bool] = Field(True, description="Include detailed explanation")

class RecruiterRecommendationRequest(BaseModel):
    """Request for recruiter candidate recommendations"""
    job_id: int = Field(..., description="Job ID")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Number of recommendations to return")
    include_explanation: Optional[bool] = Field(True, description="Include detailed explanation")

class FeedbackRequest(BaseModel):
    """Request for submitting feedback"""
    user_id: int = Field(..., description="User ID")
    user_type: str = Field(..., description="User type (candidate or recruiter)")
    job_id: Optional[int] = Field(None, description="Job ID")
    candidate_id: Optional[int] = Field(None, description="Candidate ID")
    feedback_type: FeedbackTypeEnum = Field(..., description="Type of feedback")
    feedback_score: float = Field(..., ge=0.0, le=1.0, description="Feedback score")
    feedback_text: Optional[str] = Field(None, description="Optional feedback text")
    match_score: float = Field(0.0, ge=0.0, le=1.0, description="Original match score")
    interaction_type: InteractionTypeEnum = Field(InteractionTypeEnum.FEEDBACK, description="Interaction type")

class CVUploadRequest(BaseModel):
    """Request for CV upload and analysis"""
    limit: Optional[int] = Field(10, ge=1, le=20, description="Number of recommendations to return")

class RecommendationResponse(BaseModel):
    """Response for recommendation results"""
    id: int = Field(..., description="ID of the recommended item")
    title: str = Field(..., description="Title of the job or candidate name")
    company: str = Field(..., description="Company name or candidate location")
    location: str = Field(..., description="Location")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Overall match score")
    skill_match: float = Field(..., ge=0.0, le=1.0, description="Skill match score")
    experience_match: float = Field(..., ge=0.0, le=1.0, description="Experience match score")
    location_match: float = Field(..., ge=0.0, le=1.0, description="Location match score")
    education_match: float = Field(..., ge=0.0, le=1.0, description="Education match score")
    soft_skills_match: float = Field(..., ge=0.0, le=1.0, description="Soft skills match score")
    culture_match: float = Field(..., ge=0.0, le=1.0, description="Culture match score")
    recent_activity_bonus: float = Field(..., ge=0.0, le=1.0, description="Recent activity bonus")
    explanation: str = Field(..., description="Human-readable explanation")
    highlights: List[str] = Field(default_factory=list, description="Key highlights")
    concerns: List[str] = Field(default_factory=list, description="Potential concerns")
    action_items: List[str] = Field(default_factory=list, description="Recommended actions")

class FeedbackResponse(BaseModel):
    """Response for feedback submission"""
    success: bool = Field(..., description="Whether feedback was recorded successfully")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(..., description="Timestamp of feedback submission")

class ModelPerformanceResponse(BaseModel):
    """Response for model performance metrics"""
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Model accuracy")
    precision: float = Field(..., ge=0.0, le=1.0, description="Model precision")
    recall: float = Field(..., ge=0.0, le=1.0, description="Model recall")
    f1_score: float = Field(..., ge=0.0, le=1.0, description="Model F1 score")
    total_feedback: int = Field(..., ge=0, description="Total number of feedback entries")
    positive_feedback: int = Field(..., ge=0, description="Number of positive feedback entries")
    negative_feedback: int = Field(..., ge=0, description="Number of negative feedback entries")

class QuickMatchRequest(BaseModel):
    """Request for quick matching"""
    skills: List[str] = Field(..., description="List of skills")
    experience_years: float = Field(..., ge=0.0, description="Years of experience")
    location: Optional[str] = Field(None, description="Location")
    limit: Optional[int] = Field(5, ge=1, le=20, description="Number of matches to return")

class QuickMatchResponse(BaseModel):
    """Response for quick matching"""
    matches: List[Dict[str, Any]] = Field(..., description="List of matches")
    total_matches: int = Field(..., description="Total number of matches found")

class CVAnalysisResponse(BaseModel):
    """Response for CV analysis"""
    extracted_skills: List[str] = Field(..., description="Extracted skills from CV")
    total_experience: float = Field(..., description="Total years of experience")
    location: Optional[str] = Field(None, description="Extracted location")
    certifications: List[str] = Field(default_factory=list, description="Extracted certifications")
    languages: List[str] = Field(default_factory=list, description="Extracted languages")
    soft_skills: List[str] = Field(default_factory=list, description="Extracted soft skills")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted education")

class CVUploadResponse(BaseModel):
    """Response for CV upload and analysis"""
    cv_analysis: CVAnalysisResponse = Field(..., description="CV analysis results")
    recommendations: List[RecommendationResponse] = Field(..., description="Job recommendations")
    total_recommendations: int = Field(..., description="Total number of recommendations")

class FeedbackInsightsResponse(BaseModel):
    """Response for feedback insights"""
    total_feedback: int = Field(..., description="Total number of feedback entries")
    positive_feedback: int = Field(..., description="Number of positive feedback entries")
    negative_feedback: int = Field(..., description="Number of negative feedback entries")
    neutral_feedback: int = Field(..., description="Number of neutral feedback entries")
    average_score: float = Field(..., description="Average feedback score")
    feedback_trend: str = Field(..., description="Feedback trend (improving/stable/declining)")
    top_concerns: List[str] = Field(default_factory=list, description="Top concerns from feedback")
    improvement_areas: List[str] = Field(default_factory=list, description="Areas for improvement")

class PredictionResponse(BaseModel):
    """Response for feedback prediction"""
    predicted_probability: float = Field(..., ge=0.0, le=1.0, description="Predicted probability of positive feedback")
    confidence: str = Field(..., description="Confidence level (high/medium/low)")

# Additional schemas for advanced features

class SkillMatchDetail(BaseModel):
    """Detailed skill match information"""
    skill: str = Field(..., description="Skill name")
    required_years: Optional[float] = Field(None, description="Required years of experience")
    actual_years: Optional[float] = Field(None, description="Actual years of experience")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Skill-specific match score")
    is_required: bool = Field(..., description="Whether this skill is required")

class ExperienceMatchDetail(BaseModel):
    """Detailed experience match information"""
    required_years: float = Field(..., description="Required years of experience")
    actual_years: float = Field(..., description="Actual years of experience")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Experience match score")
    gap: float = Field(..., description="Experience gap (positive if overqualified)")

class LocationMatchDetail(BaseModel):
    """Detailed location match information"""
    job_location: str = Field(..., description="Job location")
    candidate_location: str = Field(..., description="Candidate location")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Location match score")
    is_remote: bool = Field(..., description="Whether the job is remote")

class DetailedRecommendationResponse(BaseModel):
    """Detailed recommendation response with breakdown"""
    basic_info: RecommendationResponse = Field(..., description="Basic recommendation information")
    skill_matches: List[SkillMatchDetail] = Field(..., description="Detailed skill matches")
    experience_match: ExperienceMatchDetail = Field(..., description="Detailed experience match")
    location_match: LocationMatchDetail = Field(..., description="Detailed location match")
    additional_factors: Dict[str, Any] = Field(default_factory=dict, description="Additional matching factors")

class RecommendationFilters(BaseModel):
    """Filters for recommendation requests"""
    min_match_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum match score")
    location_preference: Optional[str] = Field(None, description="Preferred location")
    experience_range: Optional[tuple] = Field(None, description="Experience range (min, max)")
    skill_requirements: Optional[List[str]] = Field(None, description="Required skills")
    exclude_applied: Optional[bool] = Field(False, description="Exclude already applied jobs")
    include_remote: Optional[bool] = Field(True, description="Include remote jobs")

class RecommendationSettings(BaseModel):
    """Settings for recommendation algorithm"""
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "skill_match": 0.35,
            "experience_match": 0.20,
            "location_match": 0.15,
            "education_match": 0.10,
            "soft_skills_match": 0.10,
            "culture_match": 0.05,
            "recent_activity": 0.05
        },
        description="Weights for different matching factors"
    )
    use_ml_ranking: bool = Field(True, description="Use ML-based ranking")
    apply_filters: bool = Field(True, description="Apply business rule filters")
    strict_mode: bool = Field(False, description="Use strict filtering mode") 

class QuickCandidateMatchRequest(BaseModel):
    """Request model for quick candidate matching"""
    skills: List[str] = Field(..., description="List of candidate skills")
    experience_years: float = Field(..., description="Years of experience")
    location: Optional[str] = Field(None, description="Preferred location")
    limit: int = Field(5, description="Maximum number of matches to return")

class QuickRecruiterMatchRequest(BaseModel):
    """Request model for quick recruiter matching"""
    job_title: str = Field(..., description="Job title")
    required_skills: List[str] = Field(..., description="Required skills for the job")
    experience_required: float = Field(..., description="Required years of experience")
    location: Optional[str] = Field(None, description="Job location")
    limit: int = Field(5, description="Maximum number of matches to return") 