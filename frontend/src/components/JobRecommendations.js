import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../api';
import './JobRecommendations.css';

const JobRecommendations = () => {
  const [userProfile, setUserProfile] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [matchPercentages, setMatchPercentages] = useState({});
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    limit: 10,
    use_ml_ranking: true,
    apply_filters: true,
    strict_mode: false
  });

  useEffect(() => {
    checkAuthentication();
  }, []);

  useEffect(() => {
    // Animate match percentages when recommendations load
    if (recommendations.length > 0) {
      recommendations.forEach((rec, index) => {
        setTimeout(() => {
          setMatchPercentages(prev => ({
            ...prev,
            [rec.job_id]: 0
          }));
          
          const targetPercentage = rec.combined_score ? Math.round(rec.combined_score * 100) : 0;
          let currentPercentage = 0;
          
          const interval = setInterval(() => {
            currentPercentage += 2;
            if (currentPercentage >= targetPercentage) {
              currentPercentage = targetPercentage;
              clearInterval(interval);
            }
            setMatchPercentages(prev => ({
              ...prev,
              [rec.job_id]: currentPercentage
            }));
          }, 30);
        }, index * 200);
      });
    }
  }, [recommendations]);

  const checkAuthentication = async () => {
    try {
      console.log('=== CHECKING AUTHENTICATION ===');
      
      // Check all possible token locations
      const token = localStorage.getItem('access_token') || 
                   localStorage.getItem('token') || 
                   sessionStorage.getItem('access_token') || 
                   sessionStorage.getItem('token');

      console.log('Token found:', !!token);
      if (token) {
        console.log('Token length:', token.length);
        console.log('Token preview:', token.substring(0, 20) + '...');
      }

      if (!token) {
        console.log('No token found, redirecting to login');
        navigate('/login');
        return;
      }

      // Set the token in apiService
      apiService.setAuthToken(token);
      console.log('Token set in apiService');

      // Test the token by calling getCurrentUser
      try {
        const currentUser = await apiService.getCurrentUser();
        console.log('Current user:', currentUser);
        
        if (currentUser) {
          setUserProfile(currentUser);
          setIsAuthenticated(true);
          console.log('Authentication successful');
        } else {
          console.log('No user data returned, redirecting to login');
          navigate('/login');
        }
      } catch (apiError) {
        console.error('API call failed:', apiError);
        
        // If it's a 401, clear the token and redirect
        if (apiError.response && apiError.response.status === 401) {
          console.log('Token is invalid (401), clearing and redirecting');
          localStorage.removeItem('access_token');
          localStorage.removeItem('token');
          sessionStorage.removeItem('access_token');
          sessionStorage.removeItem('token');
          navigate('/login');
        } else {
          console.log('Other API error, redirecting to login');
          navigate('/login');
        }
      }
    } catch (error) {
      console.error('Authentication check failed:', error);
      navigate('/login');
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiService.getJobRecommendations(formData.limit);
      setRecommendations(response);
    } catch (error) {
      console.error('Failed to get recommendations:', error);
      setError('Failed to get recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getMatchColor = (score) => {
    if (score >= 0.7) return '#10b981'; // Green for high match
    if (score >= 0.4) return '#f59e0b'; // Orange for medium match
    return '#ef4444'; // Red for low match
  };

  const getDaysAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (!isAuthenticated) {
    return (
      <div className="job-recommendations">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading your profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="job-recommendations">
      {/* Animated Background */}
      <div className="animated-background">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
        <div className="blob blob-3"></div>
      </div>

      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            Personalized Job Recommendations
          </h1>
          <p className="hero-subtitle">
            Based on your profile and preferences
          </p>
        </div>
      </div>

      {/* Profile & Settings Card */}
      <div className="settings-panel">
        <div className="profile-settings-card">
          <form onSubmit={handleSubmit} className="recommendations-form">
            {/* User Profile Section */}
            <div className="user-profile-section">
              <div className="user-avatar-container">
                <div className="user-avatar">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                  </svg>
                </div>
                <div className="user-details">
                  <h3 className="user-name">{userProfile?.name || 'Candidate'}</h3>
                  <div className="user-info">
                    <div className="info-item">
                      <span className="info-icon">📧</span>
                      <span className="info-text">{userProfile?.email || 'candidate@example.com'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-icon">📍</span>
                      <span className="info-text">{userProfile?.location || 'Location not specified'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendation Settings */}
            <div className="settings-section">
              <h3 className="settings-title">Recommendation Settings</h3>
              
              <div className="settings-grid">
                <div className="setting-group">
                  <label htmlFor="limit" className="setting-label">
                    Number of Recommendations
                  </label>
                  <div className="custom-select">
                    <select
                      id="limit"
                      name="limit"
                      value={formData.limit}
                      onChange={handleInputChange}
                      className="setting-select"
                    >
                      <option value={5}>5 recommendations</option>
                      <option value={10}>10 recommendations</option>
                      <option value={15}>15 recommendations</option>
                      <option value={20}>20 recommendations</option>
                    </select>
                    <div className="select-arrow">▼</div>
                  </div>
                </div>

                <div className="filters-section">
                  <h4 className="filters-title">Filters</h4>
                  <div className="toggle-settings">
                    <div className="toggle-group">
                      <label className="toggle-label">
                        <input
                          type="checkbox"
                          name="use_ml_ranking"
                          checked={formData.use_ml_ranking}
                          onChange={handleInputChange}
                          className="toggle-input"
                        />
                        <span className="toggle-slider"></span>
                        <span className="toggle-text">Use AI-powered ranking</span>
                        <span className="toggle-tooltip" title="Uses machine learning to rank jobs based on your profile">ⓘ</span>
                      </label>
                    </div>
                    
                    <div className="toggle-group">
                      <label className="toggle-label">
                        <input
                          type="checkbox"
                          name="apply_filters"
                          checked={formData.apply_filters}
                          onChange={handleInputChange}
                          className="toggle-input"
                        />
                        <span className="toggle-slider"></span>
                        <span className="toggle-text">Apply smart filters</span>
                        <span className="toggle-tooltip" title="Filters jobs based on location, salary, and experience">ⓘ</span>
                      </label>
                    </div>
                    
                    <div className="toggle-group">
                      <label className="toggle-label">
                        <input
                          type="checkbox"
                          name="strict_mode"
                          checked={formData.strict_mode}
                          onChange={handleInputChange}
                          className="toggle-input"
                        />
                        <span className="toggle-slider"></span>
                        <span className="toggle-text">Strict matching mode</span>
                        <span className="toggle-tooltip" title="Only shows jobs that closely match your requirements">ⓘ</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="error-message">
                <span className="error-text">{error}</span>
                <button onClick={() => setError('')} className="error-close">×</button>
              </div>
            )}

            {/* Submit Button */}
            <button type="submit" className="get-recommendations-btn" disabled={loading}>
              {loading ? (
                <>
                  <div className="btn-spinner"></div>
                  <span>Getting Recommendations...</span>
                </>
              ) : (
                <>
                  <span className="btn-icon">✨</span>
                  <span>Get Personalized Recommendations</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Recommendations Results */}
      {recommendations.length > 0 && (
        <div className="recommendations-results">
          <div className="results-header">
            <h2>Your Personalized Job Recommendations</h2>
            <p className="results-subtitle">Based on your profile and preferences</p>
          </div>
          
          <div className="recommendations-grid">
            {recommendations.map((recommendation, index) => (
              <div 
                key={recommendation.job_id || index} 
                className="recommendation-card"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="card-header">
                  <div className="company-logo">
                    <div className="logo-placeholder">
                      {recommendation.job.company?.charAt(0) || 'C'}
                    </div>
                  </div>
                  
                  <div className="card-title-section">
                    <h3 className="job-title">{recommendation.job.title}</h3>
                    <span className="company-name">{recommendation.job.company}</span>
                  </div>
                  
                  <div className="match-score-container">
                    <div className="match-score-ring">
                      <svg className="progress-ring" width="60" height="60">
                        <circle
                          className="progress-ring-circle-bg"
                          stroke="#e5e7eb"
                          strokeWidth="4"
                          fill="transparent"
                          r="26"
                          cx="30"
                          cy="30"
                        />
                        <circle
                          className="progress-ring-circle"
                          stroke={getMatchColor(recommendation.combined_score)}
                          strokeWidth="4"
                          fill="transparent"
                          r="26"
                          cx="30"
                          cy="30"
                          strokeDasharray={`${2 * Math.PI * 26}`}
                          strokeDashoffset={`${2 * Math.PI * 26 * (1 - (matchPercentages[recommendation.job_id] || 0) / 100)}`}
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className="match-percentage">
                        {matchPercentages[recommendation.job_id] || 0}%
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="card-content">
                  <div className="job-details">
                    <div className="detail-item">
                      <span className="detail-icon">📍</span>
                      <span className="detail-text">{recommendation.job.location}</span>
                    </div>
                    
                    <div className="detail-item">
                      <span className="detail-icon">💰</span>
                      <span className="detail-text">
                        {recommendation.job.salary_min && recommendation.job.salary_max 
                          ? `$${recommendation.job.salary_min.toLocaleString()} - $${recommendation.job.salary_max.toLocaleString()}`
                          : 'Salary not specified'}
                      </span>
                    </div>
                    
                    <div className="detail-item">
                      <span className="detail-icon">⏰</span>
                      <span className="detail-text">{recommendation.job.total_years_required} years experience</span>
                    </div>
                    
                    <div className="detail-item">
                      <span className="detail-icon">📅</span>
                      <span className="detail-text">
                        Posted {getDaysAgo(recommendation.job.created_at)} days ago
                      </span>
                    </div>
                  </div>
                  
                  <div className="job-description">
                    <p>{recommendation.job.job_description?.substring(0, 120)}...</p>
                  </div>
                </div>
                
                <div className="card-actions">
                  <button className="btn-view-details">
                    <span className="btn-icon-small">👁️</span>
                    View Details
                  </button>
                  <button className="btn-apply-now">
                    <span className="btn-icon-small">📝</span>
                    Apply Now
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default JobRecommendations; 