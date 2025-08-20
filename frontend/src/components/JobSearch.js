import React, { useState, useEffect } from 'react';
import { apiService } from '../api';
import api from '../api';
import './JobSearch.css';

const JobSearch = () => {
  const [formData, setFormData] = useState({
    query: '',
    limit: 10,
    apply_filters: true,
    strict_mode: false,
    use_ml_ranking: true
  });
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [showJobModal, setShowJobModal] = useState(false);
  const [applicationStatus, setApplicationStatus] = useState({});

  // Initialize authentication when component loads
  useEffect(() => {
    // Initialize auth token from localStorage
    const accessToken = localStorage.getItem('access_token') || 
                       localStorage.getItem('token') || 
                       localStorage.getItem('recruiterToken') || 
                       localStorage.getItem('candidateToken') ||
                       sessionStorage.getItem('access_token') ||
                       sessionStorage.getItem('token') ||
                       sessionStorage.getItem('recruiterToken') ||
                       sessionStorage.getItem('candidateToken');
    
    if (accessToken) {
      apiService.setAuthToken(accessToken);
      console.log('Authentication initialized with token');
    }
  }, []);

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
    setSearchResults([]);

    try {
      const response = await apiService.searchJobs(formData);
      setSearchResults(Array.isArray(response) ? response : []);
    } catch (err) {
      setError(err.message || 'Failed to search jobs');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (job) => {
    try {
      setSelectedJob(job);
      setShowJobModal(true);
      
      // Log the job view for analytics
      console.log('Job viewed:', job.title, 'at', job.company);
      
      // You can also send analytics data to your backend
      // await apiService.logJobView(job.id);
      
    } catch (err) {
      console.error('Error viewing job details:', err);
      setError('Failed to load job details');
    }
  };

  const handleApplyNow = async (job) => {
    console.log('=== APPLY NOW CLICKED ===');
    console.log('Job object:', job);
    console.log('Job ID field:', job.id || job.job_id);
    console.log('Available job fields:', Object.keys(job));
    
    try {
      // Set status for THIS specific job only
      const jobId = job.id || job.job_id;
      setApplicationStatus(prev => ({ ...prev, [jobId]: 'applying' }));
      
      // Check if user is logged in - check all possible token names
      const accessToken = localStorage.getItem('access_token') || 
                         localStorage.getItem('token') || 
                         localStorage.getItem('recruiterToken') || 
                         localStorage.getItem('candidateToken') ||
                         sessionStorage.getItem('access_token') ||
                         sessionStorage.getItem('token') ||
                         sessionStorage.getItem('recruiterToken') ||
                         sessionStorage.getItem('candidateToken');
      
      console.log('=== DEBUGGING AUTHENTICATION ===');
      console.log('Found token:', accessToken ? 'Token exists' : 'No token found');
      console.log('Token value:', accessToken);
      console.log('Token length:', accessToken ? accessToken.length : 0);
      console.log('Token starts with:', accessToken ? accessToken.substring(0, 20) + '...' : 'No token');
      
      // Check all storage locations
      console.log('=== STORAGE CHECK ===');
      console.log('localStorage.access_token:', localStorage.getItem('access_token'));
      console.log('localStorage.token:', localStorage.getItem('token'));
      console.log('localStorage.recruiterToken:', localStorage.getItem('recruiterToken'));
      console.log('localStorage.candidateToken:', localStorage.getItem('candidateToken'));
      console.log('sessionStorage.access_token:', sessionStorage.getItem('access_token'));
      console.log('sessionStorage.token:', sessionStorage.getItem('token'));
      
      if (!accessToken) {
        // Reset status for this job only
        setApplicationStatus(prev => ({ ...prev, [jobId]: 'error' }));
        // Redirect to login page or show login modal
        alert('Please log in to apply for this job');
        // You can implement your own login redirect logic here
        // window.location.href = '/login';
        return;
      }
      
      // Set the authentication token in API headers
      apiService.setAuthToken(accessToken);
      
      // Verify the token is set correctly
      console.log('Authorization header set:', api.defaults.headers.common['Authorization']);
      
      // Test the token by making a simple API call first
      try {
        console.log('=== TESTING TOKEN ===');
        const testResponse = await apiService.getCurrentUser();
        console.log('Token is valid! User:', testResponse);
      } catch (tokenError) {
        console.error('Token validation failed:', tokenError);
        setApplicationStatus(prev => ({ ...prev, [jobId]: 'error' }));
        alert('Your login session has expired. Please log in again.');
        return;
      }
      
      // Get user data from localStorage
      const userData = localStorage.getItem('user_data') || 
                      localStorage.getItem('candidate_data') ||
                      sessionStorage.getItem('user_data') ||
                      sessionStorage.getItem('candidate_data');
      
      let candidateId = 1; // Default fallback
      if (userData) {
        try {
          const parsedUserData = JSON.parse(userData);
          candidateId = parsedUserData.id || parsedUserData.candidate_id || 1;
        } catch (e) {
          console.warn('Could not parse user data:', e);
        }
      }
      
      // Create application with required fields only
      const applicationData = {
        job_id: jobId,  // Use the correct job ID
        status: 'applied'
      };
      
      console.log('Sending application with token:', accessToken ? 'Token present' : 'No token');
      console.log('Application data:', applicationData);
      
      // Send application to backend
      const response = await apiService.createApplication(applicationData);
      
      if (response) {
        setApplicationStatus(prev => ({ ...prev, [jobId]: 'applied' }));
        alert(`Successfully applied for ${job.title} at ${job.company}!`);
        
        // Log the application
        console.log('Job applied:', job.title, 'at', job.company);
        
        // You can also send analytics data to your backend
        // await apiService.logJobApplication(job.id);
        
      } else {
        throw new Error('Failed to submit application');
      }
      
    } catch (err) {
      console.error('Error applying for job:', err);
      const jobId = job.id || job.job_id;
      setApplicationStatus(prev => ({ ...prev, [jobId]: 'error' }));
      setError('Failed to submit application. Please try again.');
    }
  };

  const closeJobModal = () => {
    setShowJobModal(false);
    setSelectedJob(null);
  };

  const formatSalary = (min, max) => {
    if (!min && !max) return 'Salary not specified';
    if (!min) return `Up to $${max?.toLocaleString()}`;
    if (!max) return `From $${min?.toLocaleString()}`;
    return `$${min?.toLocaleString()} - $${max?.toLocaleString()}`;
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'high';
    if (score >= 0.6) return 'medium';
    return 'low';
  };

  const getRatingStars = (rating = 4.5) => {
    // Ensure rating is within valid range (0-5)
    const clampedRating = Math.max(0, Math.min(5, rating));
    const fullStars = Math.floor(clampedRating);
    const hasHalfStar = clampedRating % 1 >= 0.5;
    const emptyStars = Math.max(0, 5 - fullStars - (hasHalfStar ? 1 : 0));
    
    return (
      <div className="rating">
        <div className="stars">
          {'★'.repeat(fullStars)}
          {hasHalfStar && '☆'}
          {'☆'.repeat(emptyStars)}
        </div>
        <span className="rating-text">({clampedRating.toFixed(1)})</span>
      </div>
    );
  };

  const resetFilters = () => {
    setFormData({
      query: '',
      limit: 10,
      apply_filters: true,
      strict_mode: false,
      use_ml_ranking: true
    });
    setSearchResults([]);
    setError('');
  };

  return (
    <div className="job-search">
      {/* Professional Header */}
      <div className="unified-header">
        <div className="header-content">
          <h1 className="header-title"><span className="title-icon">🔍</span> Job Search</h1>
        </div>
        <div className="header-actions">
          <button className="btn-back" onClick={() => window.history.back()}>← Back</button>
        </div>
      </div>

      {/* Clean Search Form */}
      <div className="search-container">
        <form onSubmit={handleSubmit} className="search-form">
          <div className="search-input-group">
            <div className="input-wrapper">
              <input
                type="text"
                name="query"
                value={formData.query}
                onChange={handleInputChange}
                placeholder="Search for jobs (e.g., Python Developer, React Engineer)"
                className="search-input"
                required
              />
              <button type="submit" className="search-button" disabled={loading}>
                {loading ? (
                  <span className="loading-spinner">⏳</span>
                ) : (
                  <span>🔍</span>
                )}
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
        </form>

        {/* Error Display */}
        {error && (
          <div className="error-message">
            <span>{error}</span>
            <button onClick={() => setError('')} className="error-close">×</button>
          </div>
        )}

        {/* Professional Search Results */}
        {searchResults.length > 0 && (
          <div className="search-results">
            <div className="results-header">
              <h2>{searchResults.length} Jobs Found</h2>
              <div className="results-summary">
                <span className="average-score">
                  Average Match: {(searchResults.reduce((acc, job) => acc + job.combined_score, 0) / searchResults.length * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            
            <div className="search-results-grid">
              {searchResults.map((job, index) => (
                <div key={job.job_id || index} className="job-card">
                  <div className="card-header">
                    <div className="job-title-section">
                      <h3 className="job-title">{job.title}</h3>
                      <span className="company-name">{job.company}</span>
                    </div>
                    <div className={`match-score ${getScoreColor(job.combined_score)}`}>
                      {(job.combined_score * 100).toFixed(0)}% Match
                    </div>
                  </div>
                  
                  <div className="card-content">
                    <div className="job-details">
                      <div className="detail-item">
                        <span className="detail-icon">📍</span>
                        <span className="detail-label">Location</span>
                        <span className="detail-value">{job.location}</span>
                      </div>
                      
                      <div className="detail-item">
                        <span className="detail-icon">💰</span>
                        <span className="detail-label">Salary</span>
                        <span className="detail-value">{formatSalary(job.salary_min, job.salary_max)}</span>
                      </div>
                      
                      <div className="detail-item">
                        <span className="detail-icon">⭐</span>
                        <span className="detail-label">Rating</span>
                        <span className="detail-value">{getRatingStars(Math.min(5, 4.2 + (index * 0.1)))}</span>
                      </div>
                    </div>
                    
                    {job.mandatory_skills && job.mandatory_skills.length > 0 && (
                      <div className="skills-section">
                        <span className="skills-label">Required Skills:</span>
                        <div className="skills-list">
                          {job.mandatory_skills.slice(0, 4).map((skill, skillIndex) => (
                            <span key={skillIndex} className="skill-tag">
                              {skill.skill}
                            </span>
                          ))}
                          {job.mandatory_skills.length > 4 && (
                            <span className="skill-tag more-skills">
                              +{job.mandatory_skills.length - 4} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="card-actions">
                    <button 
                      className="btn-view-details"
                      onClick={() => handleViewDetails(job)}
                    >
                      View Details
                    </button>
                    <button 
                      className={`btn-apply-now ${applicationStatus[job.id || job.job_id] === 'applied' ? 'applied' : ''}`}
                      onClick={() => handleApplyNow(job)}
                      disabled={applicationStatus[job.id || job.job_id] === 'applying' || applicationStatus[job.id || job.job_id] === 'applied'}
                    >
                      {applicationStatus[job.id || job.job_id] === 'applying' ? 'Applying...' : 
                       applicationStatus[job.id || job.job_id] === 'applied' ? 'Applied ✓' : 'Apply Now'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Clean Empty State */}
        {!loading && searchResults.length === 0 && !error && (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <h3>Start Your Job Search</h3>
            <p>Enter a job title, skill, or company to find relevant positions</p>
          </div>
        )}
      </div>

      {/* Job Details Modal */}
      {showJobModal && selectedJob && (
        <div className="modal-overlay" onClick={closeJobModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedJob.title}</h2>
              <button className="modal-close" onClick={closeJobModal}>×</button>
            </div>
            <div className="modal-body">
              <div className="job-detail-section">
                <h3>Company</h3>
                <p>{selectedJob.company}</p>
              </div>
              <div className="job-detail-section">
                <h3>Location</h3>
                <p>{selectedJob.location}</p>
              </div>
              <div className="job-detail-section">
                <h3>Salary</h3>
                <p>{formatSalary(selectedJob.salary_min, selectedJob.salary_max)}</p>
              </div>
              <div className="job-detail-section">
                <h3>Job Description</h3>
                <p>{selectedJob.job_description || 'No description available'}</p>
              </div>
              {selectedJob.mandatory_skills && selectedJob.mandatory_skills.length > 0 && (
                <div className="job-detail-section">
                  <h3>Required Skills</h3>
                  <div className="skills-list">
                    {selectedJob.mandatory_skills.map((skill, index) => (
                      <span key={index} className="skill-tag">
                        {skill.skill} ({skill.min_experience || 0} years)
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-view-details" onClick={closeJobModal}>
                Close
              </button>
              <button 
                className="btn-apply-now"
                onClick={() => {
                  handleApplyNow(selectedJob);
                  closeJobModal();
                }}
              >
                Apply Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobSearch; 