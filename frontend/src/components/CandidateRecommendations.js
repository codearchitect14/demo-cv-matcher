import React, { useState, useEffect } from 'react';
import { apiService } from '../api';
import './CandidateRecommendations.css';

const CandidateRecommendations = () => {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'profile'
  const [formData, setFormData] = useState({
    candidate_id: '',
    limit: 10,
    include_explanation: true
  });
  const [cvFile, setCvFile] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [cvAnalysis, setCvAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setCvFile(file);
    }
  };

  const handleCvUpload = async (e) => {
    e.preventDefault();
    if (!cvFile) {
      setError('Please select a CV file');
      return;
    }

    setLoading(true);
    setError('');
    setRecommendations([]);
    setCvAnalysis(null);

    try {
      const formData = new FormData();
      formData.append('cv_file', cvFile);
      formData.append('limit', 10);

      const response = await apiService.uploadCvAndGetRecommendations(formData);
      setRecommendations(response.recommendations || []);
      setCvAnalysis(response.cv_analysis);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to process CV and get recommendations';
      setError(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
    } finally {
      setLoading(false);
    }
  };

  const handleProfileRecommendations = async (e) => {
    e.preventDefault();
    if (!formData.candidate_id) {
      setError('Please enter a candidate ID');
      return;
    }

    setLoading(true);
    setError('');
    setRecommendations([]);

    try {
      const response = await apiService.getCandidateJobRecommendations({
        candidate_id: parseInt(formData.candidate_id),
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

  const handleFeedback = async (recommendationId, feedbackType) => {
    try {
      await apiService.submitFeedback({
        user_id: parseInt(formData.candidate_id) || 1,
        user_type: 'candidate',
        job_id: recommendationId,
        feedback_type: feedbackType,
        feedback_score: feedbackType === 'positive' ? 0.9 : 0.1,
        match_score: recommendations.find(r => r.id === recommendationId)?.match_score || 0.5,
        interaction_type: 'feedback'
      });
      
      // Show success message
      alert('Feedback submitted successfully!');
    } catch (err) {
      setError('Failed to submit feedback');
    }
  };

  return (
    <div className="candidate-recommendations">
      <div className="recommendations-header">
        <h1>Job Recommendations for Candidates</h1>
        <p>Get personalized job recommendations based on your profile or CV</p>
      </div>

      <div className="tab-container">
        <button 
          className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          Upload CV
        </button>
        <button 
          className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          Use Profile
        </button>
      </div>

      {activeTab === 'upload' && (
        <div className="recommendations-form-container">
          <form onSubmit={handleCvUpload} className="recommendations-form">
            <div className="form-group">
              <label htmlFor="cv_file">Upload CV (PDF, DOCX, DOC):</label>
              <input
                type="file"
                id="cv_file"
                accept=".pdf,.docx,.doc"
                onChange={handleFileChange}
                required
              />
            </div>

            <div className="form-actions">
              <button 
                type="submit" 
                className="btn-primary"
                disabled={loading || !cvFile}
              >
                {loading ? 'Processing CV...' : 'Upload CV & Get Recommendations'}
              </button>
            </div>
          </form>
        </div>
      )}

      {activeTab === 'profile' && (
        <div className="recommendations-form-container">
          <form onSubmit={handleProfileRecommendations} className="recommendations-form">
            <div className="form-group">
              <label htmlFor="candidate_id">Candidate ID:</label>
              <input
                type="number"
                id="candidate_id"
                name="candidate_id"
                value={formData.candidate_id}
                onChange={handleInputChange}
                placeholder="Enter your candidate ID"
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
                {loading ? 'Getting Recommendations...' : 'Get Recommendations'}
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

      {cvAnalysis && (
        <div className="cv-analysis">
          <h2>CV Analysis</h2>
          <div className="analysis-grid">
            <div className="analysis-section">
              <h3>Skills Extracted</h3>
              <div className="skills-list">
                {cvAnalysis.extracted_skills.map((skill, index) => (
                  <span key={index} className="skill-tag">{skill}</span>
                ))}
              </div>
            </div>
            
            <div className="analysis-section">
              <h3>Experience</h3>
              <p><strong>Total Years:</strong> {cvAnalysis.total_experience} years</p>
              <p><strong>Location:</strong> {cvAnalysis.location || 'Not specified'}</p>
            </div>
            
            <div className="analysis-section">
              <h3>Certifications</h3>
              <div className="certifications-list">
                {cvAnalysis.certifications.map((cert, index) => (
                  <span key={index} className="certification-tag">{cert}</span>
                ))}
              </div>
            </div>
            
            <div className="analysis-section">
              <h3>Languages</h3>
              <div className="languages-list">
                {cvAnalysis.languages.map((lang, index) => (
                  <span key={index} className="language-tag">{lang}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="recommendations-results">
          <h2>Recommended Jobs ({recommendations.length})</h2>
          <div className="recommendations-grid">
            {recommendations.map((job, index) => (
              <div key={index} className="recommendation-card">
                <div className="card-header">
                  <h3>{job.title}</h3>
                  <div className="match-score">
                    <span className="score">{Math.round(job.match_score * 100)}%</span>
                    <span className="label">Match</span>
                  </div>
                </div>
                
                <div className="card-content">
                  <p><strong>Company:</strong> {job.company}</p>
                  <p><strong>Location:</strong> {job.location}</p>
                  
                  <div className="match-breakdown">
                    <div className="match-item">
                      <span>Skills: {Math.round(job.skill_match * 100)}%</span>
                    </div>
                    <div className="match-item">
                      <span>Experience: {Math.round(job.experience_match * 100)}%</span>
                    </div>
                    <div className="match-item">
                      <span>Location: {Math.round(job.location_match * 100)}%</span>
                    </div>
                  </div>
                  
                  <div className="explanation">
                    <p><strong>Why this job matches:</strong></p>
                    <p>{job.explanation}</p>
                  </div>
                  
                  {job.highlights.length > 0 && (
                    <div className="highlights">
                      <p><strong>Highlights:</strong></p>
                      <ul>
                        {job.highlights.map((highlight, idx) => (
                          <li key={idx}>{highlight}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {job.concerns.length > 0 && (
                    <div className="concerns">
                      <p><strong>Considerations:</strong></p>
                      <ul>
                        {job.concerns.map((concern, idx) => (
                          <li key={idx}>{concern}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                
                <div className="card-actions">
                  <button 
                    className="btn-apply"
                    onClick={() => window.open(`/jobs/${job.id}`, '_blank')}
                  >
                    View Job
                  </button>
                  <div className="feedback-buttons">
                    <button 
                      className="btn-feedback positive"
                      onClick={() => handleFeedback(job.id, 'positive')}
                      title="This job is relevant"
                    >
                      👍
                    </button>
                    <button 
                      className="btn-feedback negative"
                      onClick={() => handleFeedback(job.id, 'negative')}
                      title="This job is not relevant"
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

export default CandidateRecommendations; 