import React, { useState, useEffect } from 'react';
import './ApplicationsManagement.css';

const ApplicationsManagement = () => {
  const [applications, setApplications] = useState([]);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [filters, setFilters] = useState({
    job_id: '',
    candidate_id: '',
    status: ''
  });
  const [formData, setFormData] = useState({
    candidate_id: '',
    job_id: '',
    status: 'applied'
  });

  const fetchApplicationDetails = async (applicationId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/applications/${applicationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedApplication(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch application details: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to fetch application details');
    }
  };

  const fetchJobApplications = async (jobId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/applications/job/${jobId}/applications`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setApplications(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch job applications: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to fetch job applications');
    }
  };

  const fetchCandidateApplications = async (candidateId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/applications/candidate/${candidateId}/applications`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setApplications(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch candidate applications: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to fetch candidate applications');
    }
  };

  const handleCreateApplication = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/applications/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });
      if (response.ok) {
        const data = await response.json();
        setMessage('Application created successfully');
        setFormData({
          candidate_id: '',
          job_id: '',
          status: 'applied'
        });
        setShowForm(false);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to create application: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to create application');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateApplicationStatus = async (applicationId, newStatus) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/applications/${applicationId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: newStatus })
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedApplication(data);
        setMessage('Application status updated successfully');
        // Update the application in the list
        setApplications(prev => prev.map(app => 
          app.id === applicationId ? { ...app, status: newStatus } : app
        ));
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to update application status: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to update application status');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterApplications = () => {
    if (filters.job_id) {
      fetchJobApplications(filters.job_id);
    } else if (filters.candidate_id) {
      fetchCandidateApplications(filters.candidate_id);
    } else {
      setError('Please enter either a Job ID or Candidate ID to filter applications');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'applied': return '#ff9800';
      case 'reviewing': return '#2196f3';
      case 'interviewed': return '#9c27b0';
      case 'accepted': return '#4caf50';
      case 'rejected': return '#f44336';
      default: return '#757575';
    }
  };

  return (
    <div className="applications-dashboard">
      <div className="dashboard-header">
        <h1>Applications Management</h1>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setShowForm(true)}
          >
            Create Application
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {message && (
        <div className="success-message">
          {message}
          <button onClick={() => setMessage('')}>×</button>
        </div>
      )}

      <div className="dashboard-content">
        <div className="filters-section">
          <h2>Filter Applications</h2>
          <div className="filters">
            <div className="filter-group">
              <label>Job ID:</label>
              <input
                type="number"
                value={filters.job_id}
                onChange={(e) => setFilters({...filters, job_id: e.target.value})}
                placeholder="Enter Job ID"
              />
            </div>
            <div className="filter-group">
              <label>Candidate ID:</label>
              <input
                type="number"
                value={filters.candidate_id}
                onChange={(e) => setFilters({...filters, candidate_id: e.target.value})}
                placeholder="Enter Candidate ID"
              />
            </div>
            <div className="filter-group">
              <label>Status:</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({...filters, status: e.target.value})}
              >
                <option value="">All Statuses</option>
                <option value="applied">Applied</option>
                <option value="reviewing">Reviewing</option>
                <option value="interviewed">Interviewed</option>
                <option value="accepted">Accepted</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <button 
              className="btn btn-secondary"
              onClick={handleFilterApplications}
            >
              Filter Applications
            </button>
          </div>
        </div>

        <div className="applications-list">
          <h2>Applications ({applications.length})</h2>
          {loading ? (
            <div className="loading">Loading applications...</div>
          ) : (
            <div className="applications-grid">
              {applications.map(application => (
                <div 
                  key={application.id} 
                  className={`application-card ${selectedApplication?.id === application.id ? 'selected' : ''}`}
                  onClick={() => fetchApplicationDetails(application.id)}
                >
                  <div className="application-header">
                    <h3>Application #{application.id}</h3>
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(application.status) }}
                    >
                      {application.status}
                    </span>
                  </div>
                  <p><strong>Candidate:</strong> {application.candidate?.name || 'N/A'}</p>
                  <p><strong>Job:</strong> {application.job?.title || 'N/A'}</p>
                  <p><strong>Applied:</strong> {new Date(application.created_at).toLocaleDateString()}</p>
                  <div className="application-actions">
                    <select
                      value={application.status}
                      onChange={(e) => {
                        e.stopPropagation();
                        handleUpdateApplicationStatus(application.id, e.target.value);
                      }}
                      className="status-select"
                    >
                      <option value="applied">Applied</option>
                      <option value="reviewing">Reviewing</option>
                      <option value="interviewed">Interviewed</option>
                      <option value="accepted">Accepted</option>
                      <option value="rejected">Rejected</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedApplication && (
          <div className="application-details">
            <h2>Application Details</h2>
            <div className="detail-section">
              <h3>Basic Information</h3>
              <p><strong>Application ID:</strong> {selectedApplication.id}</p>
              <p><strong>Status:</strong> 
                <span 
                  className="status-badge"
                  style={{ backgroundColor: getStatusColor(selectedApplication.status) }}
                >
                  {selectedApplication.status}
                </span>
              </p>
              <p><strong>Applied Date:</strong> {new Date(selectedApplication.created_at).toLocaleDateString()}</p>
              <p><strong>Last Updated:</strong> {new Date(selectedApplication.updated_at).toLocaleDateString()}</p>
            </div>

            <div className="detail-section">
              <h3>Candidate Information</h3>
              {selectedApplication.candidate ? (
                <>
                  <p><strong>Name:</strong> {selectedApplication.candidate.name}</p>
                  <p><strong>Email:</strong> {selectedApplication.candidate.email}</p>
                  <p><strong>Location:</strong> {selectedApplication.candidate.location}</p>
                  <p><strong>Domain:</strong> {selectedApplication.candidate.domain}</p>
                  <p><strong>Expected Salary:</strong> ${selectedApplication.candidate.expected_salary_min} - ${selectedApplication.candidate.expected_salary_max}</p>
                </>
              ) : (
                <p>Candidate information not available</p>
              )}
            </div>

            <div className="detail-section">
              <h3>Job Information</h3>
              {selectedApplication.job ? (
                <>
                  <p><strong>Title:</strong> {selectedApplication.job.title}</p>
                  <p><strong>Company:</strong> {selectedApplication.job.company}</p>
                  <p><strong>Location:</strong> {selectedApplication.job.location}</p>
                  <p><strong>Domain:</strong> {selectedApplication.job.domain}</p>
                  <p><strong>Salary Range:</strong> ${selectedApplication.job.salary_min} - ${selectedApplication.job.salary_max}</p>
                  <p><strong>Experience Required:</strong> {selectedApplication.job.total_years_required} years</p>
                </>
              ) : (
                <p>Job information not available</p>
              )}
            </div>

            <div className="detail-section">
              <h3>Update Status</h3>
              <div className="status-update">
                <select
                  value={selectedApplication.status}
                  onChange={(e) => handleUpdateApplicationStatus(selectedApplication.id, e.target.value)}
                >
                  <option value="applied">Applied</option>
                  <option value="reviewing">Reviewing</option>
                  <option value="interviewed">Interviewed</option>
                  <option value="accepted">Accepted</option>
                  <option value="rejected">Rejected</option>
                </select>
                <button 
                  className="btn btn-primary"
                  onClick={() => handleUpdateApplicationStatus(selectedApplication.id, selectedApplication.status)}
                >
                  Update Status
                </button>
              </div>
            </div>
          </div>
        )}

        {showForm && (
          <div className="modal">
            <div className="modal-content">
              <h3>Create New Application</h3>
              <form onSubmit={handleCreateApplication}>
                <div className="form-group">
                  <label>Candidate ID:</label>
                  <input
                    type="number"
                    value={formData.candidate_id}
                    onChange={(e) => setFormData({...formData, candidate_id: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Job ID:</label>
                  <input
                    type="number"
                    value={formData.job_id}
                    onChange={(e) => setFormData({...formData, job_id: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Status:</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                  >
                    <option value="applied">Applied</option>
                    <option value="reviewing">Reviewing</option>
                    <option value="interviewed">Interviewed</option>
                    <option value="accepted">Accepted</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
                <div className="form-actions">
                  <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Creating...' : 'Create Application'}
                  </button>
                  <button 
                    type="button" 
                    className="btn btn-secondary"
                    onClick={() => setShowForm(false)}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ApplicationsManagement; 