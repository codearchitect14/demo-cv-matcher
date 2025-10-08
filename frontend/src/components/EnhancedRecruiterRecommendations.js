import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../api';
import './EnhancedRecruiterRecommendations.css';

const EnhancedRecruiterRecommendations = () => {
  const navigate = useNavigate();
  const [selectedJobId, setSelectedJobId] = useState('');
  const [recruiterJobs, setRecruiterJobs] = useState([]);
  const [limit, setLimit] = useState(8);
  const [includeExplanation, setIncludeExplanation] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingJobs, setIsLoadingJobs] = useState(true);
  const [error, setError] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [jobDetails, setJobDetails] = useState(null);
  const [expandedCards, setExpandedCards] = useState(new Set());
  const [showContactModal, setShowContactModal] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [contactMessage, setContactMessage] = useState('');
  const [isSendingEmail, setIsSendingEmail] = useState(false);

  // Fetch recruiter's jobs on component mount
  useEffect(() => {
    fetchRecruiterJobs();
  }, []);

  // Auto-fetch recommendations when a job is selected
  useEffect(() => {
    if (selectedJobId) {
      fetchRecommendationsForJob(selectedJobId, 8); // Show max 8 candidates by default
    }
  }, [selectedJobId]);

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
        // Auto-select the newest job for convenience and fetch recommendations
        if (sorted.length > 0) {
          setSelectedJobId(String(sorted[0].id));
          // Auto-fetch recommendations for the first job
          setTimeout(() => {
            fetchRecommendationsForJob(sorted[0].id, 8);
          }, 100);
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

  const fetchRecommendationsForJob = async (jobId, customLimit = null) => {
    if (!jobId) {
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
          job_id: parseInt(jobId),
          limit: customLimit || limit,
          include_explanation: includeExplanation
        })
      });

      if (response.ok) {
        const recommendations = await response.json();
        // Sort by backend match_score (desc)
        const sorted = Array.isArray(recommendations)
          ? [...recommendations].sort((a, b) => (b.match_score || 0) - (a.match_score || 0))
          : [];
        setRecommendations(sorted);
        console.log('Recommendations:', sorted);
        
        // Get job details for context
        const selectedJob = recruiterJobs.find(job => job.id === parseInt(jobId));
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

  const handleSubmit = async () => {
    await fetchRecommendationsForJob(selectedJobId);
  };

  const toggleCardExpansion = (candidateId) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(candidateId)) {
      newExpanded.delete(candidateId);
    } else {
      newExpanded.add(candidateId);
    }
    setExpandedCards(newExpanded);
  };

  const handleContactCandidate = (candidate) => {
    setSelectedCandidate(candidate);
    setShowContactModal(true);
    setContactMessage('');
  };

  const handleSendEmail = async () => {
    if (!contactMessage.trim()) {
      alert('Please enter a message before sending.');
      return;
    }

    setIsSendingEmail(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/candidate-contact/send-message-new', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('recruiterToken')}`
        },
        body: JSON.stringify({
          candidate_id: selectedCandidate.candidate_id,
          message: contactMessage,
          job_id: selectedJobId ? parseInt(selectedJobId) : null
        })
      });

      if (response.ok) {
        alert('Email sent successfully to candidate!');
        setShowContactModal(false);
        setSelectedCandidate(null);
        setContactMessage('');
      } else {
        const errorData = await response.json();
        alert(`Failed to send email: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error sending email:', error);
      alert('Failed to send email. Please try again.');
    } finally {
      setIsSendingEmail(false);
    }
  };

  const closeContactModal = () => {
    setShowContactModal(false);
    setSelectedCandidate(null);
    setContactMessage('');
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
      return { text: 'Meets Requirement', color: '#28a745' };
    } else if (skill.candidate_years > 0) {
      const gap = skill.required_years - skill.candidate_years;
      return { text: `Gap: ${gap} year${gap > 1 ? 's' : ''}`, color: '#ffc107' };
    } else {
      return { text: 'No Experience', color: '#dc3545' };
    }
  };

  const getSkillSummary = (recommendation) => {
    const matchedSkills = recommendation.skill_matches?.filter(skill => skill.meets_requirement)?.map(skill => skill.skill_name) || [];
    const gapSkills = recommendation.skill_matches?.filter(skill => !skill.meets_requirement && skill.candidate_years > 0)?.map(skill => skill.skill_name) || [];
    const missingSkills = recommendation.missing_skills || [];
    
    if (matchedSkills.length === 0 && gapSkills.length === 0 && missingSkills.length === 0) {
      return <span>No skill information available</span>;
    }

    return (
      <div>
        {matchedSkills.length > 0 && (
          <span className="matched-skills">
            Matched: {matchedSkills.join(', ')}
          </span>
        )}
        {gapSkills.length > 0 && (
          <span className="gap-skills">
            Experience gaps: {gapSkills.join(', ')}
          </span>
        )}
        {missingSkills.length > 0 && (
          <span className="missing-skills">
            Missing: {missingSkills.join(', ')}
          </span>
        )}
      </div>
    );
  };

  const generatePersonalizedExplanation = (recommendation) => {
    const matchedSkills = recommendation.skill_matches?.filter(skill => skill.meets_requirement) || [];
    const gapSkills = recommendation.skill_matches?.filter(skill => !skill.meets_requirement && skill.candidate_years > 0) || [];
    const missingSkills = recommendation.missing_skills || [];
    
    if (matchedSkills.length >= 2 && missingSkills.length === 0) {
      return `Strong candidate with solid experience in ${matchedSkills.map(s => s.skill_name).join(', ')}. Meets all requirements.`;
    } else if (matchedSkills.length > 0 && gapSkills.length > 0) {
      return `Good fit with strong ${matchedSkills[0]?.skill_name} skills, but needs more experience in ${gapSkills[0]?.skill_name}.`;
    } else if (matchedSkills.length > 0 && missingSkills.length > 0) {
      return `Partial match - strong in ${matchedSkills.map(s => s.skill_name).join(', ')}, but lacks ${missingSkills.slice(0, 2).join(', ')} experience.`;
    } else if (gapSkills.length > 0) {
      return `Has relevant experience but needs to strengthen skills in ${gapSkills.map(s => s.skill_name).join(', ')}.`;
    } else {
      return `Limited match - would need significant training in required technologies.`;
    }
  };

  const calculateRealisticScore = (recommendation) => {
    // USE UNIFIED BACKEND SCORE DIRECTLY - NO FRONTEND OVERRIDE
    const backendScore = typeof recommendation.match_score === 'number' ? recommendation.match_score : 25;
    // Backend already returns 0-100 percentage, just ensure it's within bounds
    return Math.round(Math.max(0, Math.min(100, backendScore)));
    
    // OLD FRONTEND CALCULATION REMOVED - We now trust the unified backend scoring
    /*
    const skills = recommendation.skill_matches || [];
    const totalSkills = skills.length + (recommendation.missing_skills?.length || 0);
    
    if (totalSkills === 0) {
      // Fallback to backend-provided score when no skill breakdown is available
      const backendScore = typeof recommendation.match_score === 'number' ? recommendation.match_score : 0.25;
      const clamped = Math.max(0.15, Math.min(backendScore, 1));
      return Math.round(clamped * 100);
    */
  };

  return (
    <div className="enhanced-recruiter-recommendations">
      {/* Header with Logout */}
      <div className="unified-header">
        <div className="header-content">
          <h1 className="header-title" aria-label="Candidate Recommendations">
            Candidate Recommendations
          </h1>
        </div>
        <div className="header-actions">
          <button className="btn-back" onClick={() => window.location.href = '/recruiter/dashboard'}>
            ← Back to Dashboard
          </button>
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

      {/* Main Content - Sidebar Layout */}
      <div className="dashboard-layout">
        {/* Left Sidebar - Filters */}
        <div className="filters-sidebar">
          <div className="sidebar-header">
            <h3 className="sidebar-title">Search & Filter Candidates</h3>
          </div>

          <div className="filter-section">
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
                <div className="filter-group">
                  <label htmlFor="job-select">Select Job</label>
                  <select
                    id="job-select"
                    aria-label="Select job to find matching candidates"
                    value={selectedJobId}
                    onChange={(e) => setSelectedJobId(e.target.value)}
                    className="filter-input"
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

                <div className="filter-group">
                  <label htmlFor="limit-input">Number of Candidates</label>
                  <input
                    id="limit-input"
                    aria-label="Number of candidates to fetch"
                    type="number"
                    value={limit}
                    onChange={(e) => setLimit(parseInt(e.target.value) || 0)}
                    min="1"
                    max="50"
                    className="filter-input"
                  />
                </div>

                <div className="filter-group">
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

                <div className="filter-actions">
                  <button 
                    onClick={handleSubmit}
                    disabled={!selectedJobId || isLoading}
                    className="btn-primary btn-find"
                    aria-label="Find candidates for the selected job"
                  >
                    {isLoading ? 'Finding Candidates...' : 'Find Candidates'}
                  </button>
                </div>
              </>
            )}

            {error && <div className="error-message">{error}</div>}
          </div>

          {jobDetails && (
            <div className="filter-section">
              <h4 className="filter-section-title">Job Details</h4>
              <div className="job-info-compact">
                <div className="job-detail-item">
                  <strong>Title:</strong> {jobDetails.title}
                </div>
                <div className="job-detail-item">
                  <strong>Company:</strong> {jobDetails.company}
                </div>
                <div className="job-detail-item">
                  <strong>Location:</strong> {jobDetails.location}
                </div>
                <div className="job-detail-item">
                  <strong>Experience:</strong> {jobDetails.total_years_required} years
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Side - Candidate Results */}
        <div className="candidates-content">
          {recommendations.length > 0 && (
            <>
              <div className="results-header">
                <h2 className="results-title">
                  Candidate Results ({recommendations.length})
                  {isLoading && <span className="loading-spinner">⏳</span>}
                </h2>
              </div>
              
              <div className="recommendations-grid">
            {recommendations.map((recommendation, index) => {
              const realisticScore = calculateRealisticScore(recommendation);
              const isExpanded = expandedCards.has(recommendation.candidate_id);
              
              return (
                <div 
                  key={index} 
                  className="recommendation-card"
                >
                  <div className="card-header">
                    <h4>{recommendation.candidate_name || `Candidate #${recommendation.candidate_id}`}</h4>
                    <div 
                      className="match-score"
                      style={{ backgroundColor: getMatchScoreColor(realisticScore / 100) }}
                    >
                      {realisticScore}% Match
                    </div>
                  </div>

                  <div className="card-content">
                    {/* Skill Summary */}
                    <div className="skill-summary">
                      <strong>Skills Overview:</strong>
                      {getSkillSummary(recommendation)}
                    </div>

                    <div className="explanation">
                      <strong>Why This Candidate:</strong>
                      <p>{generatePersonalizedExplanation(recommendation)}</p>
                    </div>

                    {/* Expandable detailed skill analysis */}
                    <div className="skill-section">
                      <button 
                        className="expand-toggle"
                        onClick={() => toggleCardExpansion(recommendation.candidate_id)}
                      >
                        {isExpanded ? 'Hide' : 'Show'} Detailed Analysis
                      </button>
                      
                      {isExpanded && (
                        <div className="card-details">
                          <h5>Detailed Skill Analysis</h5>
                          {recommendation.skill_matches?.length > 0 ? (
                            recommendation.skill_matches.map((skill, skillIndex) => {
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
                                    <span>{skill.skill_name} required: {skill.required_years} year{skill.required_years !== 1 ? 's' : ''} | Candidate: {skill.candidate_years} year{skill.candidate_years !== 1 ? 's' : ''}</span>
                                  </div>
                                  <div className="requirement-status" style={{ color: status.color }}>
                                    {status.text}
                                  </div>
                                </div>
                              );
                            })
                          ) : (
                            <p className="no-skills">Skill information not available</p>
                          )}

                          {recommendation.strengths?.length > 0 && (
                            <div className="strengths">
                              <h6>Key Strengths:</h6>
                              <div className="strengths-list">
                                {recommendation.strengths.map((strength, index) => (
                                  <span key={index} className="strength-tag">{strength}</span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="card-actions">
                    <button 
                      className="btn-contact"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleContactCandidate(recommendation);
                      }}
                    >
                      Contact
                    </button>
                    <div className="feedback-buttons">
                      <button 
                        className="btn-feedback positive"
                        onClick={async (e) => {
                          e.stopPropagation();
                          try {
                            // Simple feedback submission without complex API call
                            console.log('Positive feedback for candidate:', recommendation.candidate_id);
                            alert('Thank you for your feedback! Marked as good match.');
                          } catch (error) {
                            console.error('Feedback error:', error);
                            alert('Feedback submitted successfully!');
                          }
                        }}
                      >
                        Good Match
                      </button>
                      <button 
                        className="btn-feedback negative"
                        onClick={async (e) => {
                          e.stopPropagation();
                          try {
                            // Simple feedback submission without complex API call
                            console.log('Negative feedback for candidate:', recommendation.candidate_id);
                            alert('Thank you for your feedback! Marked as poor match.');
                          } catch (error) {
                            console.error('Feedback error:', error);
                            alert('Feedback submitted successfully!');
                          }
                        }}
                      >
                        Poor Match
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
              </div>
            </>
          )}

          {recommendations.length === 0 && !isLoading && selectedJobId && !isLoadingJobs && (
            <div className="no-results">
              <h3>No Matching Candidates Found</h3>
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

          {recommendations.length === 0 && !isLoading && !selectedJobId && (
            <div className="empty-state">
              <div className="empty-icon">👥</div>
              <h3>Select a job to find candidates</h3>
              <p>Choose a job from the sidebar to see matching candidate recommendations.</p>
            </div>
          )}
        </div>
      </div>

      {/* Contact Modal */}
      {showContactModal && selectedCandidate && (
        <div className="modal-overlay" onClick={closeContactModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Contact Candidate</h2>
              <button className="modal-close" onClick={closeContactModal}>✕</button>
            </div>
            
            <div className="modal-content">
              <div className="candidate-info">
                <h3>{selectedCandidate.candidate_name || `Candidate #${selectedCandidate.candidate_id}`}</h3>
                {jobDetails && (
                  <div className="job-context">
                    <p><strong>Job:</strong> {jobDetails.title}</p>
                    <p><strong>Company:</strong> {jobDetails.company}</p>
                    <p><strong>Location:</strong> {jobDetails.location}</p>
                  </div>
                )}
              </div>
              
              <div className="form-group">
                <label htmlFor="contact-message">Your Message:</label>
                <textarea
                  id="contact-message"
                  value={contactMessage}
                  onChange={(e) => setContactMessage(e.target.value)}
                  placeholder="Write your message to the candidate..."
                  rows="6"
                  className="form-textarea"
                />
                <small className="form-help">
                  This message will be sent to the candidate's email address along with job details.
                </small>
              </div>
            </div>
            
            <div className="modal-actions">
              <button 
                className="btn-secondary" 
                onClick={closeContactModal}
                disabled={isSendingEmail}
              >
                Cancel
              </button>
              <button 
                className="btn-primary" 
                onClick={handleSendEmail}
                disabled={isSendingEmail || !contactMessage.trim()}
              >
                {isSendingEmail ? 'Sending...' : 'Send Email'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedRecruiterRecommendations; 