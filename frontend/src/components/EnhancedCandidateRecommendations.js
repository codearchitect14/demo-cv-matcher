import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../api';
import './EnhancedCandidateRecommendations.css';

const EnhancedCandidateRecommendations = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'profile'
  const [cvFile, setCvFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cvAnalysis, setCvAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);

  // Profile-based recommendation state
  const [candidateId, setCandidateId] = useState('');
  const [limit, setLimit] = useState(10);
  const [includeExplanation, setIncludeExplanation] = useState(true);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && (file.type === 'application/pdf' || file.type.includes('word'))) {
      setCvFile(file);
      setError(null);
    } else {
      setError('Please select a valid PDF or Word document.');
    }
  };

  const handleCvUpload = async () => {
    if (!cvFile) {
      setError('Please select a CV file first.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('cv_file', cvFile);
      formData.append('candidate_id', candidateId || '1'); // Default to candidate 1 for testing

      const response = await fetch('http://localhost:8000/api/v1/recommendations/cv/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setCvAnalysis(data.cv_analysis);
        setRecommendations(data.recommendations);
        alert('CV uploaded and analyzed successfully!');
      } else {
        const errorData = await response.json();
        setError(`Upload failed: ${typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail)}`);
      }
    } catch (error) {
      console.error('CV upload error:', error);
      setError('Failed to upload CV. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProfileRecommendations = async () => {
    if (!candidateId) {
      setError('Please enter a candidate ID.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiService.getCandidateJobRecommendations({
        candidate_id: parseInt(candidateId),
        limit: limit,
        include_explanation: includeExplanation
      });

      setRecommendations(response);
      setCvAnalysis(null);
    } catch (error) {
      console.error('Profile recommendations error:', error);
      setError('Failed to get recommendations. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRecommendationClick = (recommendation) => {
    setSelectedRecommendation(selectedRecommendation?.job_id === recommendation.job_id ? null : recommendation);
  };

  const handleFeedback = async (recommendation, feedbackType) => {
    try {
      await apiService.submitFeedback({
        user_id: candidateId || 1,
        user_type: 'candidate',
        job_id: recommendation.job_id,
        candidate_id: candidateId || 1,
        feedback_type: feedbackType,
        feedback_score: feedbackType === 'positive' ? 1 : 0,
        feedback_text: `${feedbackType} feedback for job ${recommendation.job_id}`,
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
    // Color-blind friendly scale: cyan -> blue -> indigo -> slate
    if (score >= 0.8) return '#0EA5E9';      // cyan
    if (score >= 0.6) return '#3B82F6';      // blue
    if (score >= 0.4) return '#6366F1';      // indigo
    return '#64748B';                        // slate
  };

  const getProficiencyColor = (level) => {
    // Color-blind friendly badges
    switch (level) {
      case 'expert': return '#0EA5E9';        // cyan
      case 'advanced': return '#6366F1';      // indigo
      case 'intermediate': return '#3B82F6';  // blue
      case 'beginner': return '#94A3B8';      // gray
      default: return '#94A3B8';
    }
  };

  return (
    <div className="enhanced-candidate-recommendations">
      <div className="recommendations-header">
        <h1>Enhanced Job Recommendations</h1>
        <p>Get personalized job recommendations based on your skills and experience</p>
      </div>

      <div className="tab-container">
        <button 
          className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          📄 Upload CV
        </button>
        <button 
          className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          👤 Use Profile
        </button>
      </div>

      {activeTab === 'upload' && (
        <div className="cv-upload-section">
          <div className="upload-container">
            <h3>Upload Your CV</h3>
            <p>Upload your CV to get skill-specific job recommendations</p>
            
            <div className="file-input-container">
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileChange}
                className="file-input"
                aria-label="Upload CV file (PDF or Word)"
              />
              <button 
                onClick={handleCvUpload}
                disabled={!cvFile || isLoading}
                className="btn-upload"
                aria-label="Upload and analyze CV"
              >
                {isLoading ? 'Uploading...' : 'Upload & Analyze'}
              </button>
            </div>

            <div className="candidate-id-input">
              <label htmlFor="candidate-id-upload">Candidate ID (for testing):</label>
              <input
                id="candidate-id-upload"
                type="number"
                value={candidateId}
                onChange={(e) => setCandidateId(e.target.value)}
                placeholder="Enter candidate ID"
                className="form-input"
                aria-label="Candidate ID"
              />
            </div>

            {error && <div className="error-message">{error}</div>}
          </div>

          {cvAnalysis && (
            <div className="cv-analysis">
              <h3>📊 CV Analysis Results</h3>
              <div className="analysis-grid">
                <div className="analysis-section">
                  <h4>👤 Personal Info</h4>
                  <p><strong>Name:</strong> {cvAnalysis.full_name || 'Not detected'}</p>
                  <p><strong>Email:</strong> {cvAnalysis.email || 'Not detected'}</p>
                  <p><strong>Location:</strong> {cvAnalysis.location || 'Not detected'}</p>
                </div>
                
                <div className="analysis-section">
                  <h4>💼 Experience</h4>
                  <p><strong>Total Experience:</strong> {cvAnalysis.total_experience?.toFixed(1) || 0} years</p>
                  <p><strong>Work Experiences:</strong> {cvAnalysis.experiences || 0}</p>
                  <p><strong>Education:</strong> {cvAnalysis.education || 0}</p>
                </div>
                
                <div className="analysis-section">
                  <h4>🛠️ Skills Detected</h4>
                  <div className="skills-container">
                    {cvAnalysis.skills?.map((skill, index) => (
                      <span key={index} className="skill-tag">{skill}</span>
                    ))}
                  </div>
                </div>
                
                <div className="analysis-section">
                  <h4>🏆 Certifications</h4>
                  <div className="certifications-container">
                    {cvAnalysis.certifications?.map((cert, index) => (
                      <span key={index} className="certification-tag">{cert}</span>
                    ))}
                  </div>
                </div>
                
                <div className="analysis-section">
                  <h4>🌍 Languages</h4>
                  <div className="languages-container">
                    {cvAnalysis.languages?.map((lang, index) => (
                      <span key={index} className="language-tag">{lang}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'profile' && (
        <div className="profile-section">
          <div className="form-container">
            <h3>Use Existing Profile</h3>
            
            <div className="form-group">
              <label htmlFor="candidate-id-profile">Candidate ID:</label>
              <input
                id="candidate-id-profile"
                type="number"
                value={candidateId}
                onChange={(e) => setCandidateId(e.target.value)}
                placeholder="Enter candidate ID"
                className="form-input"
                aria-label="Candidate ID"
              />
            </div>

            <div className="form-group">
              <label htmlFor="rec-limit">Number of Recommendations:</label>
              <input
                id="rec-limit"
                type="number"
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                min="1"
                max="50"
                className="form-input"
                aria-label="Number of recommendations"
              />
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={includeExplanation}
                  onChange={(e) => setIncludeExplanation(e.target.checked)}
                  aria-label="Include detailed explanations"
                />
                Include detailed explanations
              </label>
            </div>

            <button 
              onClick={handleProfileRecommendations}
              disabled={!candidateId || isLoading}
              className="btn-primary"
              aria-label="Get job recommendations"
            >
              {isLoading ? 'Loading...' : 'Get Recommendations'}
            </button>

            {error && <div className="error-message">{error}</div>}
          </div>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="recommendations-results">
          <h3>🎯 Job Recommendations</h3>
          <p>Found {recommendations.length} matching jobs</p>
          
          <div className="recommendations-grid">
            {recommendations.map((recommendation, index) => (
              <div 
                key={index} 
                className={`recommendation-card ${selectedRecommendation?.job_id === recommendation.job_id ? 'selected' : ''}`}
                onClick={() => handleRecommendationClick(recommendation)}
              >
                <div className="card-header">
                  <h4>Job #{recommendation.job_id}</h4>
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
                      <span>{recommendation.skill_matches || 0}</span>
                    </div>
                    <div className="breakdown-item">
                      <span>❌ Missing Skills:</span>
                      <span>{recommendation.missing_skills || 0}</span>
                    </div>
                    <div className="breakdown-item">
                      <span>⚠️ Experience Gaps:</span>
                      <span>{recommendation.experience_gaps || 0}</span>
                    </div>
                    <div className="breakdown-item">
                      <span>💪 Strengths:</span>
                      <span>{recommendation.strengths || 0}</span>
                    </div>
                  </div>

                  <div className="explanation">
                    <strong>Match Explanation:</strong>
                    <p>{recommendation.explanation || 'No explanation available'}</p>
                  </div>
                </div>

                {selectedRecommendation?.job_id === recommendation.job_id && (
                  <div className="card-details">
                    <h5>Detailed Skill Analysis</h5>
                    {recommendation.skill_matches?.map((skill, skillIndex) => (
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
                          <span>Your Experience: {skill.candidate_years} years</span>
                          <span>Match: {(skill.match_score * 100).toFixed(0)}%</span>
                        </div>
                        <div className="requirement-status">
                          {skill.meets_requirement ? '✅ Meets Requirement' : '❌ Below Requirement'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="card-actions">
                  <button 
                    className="btn-apply"
                    onClick={(e) => {
                      e.stopPropagation();
                      alert(`Applied to job ${recommendation.job_id}`);
                    }}
                  >
                    Apply Now
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
    </div>
  );
};

export default EnhancedCandidateRecommendations; 