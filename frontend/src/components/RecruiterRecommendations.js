import React, { useState } from 'react';
import { apiService } from '../api';
import './RecruiterRecommendations.css';

const RecruiterRecommendations = () => {
  const [activeTab, setActiveTab] = useState('job'); // 'job' or 'quick'
  const [formData, setFormData] = useState({
    job_id: '',
    limit: 10,
    include_explanation: true
  });
  const [quickMatchData, setQuickMatchData] = useState({
    job_title: '',
    required_skills: '',
    experience_required: 0,
    location: '',
    limit: 5
  });
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleQuickMatchChange = (e) => {
    const { name, value } = e.target;
    setQuickMatchData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleJobRecommendations = async (e) => {
    e.preventDefault();
    if (!formData.job_id) {
      setError('Please enter a job ID');
      return;
    }

    setLoading(true);
    setError('');
    setRecommendations([]);

    try {
      const response = await apiService.getRecruiterCandidateRecommendations({
        job_id: parseInt(formData.job_id),
        limit: formData.limit,
        include_explanation: formData.include_explanation
      });
      setRecommendations(response);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get recommendations';
      setError(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
    } finally {
      setLoading(false);
    }
  };

  const handleQuickMatch = async (e) => {
    e.preventDefault();
    if (!quickMatchData.job_title || !quickMatchData.required_skills) {
      setError('Please enter job title and required skills');
      return;
    }

    setLoading(true);
    setError('');
    setRecommendations([]);

    try {
      const skills = quickMatchData.required_skills.split(',').map(s => s.trim());
      const response = await apiService.quickRecruiterMatch({
        job_title: quickMatchData.job_title,
        required_skills: skills,
        experience_required: parseFloat(quickMatchData.experience_required),
        location: quickMatchData.location || undefined,
        limit: quickMatchData.limit
      });
      setRecommendations(response.matches);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get quick matches';
      setError(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (candidateId, feedbackType) => {
    try {
      await apiService.submitFeedback({
        user_id: parseInt(formData.job_id) || 1,
        user_type: 'recruiter',
        candidate_id: candidateId,
        feedback_type: feedbackType,
        feedback_score: feedbackType === 'positive' ? 0.9 : 0.1,
        match_score: recommendations.find(r => r.candidate_id === candidateId)?.match_score || 0.5,
        interaction_type: 'feedback'
      });
      
      alert('Feedback submitted successfully!');
    } catch (err) {
      setError('Failed to submit feedback');
    }
  };

  return (
    <div className="recruiter-recommendations">
      <div className="recommendations-header">
        <h1>Candidate Recommendations for Recruiters</h1>
        <p>Find the best candidates for your job openings</p>
      </div>

      <div className="tab-container">
        <button 
          className={`tab-button ${activeTab === 'job' ? 'active' : ''}`}
          onClick={() => setActiveTab('job')}
        >
          Existing Job
        </button>
        <button 
          className={`tab-button ${activeTab === 'quick' ? 'active' : ''}`}
          onClick={() => setActiveTab('quick')}
        >
          Quick Match
        </button>
      </div>

      {activeTab === 'job' && (
        <div className="recommendations-form-container">
          <form onSubmit={handleJobRecommendations} className="recommendations-form">
            <div className="form-group">
              <label htmlFor="job_id">Job ID:</label>
              <input
                type="number"
                id="job_id"
                name="job_id"
                value={formData.job_id}
                onChange={handleInputChange}
                placeholder="Enter job ID"
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="limit">Number of Recommendations:</label>
              <select
                id="limit"
                name="limit"
                value={formData.limit}
                onChange={handleInputChange}
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={15}>15</option>
                <option value={20}>20</option>
              </select>
            </div>

            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="include_explanation"
                  checked={formData.include_explanation}
                  onChange={handleInputChange}
                />
                <span className="checkmark"></span>
                Include detailed explanations
              </label>
            </div>

            <div className="form-actions">
              <button 
                type="submit" 
                className="btn-primary"
                disabled={loading}
              >
                {loading ? 'Getting Recommendations...' : 'Get Candidate Recommendations'}
              </button>
            </div>
          </form>
        </div>
      )}

      {activeTab === 'quick' && (
        <div className="recommendations-form-container">
          <form onSubmit={handleQuickMatch} className="recommendations-form">
            <div className="form-group">
              <label htmlFor="job_title">Job Title:</label>
              <input
                type="text"
                id="job_title"
                name="job_title"
                value={quickMatchData.job_title}
                onChange={handleQuickMatchChange}
                placeholder="e.g., Senior Python Developer"
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="required_skills">Required Skills (comma-separated):</label>
              <input
                type="text"
                id="required_skills"
                name="required_skills"
                value={quickMatchData.required_skills}
                onChange={handleQuickMatchChange}
                placeholder="e.g., Python, Django, PostgreSQL"
                required
              />
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="experience_required">Experience Required (years):</label>
                <input
                  type="number"
                  id="experience_required"
                  name="experience_required"
                  value={quickMatchData.experience_required}
                  onChange={handleQuickMatchChange}
                  min="0"
                  step="0.5"
                  placeholder="3"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="location">Location (optional):</label>
                <input
                  type="text"
                  id="location"
                  name="location"
                  value={quickMatchData.location}
                  onChange={handleQuickMatchChange}
                  placeholder="e.g., New York, NY"
                />
              </div>
            </div>
            
            <div className="form-group">
              <label htmlFor="quick_limit">Number of Matches:</label>
              <select
                id="quick_limit"
                name="limit"
                value={quickMatchData.limit}
                onChange={handleQuickMatchChange}
              >
                <option value={3}>3</option>
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={15}>15</option>
              </select>
            </div>

            <div className="form-actions">
              <button 
                type="submit" 
                className="btn-primary"
                disabled={loading}
              >
                {loading ? 'Finding Matches...' : 'Find Quick Matches'}
              </button>
            </div>
          </form>
        </div>
      )}

      {error && (
        <div className="error-message">
          <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="recommendations-results">
          <h2>Recommended Candidates ({recommendations.length})</h2>
          <div className="recommendations-grid">
            {recommendations.map((candidate, index) => (
              <div key={index} className="recommendation-card">
                <div className="card-header">
                  <h3>{candidate.title || candidate.name}</h3>
                  <div className="match-score">
                    <span className="score">{Math.round(candidate.match_score * 100)}%</span>
                    <span className="label">Match</span>
                  </div>
                </div>
                
                <div className="card-content">
                  <p><strong>Location:</strong> {candidate.location}</p>
                  {candidate.experience_years && (
                    <p><strong>Experience:</strong> {candidate.experience_years} years</p>
                  )}
                  
                  {candidate.skill_match && (
                    <div className="match-breakdown">
                      <div className="match-item">
                        <span>Skills: {Math.round(candidate.skill_match * 100)}%</span>
                      </div>
                      {candidate.experience_match && (
                        <div className="match-item">
                          <span>Experience: {Math.round(candidate.experience_match * 100)}%</span>
                        </div>
                      )}
                      {candidate.location_match && (
                        <div className="match-item">
                          <span>Location: {Math.round(candidate.location_match * 100)}%</span>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {candidate.explanation && (
                    <div className="explanation">
                      <p><strong>Why this candidate matches:</strong></p>
                      <p>{candidate.explanation}</p>
                    </div>
                  )}
                  
                  {candidate.highlights && candidate.highlights.length > 0 && (
                    <div className="highlights">
                      <p><strong>Highlights:</strong></p>
                      <ul>
                        {candidate.highlights.map((highlight, idx) => (
                          <li key={idx}>{highlight}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {candidate.concerns && candidate.concerns.length > 0 && (
                    <div className="concerns">
                      <p><strong>Considerations:</strong></p>
                      <ul>
                        {candidate.concerns.map((concern, idx) => (
                          <li key={idx}>{concern}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                
                <div className="card-actions">
                  <button 
                    className="btn-view"
                    onClick={() => window.open(`/candidates/${candidate.candidate_id || candidate.id}`, '_blank')}
                  >
                    View Profile
                  </button>
                  <div className="feedback-buttons">
                    <button 
                      className="btn-feedback positive"
                      onClick={() => handleFeedback(candidate.candidate_id || candidate.id, 'positive')}
                      title="This candidate is a good match"
                    >
                      👍
                    </button>
                    <button 
                      className="btn-feedback negative"
                      onClick={() => handleFeedback(candidate.candidate_id || candidate.id, 'negative')}
                      title="This candidate is not a good match"
                    >
                      👎
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RecruiterRecommendations; 