import React, { useState, useEffect } from 'react';
import apiService from '../api';

const AdminDashboard = () => {
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  const fetchStats = async () => {
    setLoading(true);
    setError('');
    
    try {
      const [
        jobsWithoutApplicants,
        candidatesZeroVisibility,
        skillGapAnalysis,
        applicationStats,
        jobPerformance,
        systemHealth,
        systemStats
      ] = await Promise.all([
        apiService.getJobsWithoutApplicants(),
        apiService.getCandidatesZeroVisibility(),
        apiService.getSkillGapAnalysis(),
        apiService.getApplicationStats(),
        apiService.getJobPerformance(),
        apiService.getSystemHealth(),
        apiService.getSystemStats()
      ]);

      setStats({
        jobsWithoutApplicants,
        candidatesZeroVisibility,
        skillGapAnalysis,
        applicationStats,
        jobPerformance,
        systemHealth,
        systemStats
      });
    } catch (error) {
      setError(`Error fetching stats: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleGenerateEmbeddings = async () => {
    try {
      await apiService.generateEmbeddings();
      alert('Embeddings generated successfully!');
    } catch (error) {
      alert(`Error generating embeddings: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleRetrainModels = async () => {
    try {
      await apiService.retrainModels();
      alert('Models retrained successfully!');
    } catch (error) {
      alert(`Error retraining models: ${error.response?.data?.detail || error.message}`);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div className="container">
      <h2>Admin Dashboard</h2>
      
      {error && (
        <div className="error-message">
          <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <button 
          className="btn btn-primary" 
          onClick={fetchStats}
          style={{ marginRight: '10px' }}
        >
          Refresh Stats
        </button>
        <button 
          className="btn btn-success" 
          onClick={handleGenerateEmbeddings}
          style={{ marginRight: '10px' }}
        >
          Generate Embeddings
        </button>
        <button 
          className="btn btn-warning" 
          onClick={handleRetrainModels}
        >
          Retrain Models
        </button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <button 
          className={`btn ${activeTab === 'overview' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('overview')}
          style={{ marginRight: '10px' }}
        >
          Overview
        </button>
        <button 
          className={`btn ${activeTab === 'analytics' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('analytics')}
          style={{ marginRight: '10px' }}
        >
          Analytics
        </button>
        <button 
          className={`btn ${activeTab === 'system' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('system')}
        >
          System
        </button>
      </div>

      {activeTab === 'overview' && (
        <div>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-number">
                {stats.applicationStats?.total_applications || 0}
              </div>
              <div className="stat-label">Total Applications</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">
                {stats.jobsWithoutApplicants?.length || 0}
              </div>
              <div className="stat-label">Jobs Without Applicants</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">
                {stats.candidatesZeroVisibility?.length || 0}
              </div>
              <div className="stat-label">Candidates Zero Visibility</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">
                {stats.systemStats?.total_candidates || 0}
              </div>
              <div className="stat-label">Total Candidates</div>
            </div>
          </div>

          <div className="grid">
            <div className="card">
              <h3>System Health</h3>
              <p><strong>Status:</strong> {stats.systemHealth?.status || 'Unknown'}</p>
              <p><strong>Service:</strong> {stats.systemHealth?.service || 'Unknown'}</p>
              <p><strong>Timestamp:</strong> {stats.systemHealth?.timestamp || 'Unknown'}</p>
            </div>

            <div className="card">
              <h3>Application Statistics</h3>
              <p><strong>Total Applications:</strong> {stats.applicationStats?.total_applications || 0}</p>
              <p><strong>Pending Applications:</strong> {stats.applicationStats?.pending_applications || 0}</p>
              <p><strong>Accepted Applications:</strong> {stats.applicationStats?.accepted_applications || 0}</p>
              <p><strong>Rejected Applications:</strong> {stats.applicationStats?.rejected_applications || 0}</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'analytics' && (
        <div>
          <div className="card">
            <h3>Jobs Without Applicants</h3>
            {stats.jobsWithoutApplicants?.length > 0 ? (
              <ul>
                {stats.jobsWithoutApplicants.map((job, index) => (
                  <li key={index}>
                    <strong>{job.title}</strong> - {job.company} ({job.location})
                  </li>
                ))}
              </ul>
            ) : (
              <p>All jobs have applicants!</p>
            )}
          </div>

          <div className="card">
            <h3>Candidates with Zero Visibility</h3>
            {stats.candidatesZeroVisibility?.length > 0 ? (
              <ul>
                {stats.candidatesZeroVisibility.map((candidate, index) => (
                  <li key={index}>
                    <strong>{candidate.name}</strong> - {candidate.location} ({candidate.domain})
                  </li>
                ))}
              </ul>
            ) : (
              <p>All candidates have visibility!</p>
            )}
          </div>

          <div className="card">
            <h3>Skill Gap Analysis</h3>
            {stats.skillGapAnalysis?.demand_vs_supply ? (
              <div>
                <h4>Top Skills in Demand:</h4>
                <ul>
                  {stats.skillGapAnalysis.demand_vs_supply.slice(0, 5).map((skill, index) => (
                    <li key={index}>
                      {skill.skill}: {skill.demand} demand vs {skill.supply} supply
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p>No skill gap data available</p>
            )}
          </div>

          <div className="card">
            <h3>Job Performance Metrics</h3>
            {stats.jobPerformance?.top_performing_jobs ? (
              <div>
                <h4>Top Performing Jobs:</h4>
                <ul>
                  {stats.jobPerformance.top_performing_jobs.slice(0, 5).map((job, index) => (
                    <li key={index}>
                      <strong>{job.title}</strong> - {job.views} views, {job.applications} applications
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p>No performance data available</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'system' && (
        <div>
          <div className="card">
            <h3>System Statistics</h3>
            <p><strong>Total Candidates:</strong> {stats.systemStats?.total_candidates || 0}</p>
            <p><strong>Total Jobs:</strong> {stats.systemStats?.total_jobs || 0}</p>
            <p><strong>Total Applications:</strong> {stats.systemStats?.total_applications || 0}</p>
            <p><strong>Total Interactions:</strong> {stats.systemStats?.total_interactions || 0}</p>
            <p><strong>Active Embeddings:</strong> {stats.systemStats?.active_embeddings || 0}</p>
            <p><strong>ML Models Status:</strong> {stats.systemStats?.ml_models_status || 'Unknown'}</p>
          </div>

          <div className="card">
            <h3>System Actions</h3>
            <p>Use the buttons above to:</p>
            <ul>
              <li><strong>Generate Embeddings:</strong> Create embeddings for all candidates and jobs</li>
              <li><strong>Retrain Models:</strong> Retrain ML models with latest interaction data</li>
              <li><strong>Refresh Stats:</strong> Update all dashboard statistics</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard; 