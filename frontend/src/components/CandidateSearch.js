import React, { useState } from 'react';
import { apiService } from '../api';
import './CandidateSearch.css';

const CandidateSearch = () => {
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
      const response = await apiService.searchCandidates(formData);
      setSearchResults(response.candidates || []);
    } catch (err) {
      setError(err.message || 'Failed to search candidates');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="candidate-search">
      <div className="search-header">
        <h1>Semantic Candidate Search</h1>
      </div>

      <div className="search-form-container">
        <form onSubmit={handleSubmit} className="search-form">
          <div className="form-group">
            <label htmlFor="query">Search Query:</label>
            <input
              type="text"
              id="query"
              name="query"
              value={formData.query}
              onChange={handleInputChange}
              placeholder="Enter candidate search query (e.g., 'senior Python developer')"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="limit">Limit:</label>
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
                  name="apply_filters"
                  checked={formData.apply_filters}
                  onChange={handleInputChange}
                />
                <span className="checkmark"></span>
                Apply Filters
              </label>
            </div>
            
            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="strict_mode"
                  checked={formData.strict_mode}
                  onChange={handleInputChange}
                />
                <span className="checkmark"></span>
                Strict Mode
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
                <span className="checkmark"></span>
                Use ML Ranking
              </label>
            </div>
          </div>

          <div className="form-actions">
            <button 
              type="submit" 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Searching...' : 'Search Candidates'}
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="error-message">
          <span>{error}</span>
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {searchResults.length > 0 && (
        <div className="search-results">
          <h2>Search Results ({searchResults.length})</h2>
          <div className="search-results-grid">
            {searchResults.map((candidate, index) => (
              <div key={index} className="search-result-card">
                <h3>{candidate.name}</h3>
                <p><strong>Email:</strong> {candidate.email}</p>
                <p><strong>Location:</strong> {candidate.location}</p>
                <p><strong>Domain:</strong> {candidate.domain}</p>
                <p><strong>Salary Range:</strong> {candidate.salary_range}</p>
                {candidate.experience && (
                  <p><strong>Experience:</strong> {candidate.experience}</p>
                )}
                <div className="search-result-score">
                  <span>Relevance Score: {candidate.score}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CandidateSearch; 