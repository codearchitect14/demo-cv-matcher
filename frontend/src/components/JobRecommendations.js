import React, { useState, useEffect } from 'react';
import apiService from '../api';

const JobRecommendations = ({ candidateId }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [useMlRanking, setUseMlRanking] = useState(true);

  const fetchRecommendations = async () => {
    if (!candidateId) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await apiService.getJobRecommendations(candidateId, useMlRanking);
      setRecommendations(response.recommendations || []);
    } catch (error) {
      setError(`Error fetching recommendations: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [candidateId, useMlRanking]);

  const handleApply = async (jobId) => {
    try {
      await apiService.applyForJob({
        candidate_id: candidateId,
        job_id: jobId
      });
      
      // Log interaction
      await apiService.logInteraction({
        candidate_id: candidateId,
        job_id: jobId,
        interaction_type: 'Applied'
      });
      
      alert('Application submitted successfully!');
      fetchRecommendations(); // Refresh recommendations
    } catch (error) {
      alert(`Error applying: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleReject = async (jobId) => {
    try {
      await apiService.logInteraction({
        candidate_id: candidateId,
        job_id: jobId,
        interaction_type: 'Rejected'
      });
      
      alert('Job rejected');
      fetchRecommendations(); // Refresh recommendations
    } catch (error) {
      alert(`Error rejecting: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleView = async (jobId) => {
    try {
      await apiService.logInteraction({
        candidate_id: candidateId,
        job_id: jobId,
        interaction_type: 'View'
      });
    } catch (error) {
      console.error('Error logging view:', error);
    }
  };

  if (!candidateId) {
    return <div className="card"><h3>Please select a candidate to view recommendations</h3></div>;
  }

  return (
    <div className="card">
      <h3>Job Recommendations</h3>
      
      <div style={{ marginBottom: '15px' }}>
        <label>
          <input
            type="checkbox"
            checked={useMlRanking}
            onChange={(e) => setUseMlRanking(e.target.checked)}
          />
          Use ML Ranking
        </label>
        <button 
          className="btn btn-primary" 
          onClick={fetchRecommendations}
          disabled={loading}
          style={{ marginLeft: '10px' }}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading">Loading recommendations...</div>
      ) : recommendations.length === 0 ? (
        <div className="alert alert-info">No job recommendations found.</div>
      ) : (
        <div className="grid">
          {recommendations.map((job, index) => (
            <div key={job.id || index} className="card" style={{ margin: '10px 0' }}>
              <h4>{job.title}</h4>
              <p><strong>Company:</strong> {job.company || 'Unknown'}</p>
              <p><strong>Location:</strong> {job.location}</p>
              <p><strong>Domain:</strong> {job.domain}</p>
              <p><strong>Salary:</strong> ${job.salary_min?.toLocaleString()} - ${job.salary_max?.toLocaleString()}</p>
              <p><strong>Required Experience:</strong> {job.total_years_required} years</p>
              {job.similarity_score && (
                <p><strong>Match Score:</strong> {(job.similarity_score * 100).toFixed(1)}%</p>
              )}
              {job.ml_score && (
                <p><strong>ML Score:</strong> {(job.ml_score * 100).toFixed(1)}%</p>
              )}
              <p><strong>Description:</strong> {job.description}</p>
              
              <div style={{ marginTop: '15px' }}>
                <button 
                  className="btn btn-primary" 
                  onClick={() => handleView(job.id)}
                  style={{ marginRight: '10px' }}
                >
                  View Details
                </button>
                <button 
                  className="btn btn-success" 
                  onClick={() => handleApply(job.id)}
                  style={{ marginRight: '10px' }}
                >
                  Apply
                </button>
                <button 
                  className="btn btn-warning" 
                  onClick={() => handleReject(job.id)}
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default JobRecommendations; 