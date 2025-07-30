import React, { useState, useEffect } from 'react';
import apiService from '../api';

const CandidateRecommendations = ({ jobId }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [useMlRanking, setUseMlRanking] = useState(true);

  const fetchRecommendations = async () => {
    if (!jobId) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await apiService.getCandidateRecommendations(jobId, useMlRanking);
      setRecommendations(response.recommendations || []);
    } catch (error) {
      setError(`Error fetching recommendations: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [jobId, useMlRanking]);

  const handleAccept = async (candidateId) => {
    try {
      // Find the application for this candidate and job
      const applications = await apiService.getJobApplications(jobId);
      const application = applications.find(app => app.candidate_id === candidateId);
      
      if (application) {
        await apiService.updateApplicationStatus(application.id, 'Accepted');
        alert('Application accepted!');
      } else {
        alert('No application found for this candidate');
      }
      
      fetchRecommendations(); // Refresh recommendations
    } catch (error) {
      alert(`Error accepting: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleReject = async (candidateId) => {
    try {
      // Find the application for this candidate and job
      const applications = await apiService.getJobApplications(jobId);
      const application = applications.find(app => app.candidate_id === candidateId);
      
      if (application) {
        await apiService.updateApplicationStatus(application.id, 'Rejected');
        alert('Application rejected!');
      } else {
        alert('No application found for this candidate');
      }
      
      fetchRecommendations(); // Refresh recommendations
    } catch (error) {
      alert(`Error rejecting: ${error.response?.data?.detail || error.message}`);
    }
  };

  if (!jobId) {
    return <div className="card"><h3>Please select a job to view candidate recommendations</h3></div>;
  }

  return (
    <div className="card">
      <h3>Candidate Recommendations</h3>
      
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
        <div className="alert alert-info">No candidate recommendations found.</div>
      ) : (
        <div className="grid">
          {recommendations.map((candidate, index) => (
            <div key={candidate.id || index} className="card" style={{ margin: '10px 0' }}>
              <h4>{candidate.name}</h4>
              <p><strong>Location:</strong> {candidate.location}</p>
              <p><strong>Domain:</strong> {candidate.domain}</p>
              <p><strong>Expected Salary:</strong> ${candidate.expected_salary_min?.toLocaleString()} - ${candidate.expected_salary_max?.toLocaleString()}</p>
              {candidate.similarity_score && (
                <p><strong>Match Score:</strong> {(candidate.similarity_score * 100).toFixed(1)}%</p>
              )}
              {candidate.ml_score && (
                <p><strong>ML Score:</strong> {(candidate.ml_score * 100).toFixed(1)}%</p>
              )}
              <p><strong>Summary:</strong> {candidate.summary}</p>
              
              {candidate.experiences && candidate.experiences.length > 0 && (
                <div>
                  <strong>Skills:</strong>
                  <ul>
                    {candidate.experiences.map((exp, expIndex) => (
                      <li key={expIndex}>
                        {exp.skill} ({exp.years} years) - {exp.description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div style={{ marginTop: '15px' }}>
                <button 
                  className="btn btn-success" 
                  onClick={() => handleAccept(candidate.id)}
                  style={{ marginRight: '10px' }}
                >
                  Accept
                </button>
                <button 
                  className="btn btn-warning" 
                  onClick={() => handleReject(candidate.id)}
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

export default CandidateRecommendations; 