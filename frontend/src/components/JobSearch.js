import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../api';
import './JobSearch.css';

const JobSearch = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    query: 'python'
  });
  const [filters, setFilters] = useState({
    location: '',
    company: ''
  });
  const [searchResults, setSearchResults] = useState([]);
  const [filteredResults, setFilteredResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSuccessMessage, setIsSuccessMessage] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [applicationStatus, setApplicationStatus] = useState({});
  const [viewMode, setViewMode] = useState('grid');
  const [showFilters, setShowFilters] = useState(true);
  const [searchTags, setSearchTags] = useState(['python']);
  const [userProfile, setUserProfile] = useState(null);

  useEffect(() => {
    const checkAuthentication = async () => {
      console.log('JobSearch: Checking authentication...');
      
      // Wait longer for the app to initialize auth
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // First check if we have a token
      if (!apiService.isAuthenticated()) {
        console.log('JobSearch: No token found, redirecting to login');
        navigate('/login');
        return;
      }

      try {
        console.log('JobSearch: Token found, validating...');
        // Validate the token by fetching current user
        const user = await apiService.validateToken();
        if (!user) {
          console.log('JobSearch: Token validation failed, redirecting to login');
          // Token is invalid, clear it and redirect to login
          apiService.logout();
          navigate('/login');
        } else {
          console.log('JobSearch: Token validation successful, user:', user.email);
          // Load user profile for application submissions
          setUserProfile(user);
        }
      } catch (error) {
        console.error('JobSearch: Error validating token:', error);
        // Don't immediately logout on network errors, just log the error
        if (error.response && error.response.status === 401) {
          console.log('JobSearch: 401 Unauthorized, clearing token and redirecting');
          apiService.logout();
          navigate('/login');
        } else {
          console.log('JobSearch: Network error during validation, continuing anyway');
          // For now, let's continue even if validation fails due to network issues
        }
      }
    };

    checkAuthentication();
  }, [navigate]);

  // Initial search on component mount
  useEffect(() => {
    if (formData.query.trim()) {
      handleSubmit({ preventDefault: () => {} });
    }
  }, []); // Only run once on mount

  // Handlers for inputs and filters
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const clearFilters = () => {
    setFilters({ location: '', company: '' });
  };

  // Apply client-side filters whenever filters or results change
  useEffect(() => {
    let filtered = Array.isArray(searchResults) ? [...searchResults] : [];
    console.log('Filtering results. Original count:', searchResults.length);
    console.log('Filtered count:', filtered.length);

    if (filters.location) {
      const q = filters.location.toLowerCase();
      filtered = filtered.filter(j => (j.location || '').toLowerCase().includes(q));
    }
    if (filters.company) {
      const q = filters.company.toLowerCase();
      filtered = filtered.filter(j => (j.company || '').toLowerCase().includes(q));
    }

    // Sort by match score (highest first) using unified match_score when present
    filtered.sort((a, b) => {
      const scoreA = (typeof a.match_score === 'number' ? a.match_score : (a.combined_score || 0))
      const scoreB = (typeof b.match_score === 'number' ? b.match_score : (b.combined_score || 0))
      return scoreB - scoreA;
    });

    console.log('Final filtered count:', filtered.length);
    setFilteredResults(filtered);
  }, [filters, searchResults]);

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    if (!formData.query.trim()) return;

    setLoading(true);
    setError('');
    setIsSuccessMessage(false);

    try {
      console.log('Searching for:', formData.query.trim());
      const params = {
        query: formData.query.trim(), // Use query instead of domain for title search
        domain: undefined, // Don't filter by domain unless specified
        location: filters.location || undefined,
        limit: 10,
      };

      const results = await apiService.searchJobs(params);
      console.log('Search results received:', results);
      console.log('Results type:', typeof results);
      console.log('Results length:', Array.isArray(results) ? results.length : 'Not an array');
      
      setSearchResults(results);
      setFilteredResults(results);

      if (!searchTags.includes(formData.query)) {
        setSearchTags(prev => [...prev, formData.query]);
      }
    } catch (error) {
      console.error('Search error:', error);
      setError('Failed to search jobs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const removeSearchTag = (tagToRemove) => {
    setSearchTags(prev => prev.filter(tag => tag !== tagToRemove));
  };

  const handleViewDetails = async (job) => {
    setSelectedJob(job);
    
    // Log the view interaction
    if (userProfile?.id) {
      try {
        await apiService.logJobView(userProfile.id, job.job_id);
        console.log(`✅ Logged VIEWED interaction for job ${job.job_id}`);
      } catch (error) {
        console.warn('⚠️ Failed to log view interaction:', error);
      }
    }
  };

  const closeJobModal = () => {
    setSelectedJob(null);
  };

  const handleApplyNow = async (jobId) => {
    try {
      // Ensure we have user profile before applying
      if (!userProfile?.id) {
        setError('User profile not loaded. Please refresh the page and try again.');
        setIsSuccessMessage(false);
        return;
      }

      const response = await apiService.createApplication({ 
        job_id: jobId,
        candidate_id: userProfile.id,
        status: 'APPLIED'
      });
      
      // Check the response message to determine if it's a new application or already applied
      if (response.message && response.message.includes('already applied')) {
        // Show friendly message for already applied case
        setError('You have already applied for this job!');
        setIsSuccessMessage(true);
      } else {
        // Show success message for new application
        setError('Application submitted successfully!');
        setIsSuccessMessage(true);
      }
      
      // Mark as applied in the UI
      setApplicationStatus(prev => ({
        ...prev,
        [jobId]: 'applied'
      }));
      
      // Clear the message after 3 seconds
      setTimeout(() => {
        setError('');
        setIsSuccessMessage(false);
      }, 3000);
      
    } catch (error) {
      console.error('Application error:', error);
      
      // For other errors, show the generic error message
      setError('Failed to apply for job. Please try again.');
      setIsSuccessMessage(false);
    }
  };

  const getMatchScoreClass = (score) => {
    if (score >= 60) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  };

  const formatSalary = (min, max) => {
    if (!min && !max) return 'Not specified';
    if (!max) return `$${min.toLocaleString()}`;
    if (!min) return `$${max.toLocaleString()}`;
    return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
  };

  const getRatingStars = (rating) => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    return '★'.repeat(fullStars) + (hasHalfStar ? '☆' : '') + '☆'.repeat(emptyStars);
  };

  const renderJobCard = (job, index) => {
    const matchScorePct = typeof job.match_score === 'number' ? Math.round(job.match_score) : Math.round((job.combined_score || 0) * 100);
    const matchClass = getMatchScoreClass(matchScorePct);

    return (
      <div key={job.job_id} className={`job-card ${matchClass}-match`}>
        <div className="card-header">
          <div className="job-title-section">
            <div className="job-title">{job.title}</div>
            <div className="company-name">{job.company}</div>
          </div>
          <div className={`match-score ${matchClass}`}>{matchScorePct}% Match</div>
        </div>
        
        <div className="card-content">
          <div className="job-details">
            <div className="detail-item">
              <span className="detail-label">Location</span>
              <span className="detail-value">{job.location}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Salary</span>
              <span className="detail-value">{formatSalary(job.salary_min, job.salary_max)}</span>
            </div>
          </div>

          <div className="rating">
            <div className="stars">{getRatingStars(Math.min(5, 4.2 + (index * 0.1)))}</div>
            <span className="rating-text">({(4.2 + (index * 0.1)).toFixed(1)})</span>
          </div>

          {job.domain && (
            <div className="skills-section">
              <span className="skills-label">Domain:</span>
              <div className="skills-list">
                <span className="skill-tag">{job.domain}</span>
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
            className={`btn-apply-now ${applicationStatus[job.job_id] === 'applied' ? 'applied' : ''}`}
            onClick={() => handleApplyNow(job.job_id)}
            disabled={applicationStatus[job.job_id] === 'applied'}
          >
            {applicationStatus[job.job_id] === 'applied' ? 'Applied' : 'Apply Now'}
          </button>
        </div>
      </div>
    );
  };

  const renderJobListItem = (job, index) => {
    const matchScore = typeof job.match_score === 'number' ? Math.round(job.match_score) : Math.round((job.combined_score || 0) * 100);
    const matchClass = getMatchScoreClass(matchScore);

    return (
      <div key={job.job_id} className={`job-list-item ${matchClass}-match`}>
        <div className="list-item-header">
          <div className="list-item-title-section">
            <div className="list-job-title">{job.title}</div>
            <div className="list-company-name">{job.company}</div>
          </div>
          <div className={`list-match-score ${matchClass}`}>{matchScore}% Match</div>
        </div>
        
        <div className="list-item-content">
          <div className="list-item-details">
            <div className="list-detail-item">
              <span className="list-detail-label">Location</span>
              <span className="list-detail-value">{job.location}</span>
            </div>
            <div className="list-detail-item">
              <span className="list-detail-label">Salary</span>
              <span className="list-detail-value">{formatSalary(job.salary_min, job.salary_max)}</span>
            </div>
          </div>

          <div className="rating">
            <div className="stars">{getRatingStars(Math.min(5, 4.2 + (index * 0.1)))}</div>
            <span className="rating-text">({(4.2 + (index * 0.1)).toFixed(1)})</span>
          </div>
        </div>

        {job.domain && (
          <div className="list-skills-section">
            <div className="list-skills-list">
              <span className="list-skill-tag">{job.domain}</span>
            </div>
          </div>
        )}

        <div className="list-item-actions">
          <button 
            className="btn-view-details"
            onClick={() => handleViewDetails(job)}
          >
            View Details
          </button>
          <button 
            className={`btn-apply-now ${applicationStatus[job.job_id] === 'applied' ? 'applied' : ''}`}
            onClick={() => handleApplyNow(job.job_id)}
            disabled={applicationStatus[job.job_id] === 'applied'}
          >
            {applicationStatus[job.job_id] === 'applied' ? 'Applied' : 'Apply Now'}
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="job-search">
      {/* Dark Blue Header - Matching Candidate Recommendations */}
      <div className="unified-header">
        <div className="header-content">
          <h1 className="header-title">Job Search</h1>
        </div>
        <div className="header-actions">
          <button className="btn-back" onClick={() => navigate('/candidates-dashboard')}>
            ← Back to Dashboard
          </button>
          <button className="btn-logout" onClick={() => navigate('/login')}>
            Logout
          </button>
        </div>
      </div>

      {/* Main Container - No Gap Layout */}
      <div className="job-search-container">
        {/* Left Column - Search & Filter Jobs */}
        <div className="filters-sidebar">
          <div className="filters-content">
            <h2 className="filters-title">Search & Filter Jobs</h2>
            
            {/* Search Section */}
            <div className="search-section">
              <div className="search-box">
                <input
                  type="text"
                  name="query"
                  value={formData.query}
                  onChange={handleInputChange}
                  className="search-input"
                  placeholder="Search jobs, skills, companies..."
                />
                <button type="submit" className="search-button" disabled={loading} onClick={handleSubmit}>
                  {loading ? (
                    <span className="loading-spinner"></span>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M21.71 20.29L18 16.61A9 9 0 1 0 16.61 18l3.68 3.68a1 1 0 0 0 1.42 0 1 1 0 0 0 0-1.39zM11 18a7 7 0 1 1 7-7 7 7 0 0 1-7 7z"/>
                    </svg>
                  )}
                </button>
              </div>
              
              {searchTags.length > 0 && (
                <div className="search-tags">
                  {searchTags.map((tag, index) => (
                    <span key={index} className="tag">
                      {tag} <span className="remove" onClick={() => removeSearchTag(tag)}>×</span>
                    </span>
                  ))}
                </div>
              )}
            </div>

                         {/* Filters Section */}
             <div className="filters-section">
               <div className="filter-group">
                 <label htmlFor="location">Location</label>
                 <input
                   type="text"
                   id="location"
                   name="location"
                   value={filters.location}
                   onChange={handleFilterChange}
                   className="filter-input"
                   placeholder="e.g., New York"
                 />
               </div>

               <div className="filter-group">
                 <label htmlFor="company">Company</label>
                 <input
                   type="text"
                   id="company"
                   name="company"
                   value={filters.company}
                   onChange={handleFilterChange}
                   className="filter-input"
                   placeholder="e.g., Google"
                 />
               </div>

              <div className="filter-actions">
                <button className="btn-find-jobs" onClick={handleSubmit} disabled={loading}>
                  {loading ? 'Searching...' : 'Find Jobs'}
                </button>
                <button className="btn-clear-filters" onClick={clearFilters}>
                  Clear Filters
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Job Results */}
        <div className="main-content">
                     <div className="results-header">
             <h2 className="results-title">
               Job Results ({filteredResults.length})
               {loading && <span style={{fontSize: '0.9rem', color: '#6b7280', marginLeft: '10px'}}> - Searching...</span>}
             </h2>
           </div>

                     {error && (
             <div className={`error-message ${isSuccessMessage ? 'success' : ''}`}>
               <span>{error}</span>
               <button className="error-close" onClick={() => {
                 setError('');
                 setIsSuccessMessage(false);
               }}>×</button>
             </div>
           )}

          <div className="search-results">
             <div className="view-controls">
               <div className="view-toggle">
                 <button
                   className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
                   onClick={() => setViewMode('grid')}
                 >
                   Grid
                 </button>
                 <button
                   className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
                   onClick={() => setViewMode('list')}
                 >
                   List
                 </button>
               </div>
             </div>

            {viewMode === 'grid' ? (
              <div className="search-results-grid">
                {console.log('Rendering grid with', filteredResults.length, 'results')}
                {filteredResults.map((job, index) => renderJobCard(job, index))}
              </div>
            ) : (
              <div className="search-results-list">
                {console.log('Rendering list with', filteredResults.length, 'results')}
                {filteredResults.map((job, index) => renderJobListItem(job, index))}
              </div>
            )}

                         {loading && (
               <div className="empty-state">
                 <h3>Searching for Jobs...</h3>
                 <p>Please wait while we find the best matches for you</p>
               </div>
             )}
             
             {!loading && filteredResults.length === 0 && !error && (
               <div className="empty-state">
                 <h3>No Jobs Found</h3>
                 <p>Try adjusting your search criteria or filters to find more opportunities</p>
               </div>
             )}
          </div>
        </div>
      </div>

      {selectedJob && (
        <div className="modal-overlay" onClick={closeJobModal}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
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
              {selectedJob.description && (
                <div className="job-detail-section">
                  <h3>Description</h3>
                  <p>{selectedJob.description}</p>
                </div>
              )}
            </div>
                         <div className="modal-footer">
               <button 
                 className={`btn-apply-now ${applicationStatus[selectedJob.job_id] === 'applied' ? 'applied' : ''}`}
                 onClick={() => handleApplyNow(selectedJob.job_id)}
                 disabled={applicationStatus[selectedJob.job_id] === 'applied'}
               >
                 {applicationStatus[selectedJob.job_id] === 'applied' ? 'Applied' : 'Apply Now'}
               </button>
             </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobSearch;
