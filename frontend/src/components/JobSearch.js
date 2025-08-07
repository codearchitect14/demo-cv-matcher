import React, { useState } from 'react';
import { apiService } from '../api';
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
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    return (
      <div className="rating">
        <div className="stars">
          {'★'.repeat(fullStars)}
          {hasHalfStar && '☆'}
          {'☆'.repeat(emptyStars)}
        </div>
        <span className="rating-text">({rating})</span>
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

  const browseAllJobs = () => {
    // Navigate to all jobs page or expand search
    console.log('Browse all jobs clicked');
  };

  return (
    <div className="job-search">
      {/* Header Section - Dark Blue Background */}
      <div className="search-header">
        <div className="header-content">
          <h1>Semantic Job Search</h1>
          <p>Find your perfect job with AI-powered matching</p>
          <div className="header-actions">
            <button className="btn-how-it-works">How it works</button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="main-content">
        {/* Search Form Container */}
        <div className="search-form-container">
          <form onSubmit={handleSubmit} className="search-form">
            <div className="form-group">
              <label htmlFor="query">Search Query</label>
              <input
                type="text"
                id="query"
                name="query"
                value={formData.query}
                onChange={handleInputChange}
                placeholder="Enter job search query (e.g., 'Python developer remote')"
                required
              />
            </div>

            <div className="form-row">
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="strict_mode"
                    checked={formData.strict_mode}
                    onChange={handleInputChange}
                  />
                  Exact Match Only
                </label>
              </div>
              
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="apply_filters"
                    checked={formData.apply_filters}
                    onChange={handleInputChange}
                  />
                  Include Remote Positions
                </label>
              </div>
              
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="use_ml_ranking"
                    checked={formData.use_ml_ranking}
                    onChange={handleInputChange}
                  />
                  Show Entry-Level Jobs
                </label>
              </div>
              
              <div className="form-group">
                <label htmlFor="limit">Results Limit</label>
                <select
                  id="limit"
                  name="limit"
                  value={formData.limit}
                  onChange={handleInputChange}
                >
                  <option value={5}>5 results</option>
                  <option value={10}>10 results</option>
                  <option value={15}>15 results</option>
                  <option value={20}>20 results</option>
                </select>
              </div>
            </div>

            <div className="form-actions">
              <button 
                type="submit" 
                className="btn-primary"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="loading-spinner"></span>
                    Searching...
                  </>
                ) : (
                  <>
                    <span className="search-icon">🔍</span>
                    Search Jobs
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
            <button onClick={() => setError('')} className="error-close">×</button>
          </div>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="search-results">
            <div className="results-header">
              <h2>Python Developer Roles ({searchResults.length} matches)</h2>
              <div className="results-summary">
                <span className="summary-item">
                  <span className="summary-icon">📊</span>
                  Average Score: {(searchResults.reduce((acc, job) => acc + job.combined_score, 0) / searchResults.length * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            
            <div className="search-results-grid">
              {searchResults.map((job, index) => (
                <div key={job.job_id || index} className="search-result-card">
                  <div className="card-header">
                    <h3 className="job-title">{job.title} @ {job.company}</h3>
                    <div className={`score-badge ${getScoreColor(job.combined_score)}`}>
                      {(job.combined_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  
                  <div className="card-content">
                    {/* Rating and Location */}
                    <div className="job-info">
                      {getRatingStars(4.2 + (index * 0.2))}
                      
                      <div className="info-item">
                        <span className="info-icon">🏙️</span>
                        <span className="info-label">Location:</span>
                        <span className="info-value">{job.location}</span>
                      </div>
                      
                      <div className="info-item">
                        <span className="info-icon">💰</span>
                        <span className="info-label">Salary:</span>
                        <span className="info-value">{formatSalary(job.salary_min, job.salary_max)}</span>
                      </div>
                      
                      <div className="info-item">
                        <span className="info-icon">✅</span>
                        <span className="info-label">Experience:</span>
                        <span className="info-value">3+ years experience</span>
                      </div>
                    </div>
                    
                    {/* Skills Tags */}
                    <div className="skills-tags">
                      <span className="skill-tag">🐍 Python</span>
                      <span className="skill-tag">⚡ Django</span>
                      <span className="skill-tag">🗄️ PostgreSQL</span>
                      <span className="skill-tag">☁️ AWS</span>
                    </div>
                  </div>
                  
                  <div className="card-actions">
                    <button className="btn-view">View Details</button>
                    <button className="btn-apply">Apply Now</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
  
        {/* Empty State */}
        {!loading && searchResults.length === 0 && !error && (
          <div className="no-results">
            <div className="no-results-icon">🔍</div>
            <h3>No matching jobs found</h3>
            <p>
              We couldn't find jobs matching your criteria. Try:
            </p>
            <div className="no-results-suggestions">
              <ul>
                <li>Broadening your location preferences</li>
                <li>Adjusting experience level filters</li>
                <li>Searching for related terms</li>
              </ul>
            </div>
            <div className="empty-state-actions">
              <button className="btn-reset-filters" onClick={resetFilters}>
                Reset Filters
              </button>
              <button className="btn-browse-all" onClick={browseAllJobs}>
                Browse All Jobs
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobSearch; 