import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../api';
import './EnhancedRecruiterRecommendations.css';

const EnhancedRecruiterRecommendations = () => {
  const navigate = useNavigate();
  const [selectedJobId, setSelectedJobId] = useState('');
  const [recruiterJobs, setRecruiterJobs] = useState([]);
  const [limit, setLimit] = useState(10);
  const [includeExplanation, setIncludeExplanation] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingJobs, setIsLoadingJobs] = useState(true);
  const [error, setError] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [jobDetails, setJobDetails] = useState(null);

  // Fetch recruiter's jobs on component mount
  useEffect(() => {
    fetchRecruiterJobs();
  }, []);

  const fetchRecruiterJobs = async () => {
    setIsLoadingJobs(true);
    try {
      // Fetch recent jobs (newest first)
      const response = await fetch('http://localhost:8000/api/v1/jobs/?skip=0&limit=50');

      if (response.ok) {
        const jobs = await response.json();
        // Sort by created_at descending if available
        const sorted = Array.isArray(jobs)
          ? [...jobs].sort((a, b) => {
              const ad = new Date(a.created_at || 0).getTime();
              const bd = new Date(b.created_at || 0).getTime();
              return bd - ad;
            })
          : [];
        setRecruiterJobs(sorted);
        // Auto-select the newest job for convenience
        if (sorted.length > 0) {
          setSelectedJobId(String(sorted[0].id));
        }
        console.log('Fetched jobs:', jobs);
      } else {
        setError('Failed to fetch jobs. Please try again.');
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setError('Failed to fetch jobs. Please try again.');
    } finally {
      setIsLoadingJobs(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedJobId) {
      setError('Please select a job.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Use public endpoint for testing
      const response = await fetch('http://localhost:8000/api/v1/recommendations/recruiter/candidates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: parseInt(selectedJobId),
          limit: limit,
          include_explanation: includeExplanation
        })
      });

      if (response.ok) {
        const recommendations = await response.json();
        setRecommendations(recommendations);
        console.log('Recommendations:', recommendations);
        
        // Get job details for context
        const selectedJob = recruiterJobs.find(job => job.id === parseInt(selectedJobId));
        if (selectedJob) {
          setJobDetails(selectedJob);
        }
      } else {
        const errorData = await response.json();
        setError(`Failed to get recommendations: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Recruiter recommendations error:', error);
      setError('Failed to get recommendations. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRecommendationClick = (recommendation) => {
    setSelectedRecommendation(selectedRecommendation?.candidate_id === recommendation.candidate_id ? null : recommendation);
  };

  const handleFeedback = async (recommendation, feedbackType) => {
    try {
      await apiService.submitFeedback({
        user_id: 1, // Recruiter ID
        user_type: 'recruiter',
        job_id: selectedJobId,
        candidate_id: recommendation.candidate_id,
        feedback_type: feedbackType,
        feedback_score: feedbackType === 'positive' ? 1 : 0,
        feedback_text: `${feedbackType} feedback for candidate ${recommendation.candidate_id}`,
        match_score: recommendation.match_score,
        interaction_type: 'view'
      });
      alert('Feedback submitted successfully!');
    } catch (error) {
      console.error('Feedback error:', error);
      alert('Failed to submit feedback.');
    }
  };

  const getMatchScoreColor = (score) => {
    if (score >= 0.8) return '#28a745';
    if (score >= 0.6) return '#ffc107';
    if (score >= 0.4) return '#fd7e14';
    return '#dc3545';
  };

  const getProficiencyColor = (level) => {
    switch (level) {
      case 'expert': return '#28a745';
      case 'advanced': return '#17a2b8';
      case 'intermediate': return '#ffc107';
      case 'beginner': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const getSkillMatchStatus = (skill) => {
    if (skill.meets_requirement) {
      return { text: '✅ Meets Requirement', color: '#28a745' };
    } else if (skill.candidate_years > 0) {
      return { text: '⚠️ Below Requirement', color: '#ffc107' };
    } else {
      return { text: '❌ No Experience', color: '#dc3545' };
    }
  };

  return (
    <div className="enhanced-recruiter-recommendations">
      {/* Header with Logout */}
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title" aria-label="Candidate Recommendations">
            <span className="title-icon" aria-hidden="true">🎯</span>
            Candidate Recommendations
          </h1>
          <p className="page-subtitle">
            Find the best candidates for your job based on skill-specific experience matching
          </p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-logout"
            onClick={() => {
              localStorage.clear();
              window.location.href = '/';
            }}
          >
            🚪 Logout
          </button>
        </div>
      </div>

      <div className="form-section">
        <div className="form-container">
          <h3>📋 Select Your Job</h3>
          
          {isLoadingJobs ? (
            <div className="loading-message">Loading your jobs...</div>
          ) : recruiterJobs.length === 0 ? (
            <div className="no-jobs-message">
              <p>No jobs found. Please post a job first!</p>
              <button 
                onClick={() => navigate('/jobs-dashboard')}
                className="btn-secondary"
              >
                Post a Job
              </button>
            </div>
          ) : (
            <>
              <div className="form-grid" role="form" aria-labelledby="job-select">
                <div className="form-group full">
                  <label htmlFor="job-select">Select Job</label>
                  <select
                    id="job-select"
                    aria-label="Select job to find matching candidates"
                    value={selectedJobId}
                    onChange={(e) => setSelectedJobId(e.target.value)}
                    className="form-select"
                  >
                    <option value="">Choose a job...</option>
                    {recruiterJobs.map((job) => {
                      const label = `[${job.id}] ${job.title} - ${job.company || 'Company'} (${job.location || 'Location'})`;
                      return (
                        <option key={job.id} value={job.id}>
                          {label}
                        </option>
                      );
                    })}
                  </select>
                </div>

                <div className="form-group compact">
                  <label htmlFor="limit-input">Number of Candidates</label>
                  <input
                    id="limit-input"
                    aria-label="Number of candidates to fetch"
                    type="number"
                    value={limit}
                    onChange={(e) => setLimit(parseInt(e.target.value) || 0)}
                    min="1"
                    max="50"
                    className="form-input"
                  />
                </div>

                <div className="form-group checkbox">
                  <label htmlFor="include-expl">
                    <input
                      id="include-expl"
                      type="checkbox"
                      checked={includeExplanation}
                      onChange={(e) => setIncludeExplanation(e.target.checked)}
                      aria-label="Include detailed explanations"
                    />
                    Include detailed explanations
                  </label>
                </div>

                <div className="form-actions">
                  <button 
                    onClick={handleSubmit}
                    disabled={!selectedJobId || isLoading}
                    className="btn-primary btn-find"
                    aria-label="Find candidates for the selected job"
                  >
                    {isLoading ? '🔍 Finding Candidates...' : '🎯 Find Candidates'}
                  </button>
                </div>
              </div>
            </>
          )}

          {error && <div className="error-message">{error}</div>}
        </div>
      </div>

      {jobDetails && (
        <div className="job-details">
          <h3>📋 Job Details</h3>
          <div className="job-info">
            <div className="job-basic">
              <h4>{jobDetails.title}</h4>
              <p><strong>Company:</strong> {jobDetails.company}</p>
              <p><strong>Location:</strong> {jobDetails.location}</p>
              <p><strong>Experience Required:</strong> {jobDetails.total_years_required} years</p>
            </div>
            <div className="job-description">
              <strong>Description:</strong>
              <p>{jobDetails.job_description}</p>
            </div>
          </div>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="recommendations-results">
          <h3>👥 Candidate Recommendations</h3>
          <p>Found {recommendations.length} matching candidates</p>
          
          <div className="recommendations-grid">
            {recommendations.map((recommendation, index) => (
              <div 
                key={index} 
                className={`recommendation-card ${selectedRecommendation?.candidate_id === recommendation.candidate_id ? 'selected' : ''}`}
                onClick={() => handleRecommendationClick(recommendation)}
              >
                <div className="card-header">
                  <h4>Candidate #{recommendation.candidate_id}</h4>
                  <div 
                    className="match-score"
                    style={{ backgroundColor: getMatchScoreColor(recommendation.match_score) }}
                  >
                    {(recommendation.match_score * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="card-content">
                  <div className="match-breakdown">
                    <div className="breakdown-item">
                      <span>✅ Skill Matches:</span>
                      <span>{recommendation.skill_matches?.length || 0}</span>
                    </div>
                    <div className="breakdown-item">
                      <span>❌ Missing Skills:</span>
                      <span>{recommendation.missing_skills?.length || 0}</span>
                    </div>
                    <div className="breakdown-item">
                      <span>⚠️ Experience Gaps:</span>
                      <span>{recommendation.experience_gaps?.length || 0}</span>
                    </div>
                    <div className="breakdown-item">
                      <span>💪 Strengths:</span>
                      <span>{recommendation.strengths?.length || 0}</span>
                    </div>
                  </div>

                  <div className="explanation">
                    <strong>Match Explanation:</strong>
                    <p>{recommendation.explanation || 'No explanation available'}</p>
                  </div>
                </div>

                {selectedRecommendation?.candidate_id === recommendation.candidate_id && (
                  <div className="card-details">
                    <h5>Detailed Skill Analysis</h5>
                    {recommendation.skill_matches?.map((skill, skillIndex) => {
                      const status = getSkillMatchStatus(skill);
                      return (
                        <div key={skillIndex} className="skill-match-item">
                          <div className="skill-header">
                            <span className="skill-name">{skill.skill_name}</span>
                            <span 
                              className="proficiency-badge"
                              style={{ backgroundColor: getProficiencyColor(skill.proficiency_level) }}
                            >
                              {skill.proficiency_level}
                            </span>
                          </div>
                          <div className="skill-details">
                            <span>Required: {skill.required_years} years</span>
                            <span>Candidate: {skill.candidate_years} years</span>
                            <span>Match: {(skill.match_score * 100).toFixed(0)}%</span>
                          </div>
                          <div className="requirement-status" style={{ color: status.color }}>
                            {status.text}
                          </div>
                        </div>
                      );
                    })}

                    {recommendation.missing_skills?.length > 0 && (
                      <div className="missing-skills">
                        <h6>❌ Missing Skills:</h6>
                        <div className="missing-skills-list">
                          {recommendation.missing_skills.map((skill, index) => (
                            <span key={index} className="missing-skill-tag">{skill}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {recommendation.experience_gaps?.length > 0 && (
                      <div className="experience-gaps">
                        <h6>⚠️ Experience Gaps:</h6>
                        <div className="experience-gaps-list">
                          {recommendation.experience_gaps.map((gap, index) => (
                            <span key={index} className="gap-tag">{gap}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {recommendation.strengths?.length > 0 && (
                      <div className="strengths">
                        <h6>💪 Strengths:</h6>
                        <div className="strengths-list">
                          {recommendation.strengths.map((strength, index) => (
                            <span key={index} className="strength-tag">{strength}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="card-actions">
                  <button 
                    className="btn-view-profile"
                    onClick={(e) => {
                      e.stopPropagation();
                      alert(`Viewing profile for candidate ${recommendation.candidate_id}`);
                    }}
                  >
                    View Profile
                  </button>
                  <button 
                    className="btn-contact"
                    onClick={(e) => {
                      e.stopPropagation();
                      alert(`Contacting candidate ${recommendation.candidate_id}`);
                    }}
                  >
                    Contact
                  </button>
                  <div className="feedback-buttons">
                    <button 
                      className="btn-feedback positive"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleFeedback(recommendation, 'positive');
                      }}
                    >
                      👍 Good Match
                    </button>
                    <button 
                      className="btn-feedback negative"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleFeedback(recommendation, 'negative');
                      }}
                    >
                      👎 Poor Match
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {recommendations.length === 0 && !isLoading && selectedJobId && (
        <div className="no-results">
          <h3>🔍 No Matching Candidates Found</h3>
          <p>Try adjusting your search criteria or check if the job ID is correct.</p>
          <div className="suggestions">
            <h4>Suggestions:</h4>
            <ul>
              <li>Verify the job ID exists in the system</li>
              <li>Check if the job has skill requirements defined</li>
              <li>Try increasing the number of candidates</li>
              <li>Consider relaxing skill requirements</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedRecruiterRecommendations; 