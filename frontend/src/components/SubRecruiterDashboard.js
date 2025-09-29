import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './SubRecruiterDashboard.css';

const SubRecruiterDashboard = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCandidateModal, setShowCandidateModal] = useState(false);

  // Load assigned jobs on component mount (no authentication required)
  useEffect(() => {
    fetchAssignedJobs();
  }, []);

  const fetchAssignedJobs = async () => {
    try {
      setLoading(true);
      setError(''); // Clear any previous errors
      
      console.log('Fetching assigned jobs (public endpoint)');
      
      const response = await fetch('http://localhost:8000/api/v1/recruiter/assigned-jobs', {
        headers: {
          'Content-Type': 'application/json'
        },
        signal: AbortSignal.timeout(30000) // 30 second timeout
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error(`Failed to fetch assigned jobs: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      console.log('Response data:', data);
      setJobs(data.jobs || []);
    } catch (err) {
      console.error('Error fetching jobs:', err);
      setError(`Failed to load assigned jobs: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchJobCandidates = async (jobId) => {
    try {
      setError(''); // Clear any previous errors
      
      console.log('Fetching candidates for job:', jobId);
      
      const response = await fetch(`http://localhost:8000/api/v1/recruiter/job-candidates/${jobId}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('Candidates response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Candidates response error:', errorText);
        throw new Error(`Failed to fetch candidates: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      console.log('Candidates data:', data);
      setCandidates(data.candidates || []);
    } catch (err) {
      console.error('Error fetching candidates:', err);
      setError(`Failed to load candidates: ${err.message}`);
    }
  };

  const updateCandidateStatus = async (candidateId, newStatus) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/recruiter/update-candidate-status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          candidate_id: candidateId,
          job_id: selectedJob.id,
          status: newStatus
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update status');
      }

      // Refresh candidates list
      fetchJobCandidates(selectedJob.id);
      setShowCandidateModal(false);
    } catch (err) {
      setError('Failed to update candidate status');
      console.error('Error updating status:', err);
    }
  };

  const handleJobClick = (job) => {
    setSelectedJob(job);
    fetchJobCandidates(job.id);
  };

  const handleCandidateClick = (candidate) => {
    setSelectedCandidate(candidate);
    setShowCandidateModal(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'APPLIED': return '#3b82f6';
      case 'INTERVIEW_SCHEDULED': return '#8b5cf6';
      case 'REJECTED': return '#ef4444';
      case 'HIRED': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getStatusCounts = (job) => {
    // The backend already provides the counts in the applications object
    return {
      APPLIED: job.applications?.APPLIED || 0,
      INTERVIEW_SCHEDULED: job.applications?.INTERVIEW_SCHEDULED || 0,
      REJECTED: job.applications?.REJECTED || 0,
      HIRED: job.applications?.HIRED || 0
    };
  };

  if (loading) {
    return (
      <div className="sub-recruiter-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading your assigned jobs...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="sub-recruiter-dashboard">
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={fetchAssignedJobs} className="btn-retry">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="sub-recruiter-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1>Recruiter Dashboard</h1>
          <p>Manage your assigned jobs and candidates</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-logout"
            onClick={() => {
              localStorage.removeItem('recruiterToken');
              localStorage.removeItem('recruiterUser');
              navigate('/recruiter-login');
            }}
          >
            Logout
          </button>
        </div>
      </div>

      {!selectedJob ? (
        <div className="jobs-section">
          <h2>Your Assigned Jobs</h2>
          {jobs.length === 0 ? (
            <div className="no-jobs">
              <p>No jobs assigned to you yet.</p>
            </div>
          ) : (
            <div className="jobs-grid">
              {jobs.map(job => {
                const statusCounts = getStatusCounts(job);
                const totalApplicants = Object.values(statusCounts).reduce((sum, count) => sum + count, 0);
                
                return (
                  <div key={job.id} className="job-card" onClick={() => handleJobClick(job)}>
                    <div className="job-header">
                      <h3>{job.title}</h3>
                      <span className="job-location">{job.location}</span>
                    </div>
                    <div className="job-stats">
                      <div className="stat-item">
                        <span className="stat-label">Total Applicants</span>
                        <span className="stat-value">{totalApplicants}</span>
                      </div>
                      <div className="status-breakdown">
                        {Object.entries(statusCounts).map(([status, count]) => (
                          count > 0 && (
                            <div key={status} className="status-item">
                              <span 
                                className="status-dot" 
                                style={{backgroundColor: getStatusColor(status)}}
                              ></span>
                              <span className="status-text">{status.replace('_', ' ')}: {count}</span>
                            </div>
                          )
                        ))}
                      </div>
                    </div>
                    <div className="job-footer">
                      <span className="job-company">{job.company}</span>
                      <span className="job-date">Posted: {new Date(job.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="candidates-section">
          <div className="section-header">
            <button 
              className="btn-back"
              onClick={() => setSelectedJob(null)}
            >
              ← Back to Jobs
            </button>
            <h2>Candidates for: {selectedJob.title}</h2>
          </div>

          {candidates.length === 0 ? (
            <div className="no-candidates">
              <p>No candidates have applied for this job yet.</p>
            </div>
          ) : (
            <div className="candidates-table-container">
              <table className="candidates-table">
                <thead>
                  <tr>
                    <th>Candidate Name</th>
                    <th>Email</th>
                    <th>Location</th>
                    <th>Experience</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map(candidate => (
                    <tr key={candidate.id} onClick={() => handleCandidateClick(candidate)}>
                      <td>
                        <div className="candidate-name">
                          <strong>{candidate.name}</strong>
                        </div>
                      </td>
                      <td>{candidate.email}</td>
                      <td>{candidate.location || 'N/A'}</td>
                      <td>{candidate.total_experience_years ? `${candidate.total_experience_years} years` : 'N/A'}</td>
                      <td>
                        <span 
                          className="status-badge"
                          style={{backgroundColor: getStatusColor(candidate.status)}}
                        >
                          {candidate.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="btn-view"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCandidateClick(candidate);
                          }}
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Candidate Details Modal */}
      {showCandidateModal && selectedCandidate && (
        <div className="modal-overlay" onClick={() => setShowCandidateModal(false)}>
          <div className="candidate-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Candidate Details</h3>
              <button 
                className="btn-close"
                onClick={() => setShowCandidateModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-content">
              <div className="candidate-info">
                <div className="info-row">
                  <label>Name:</label>
                  <span>{selectedCandidate.name}</span>
                </div>
                <div className="info-row">
                  <label>Email:</label>
                  <span>{selectedCandidate.email}</span>
                </div>
                <div className="info-row">
                  <label>Location:</label>
                  <span>{selectedCandidate.location || 'N/A'}</span>
                </div>
                <div className="info-row">
                  <label>Total Experience:</label>
                  <span>{selectedCandidate.total_experience_years ? `${selectedCandidate.total_experience_years} years` : 'N/A'}</span>
                </div>
                <div className="info-row">
                  <label>Current Status:</label>
                  <span 
                    className="status-badge"
                    style={{backgroundColor: getStatusColor(selectedCandidate.status)}}
                  >
                    {selectedCandidate.status.replace('_', ' ')}
                  </span>
                </div>
                {selectedCandidate.assessment_score && (
                  <div className="info-row">
                    <label>Assessment Score:</label>
                    <span>{selectedCandidate.assessment_score}%</span>
                  </div>
                )}
              </div>

              <div className="modal-actions">
                <h4>Update Status:</h4>
                <div className="status-buttons">
                  {['APPLIED', 'INTERVIEW_SCHEDULED', 'REJECTED', 'HIRED'].map(status => (
                    <button
                      key={status}
                      className={`btn-status ${selectedCandidate.status === status ? 'active' : ''}`}
                      onClick={() => updateCandidateStatus(selectedCandidate.id, status)}
                    >
                      {status.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubRecruiterDashboard;
