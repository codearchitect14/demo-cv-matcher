import React, { useState } from 'react';
import { apiService } from '../api';
import './JobRecommendations.css';

const JobRecommendations = () => {
  const [formData, setFormData] = useState({
    candidate_id: '',
    limit: 10,
    apply_filters: true,
    strict_mode: false,
    use_ml_ranking: true
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setRecommendations([]);

    try {
      const response = await apiService.getJobRecommendations(formData);
      setRecommendations(response.recommendations || []);
    } catch (err) {
      setError(err.message || 'Failed to get job recommendations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="job-recommendations">
      <div className="recommendations-header">
        <h1>Job Recommendations for Candidate</h1>
      </div>

      <div className="recommendations-form-container">
        <form onSubmit={handleSubmit} className="recommendations-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="candidate_id">Candidate ID:</label>
              <input
                type="text"
                id="candidate_id"
                name="candidate_id"
                value={formData.candidate_id}
                onChange={handleInputChange}
                placeholder="Enter candidate ID"
                required
              />
            </div>
            
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
          </div>

          <div className="form-row">
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
          </div>

          <div className="form-actions">
            <button 
              type="submit" 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Getting Recommendations...' : 'Get Job Recommendations'}
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

      {recommendations.length > 0 && (
        <div className="recommendations-results">
          <h2>Recommended Jobs ({recommendations.length})</h2>
          <div className="recommendations-grid">
            {recommendations.map((job, index) => (
              <div key={index} className="recommendation-card">
                <h3>{job.title}</h3>
                <p><strong>Company:</strong> {job.company}</p>
                <p><strong>Location:</strong> {job.location}</p>
                <p><strong>Salary Range:</strong> {job.salary_range}</p>
                <p><strong>Domain:</strong> {job.domain}</p>
                {job.description && (
                  <p><strong>Description:</strong> {job.description}</p>
                )}
                <div className="recommendation-score">
                  <span>Match Score: {job.score}%</span>
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