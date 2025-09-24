"""
Unified Matching Service for Candidate-Job Scoring

This service provides a single, consistent scoring algorithm used by both:
1. Recruiter recommendations (candidate -> job matching)
2. Candidate recommendations (job -> candidate matching)

The SAME candidate-job pair ALWAYS returns the SAME score regardless of which API calls it.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio

logger = logging.getLogger(__name__)

class MatchingService:
    """Unified scoring service for candidate-job matching"""
    
    def __init__(self):
        """Initialize matching service"""
        pass
    
    def calculate_match_score(self, candidate: Dict[str, Any], job: Dict[str, Any]) -> float:
        """
        Calculate unified match score between candidate and job
        
        THIS IS THE SINGLE SOURCE OF TRUTH FOR ALL SCORING
        
        Args:
            candidate: Dict with candidate info
                Required keys: id, name, domain, location, total_experience, expected_salary_min, expected_salary_max, skills
                skills format: [{"skill": "Python", "years": 3}, ...]
            job: Dict with job info  
                Required keys: id, title, domain, location, total_years_required, salary_min, salary_max, skills
                skills format: [{"skill": "Python", "min_experience": 2}, ...]
            
        Returns:
            Final match score as percentage (0-100)
        """
        try:
            # Extract data safely
            candidate_id = candidate.get('id', 'unknown')
            job_id = job.get('id', 'unknown')
            
            # 1. Skills Score (45% weight)
            skills_score = self._calculate_skills_score(
                candidate.get('skills', []), 
                job.get('skills', []),
                job.get('title', '')
            )
            
            # 2. Domain Score (15% weight)
            domain_score = self._calculate_domain_score(
                candidate.get('domain'), 
                job.get('domain')
            )
            
            # 3. Location Score (15% weight)
            location_score = self._calculate_location_score(
                candidate.get('location'), 
                job.get('location')
            )
            
            # 4. Experience Score (15% weight)
            experience_score = self._calculate_experience_score(
                candidate.get('total_experience', 0),
                job.get('total_years_required', 1)
            )
            
            # 5. Education Score (5% weight)
            education_score = self._calculate_education_score(
                candidate.get('education'),
                job.get('education_required')
            )
            
            # 6. Salary Score (5% weight)
            salary_score = self._calculate_salary_score(
                candidate.get('expected_salary_min'),
                candidate.get('expected_salary_max'),
                job.get('salary_min'),
                job.get('salary_max')
            )
            
            # Calculate final weighted score
            final_score = (
                skills_score * 0.45 +
                domain_score * 0.15 +
                location_score * 0.15 +
                experience_score * 0.15 +
                education_score * 0.05 +
                salary_score * 0.05
            ) * 100
            
            # Ensure score is between 0-100
            final_score = max(0.0, min(100.0, final_score))
            
            # DETAILED LOGGING FOR DEBUGGING
            logger.info(f"Scoring details: candidate={candidate_id}, job={job_id}, "
                       f"skills={skills_score:.3f}, domain={domain_score:.3f}, "
                       f"location={location_score:.3f}, exp={experience_score:.3f}, "
                       f"edu={education_score:.3f}, salary={salary_score:.3f}, "
                       f"final={final_score:.2f}")
            
            return round(final_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return 0.0

    def calculate_match_score_with_breakdown(self, candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate unified score and return breakdown for debug consumers."""
        try:
            candidate_id = candidate.get('id', 'unknown')
            job_id = job.get('id', 'unknown')

            skills_score = self._calculate_skills_score(
                candidate.get('skills', []), job.get('skills', []), job.get('title', '')
            )
            domain_score = self._calculate_domain_score(candidate.get('domain'), job.get('domain'))
            location_score = self._calculate_location_score(candidate.get('location'), job.get('location'))
            experience_score = self._calculate_experience_score(
                candidate.get('total_experience', 0), job.get('total_years_required', 1)
            )
            education_score = self._calculate_education_score(
                candidate.get('education'), job.get('education_required')
            )
            salary_score = self._calculate_salary_score(
                candidate.get('expected_salary_min'), candidate.get('expected_salary_max'),
                job.get('salary_min'), job.get('salary_max')
            )

            final_score = (
                skills_score * 0.45 +
                domain_score * 0.15 +
                location_score * 0.15 +
                experience_score * 0.15 +
                education_score * 0.05 +
                salary_score * 0.05
            ) * 100
            final_score = max(0.0, min(100.0, final_score))

            breakdown = {
                "skills_score": round(skills_score, 3),
                "domain_score": round(domain_score, 3),
                "location_score": round(location_score, 3),
                "experience_score": round(experience_score, 3),
                "education_score": round(education_score, 3),
                "salary_score": round(salary_score, 3)
            }

            return {"match_score": round(final_score, 2), "breakdown": breakdown}
        except Exception as e:
            logger.error(
                f"[ScoringError] job_id={job.get('id')} candidate_id={candidate.get('id')} error={str(e)}"
            )
            return {"match_score": 0.0, "breakdown": {}}
    
    def _calculate_skills_score(
        self, 
        candidate_skills: List[Dict[str, Any]], 
        job_skills: List[Dict[str, Any]],
        job_title: str = ""
    ) -> float:
        """
        Calculate skills matching score with semantic matching
        
        Args:
            candidate_skills: [{"skill": "Python", "years": 3}, ...]
            job_skills: [{"skill": "Python", "min_experience": 2}, ...]
            job_title: Job title for skill inference if no explicit skills
            
        Returns:
            Skills score between 0-1
        """
        try:
            # If no candidate skills, return 0
            if not candidate_skills:
                return 0.0
            
            # Get required skills from job_skills or infer from title
            required_skills = []
            if job_skills:
                required_skills = [
                    {
                        "skill": skill.get('skill', ''),
                        "min_experience": skill.get('min_experience', 2)
                    }
                    for skill in job_skills 
                    if skill.get('skill')
                ]
            
            # If no explicit skills, infer from job title
            if not required_skills:
                inferred_skills = self._infer_skills_from_title(job_title)
                required_skills = [
                    {"skill": skill, "min_experience": 2}
                    for skill in inferred_skills
                ]
            
            if not required_skills:
                # If no required skills, assume perfect match
                return 1.0
            
            # Create candidate skill map (safe string handling)
            candidate_skill_map = {}
            for skill in candidate_skills:
                skill_name = str(skill.get('skill', '')).lower().strip()
                years = skill.get('years', 0)
                if skill_name and isinstance(years, (int, float)) and years > 0:
                    candidate_skill_map[skill_name] = years
            
            # Count matched skills using semantic similarity
            matched_skills = 0
            total_match_score = 0.0
            
            for required_skill in required_skills:
                skill_name = str(required_skill.get('skill', '')).lower().strip()
                required_years = required_skill.get('min_experience', 2)
                
                if not skill_name:
                    continue
                
                # Check for exact match first
                if skill_name in candidate_skill_map:
                    candidate_years = candidate_skill_map[skill_name]
                    if candidate_years >= required_years:
                        matched_skills += 1
                        total_match_score += 1.0
                    else:
                        # Partial credit for having the skill but less experience
                        partial_score = candidate_years / required_years
                        total_match_score += min(partial_score, 0.7)
                else:
                    # Check for semantic similarity (simplified)
                    semantic_match = self._find_semantic_skill_match(skill_name, candidate_skill_map)
                    if semantic_match:
                        candidate_years = candidate_skill_map[semantic_match]
                        if candidate_years >= required_years:
                            matched_skills += 1
                            total_match_score += 0.8  # Slight penalty for semantic match
                        else:
                            partial_score = candidate_years / required_years * 0.8
                            total_match_score += min(partial_score, 0.6)
            
            # Calculate final skills score
            skills_ratio = total_match_score / len(required_skills)
            return min(1.0, skills_ratio)
            
        except Exception as e:
            logger.error(f"Error calculating skills score: {e}")
            return 0.0
    
    def _find_semantic_skill_match(self, required_skill: str, candidate_skills: Dict[str, int]) -> Optional[str]:
        """
        Find semantic matches between required skill and candidate skills
        
        Args:
            required_skill: Required skill name (lowercase)
            candidate_skills: Map of candidate skill names to years
            
        Returns:
            Matching candidate skill name or None
        """
        # Semantic skill mappings
        skill_synonyms = {
            'javascript': ['js', 'node.js', 'nodejs', 'react', 'angular', 'vue'],
            'js': ['javascript', 'node.js', 'nodejs', 'react', 'angular', 'vue'],
            'python': ['django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'java': ['spring', 'hibernate', 'jsp', 'servlet'],
            'c#': ['csharp', '.net', 'dotnet', 'asp.net'],
            'sql': ['mysql', 'postgresql', 'database', 'oracle', 'sqlserver'],
            'react': ['javascript', 'js', 'frontend', 'reactjs'],
            'angular': ['javascript', 'js', 'frontend', 'typescript'],
            'vue': ['javascript', 'js', 'frontend', 'vuejs'],
            'aws': ['cloud', 'amazon web services', 'ec2', 's3'],
            'docker': ['containerization', 'kubernetes', 'devops'],
            'machine learning': ['ml', 'ai', 'artificial intelligence', 'data science'],
            'data science': ['ml', 'machine learning', 'ai', 'python', 'pandas'],
        }
        
        # Direct synonyms check
        synonyms = skill_synonyms.get(required_skill, [])
        for candidate_skill in candidate_skills.keys():
            if candidate_skill in synonyms:
                return candidate_skill
            
            # Reverse check
            candidate_synonyms = skill_synonyms.get(candidate_skill, [])
            if required_skill in candidate_synonyms:
                return candidate_skill
        
        # Partial string matching
        for candidate_skill in candidate_skills.keys():
            if required_skill in candidate_skill or candidate_skill in required_skill:
                return candidate_skill
        
        return None
    
    def _calculate_domain_score(self, candidate_domain: Optional[str], job_domain: Optional[str]) -> float:
        """Calculate domain matching score"""
        if not candidate_domain or not job_domain:
            return 0.5  # Neutral score for missing data
        
        candidate_domain = str(candidate_domain).lower().strip()
        job_domain = str(job_domain).lower().strip()
        
        # Exact match
        if candidate_domain == job_domain:
            return 1.0
        
        # Related domains mapping
        related_domains = {
            'it': ['software', 'technology', 'tech', 'computer', 'engineering', 'ai'],
            'software': ['it', 'technology', 'tech', 'computer', 'engineering'],
            'technology': ['it', 'software', 'tech', 'computer', 'engineering'],
            'ai': ['it', 'technology', 'machine learning', 'data science'],
            'data science': ['ai', 'analytics', 'machine learning', 'it'],
            'health': ['healthcare', 'medical', 'medicine', 'pharma'],
            'education': ['teaching', 'academic', 'training'],
            'finance': ['banking', 'financial', 'accounting', 'fintech'],
            'marketing': ['advertising', 'sales', 'business', 'digital marketing'],
        }
        
        # Check for related domains
        for domain, related_list in related_domains.items():
            if (candidate_domain in [domain] + related_list and 
                job_domain in [domain] + related_list):
                return 0.7
        
        return 0.0
    
    def _calculate_location_score(self, candidate_location: Optional[str], job_location: Optional[str]) -> float:
        """Calculate location matching score"""
        if not candidate_location or not job_location:
            return 0.5  # Neutral score for missing data
        
        candidate_location = str(candidate_location).lower().strip()
        job_location = str(job_location).lower().strip()
        
        # Remote job - always perfect match
        if 'remote' in job_location:
            return 1.0
        
        # Exact match
        if candidate_location == job_location:
            return 1.0
        
        # Same city (check if one location contains the other)
        if (candidate_location in job_location or 
            job_location in candidate_location):
            return 1.0
        
        # Same country/region (simplified check)
        candidate_parts = candidate_location.split(',')
        job_parts = job_location.split(',')
        
        if len(candidate_parts) > 1 and len(job_parts) > 1:
            # Check if country/region matches
            if candidate_parts[-1].strip() == job_parts[-1].strip():
                return 0.7
        
        return 0.0
    
    def _calculate_experience_score(self, candidate_experience: float, required_experience: float) -> float:
        """Calculate experience matching score"""
        if required_experience <= 0:
            return 1.0  # No experience required
        
        candidate_experience = float(candidate_experience or 0)
        required_experience = float(required_experience)
        
        # Perfect match or overqualified
        if candidate_experience >= required_experience:
            # Slight bonus for being overqualified, but cap it
            bonus = min((candidate_experience - required_experience) / required_experience * 0.1, 0.2)
            return min(1.0 + bonus, 1.0)
        
        # Underqualified - linear decrease
        experience_ratio = candidate_experience / required_experience
        return max(0.0, experience_ratio)
    
    def _calculate_education_score(self, candidate_education: Optional[str], required_education: Optional[str]) -> float:
        """Calculate education matching score"""
        if not required_education:
            return 1.0  # No education requirement
        
        if not candidate_education:
            return 0.0  # Candidate has no education info
        
        candidate_education = str(candidate_education).lower().strip()
        required_education = str(required_education).lower().strip()
        
        # Exact match
        if candidate_education == required_education:
            return 1.0
        
        # Education hierarchy
        education_levels = {
            'high school': 1,
            'diploma': 2,
            'bachelor': 3,
            'master': 4,
            'mba': 4,
            'phd': 5,
            'doctorate': 5
        }
        
        candidate_level = education_levels.get(candidate_education, 0)
        required_level = education_levels.get(required_education, 0)
        
        if candidate_level >= required_level:
            return 1.0
        
        return 0.0
    
    def _calculate_salary_score(
        self, 
        candidate_salary_min: Optional[int], 
        candidate_salary_max: Optional[int],
        job_salary_min: Optional[int], 
        job_salary_max: Optional[int]
    ) -> float:
        """Calculate salary compatibility score"""
        if not candidate_salary_min or not job_salary_min:
            return 0.5  # Neutral score for missing data
        
        # Calculate average salaries
        candidate_avg = (candidate_salary_min + (candidate_salary_max or candidate_salary_min)) / 2
        job_avg = (job_salary_min + (job_salary_max or job_salary_min)) / 2
        
        # Check if within ±10% range
        tolerance = job_avg * 0.1
        if abs(candidate_avg - job_avg) <= tolerance:
            return 1.0
        
        # Calculate linear decrease outside tolerance
        salary_diff = abs(candidate_avg - job_avg) - tolerance
        max_diff = job_avg * 0.5  # 50% difference = 0 score
        
        if salary_diff >= max_diff:
            return 0.0
        
        # Linear decrease
        score = 1.0 - (salary_diff / max_diff)
        return max(0.0, score)
    
    def _infer_skills_from_title(self, job_title: str) -> List[str]:
        """Infer required skills from job title"""
        if not job_title:
            return []
        
        title_lower = str(job_title).lower()
        skills = []
        
        # Comprehensive skill mapping
        skill_keywords = {
            'Python': ['python', 'django', 'flask', 'fastapi'],
            'JavaScript': ['javascript', 'js', 'node', 'react', 'angular', 'vue'],
            'React': ['react', 'frontend', 'front-end'],
            'Java': ['java', 'spring', 'hibernate'],
            'SQL': ['sql', 'database', 'mysql', 'postgresql'],
            'Machine Learning': ['machine learning', 'ml', 'ai', 'data science'],
            'Data Science': ['data scientist', 'data science', 'analytics'],
            'AWS': ['aws', 'amazon web services', 'cloud'],
            'Docker': ['docker', 'containerization'],
            'Git': ['git', 'version control'],
            'HTML': ['html', 'frontend', 'web'],
            'CSS': ['css', 'frontend', 'styling'],
        }
        
        for skill, keywords in skill_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                skills.append(skill)
        
        return skills[:5]  # Limit to 5 skills

# Global instance
matching_service = MatchingService()