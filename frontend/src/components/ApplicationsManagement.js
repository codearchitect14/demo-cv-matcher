import React, { useState, useEffect } from 'react';
import './ApplicationsManagement.css';

const ApplicationsManagement = () => {
  const [applications, setApplications] = useState([]);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [showForm, setShowForm] = useState(false);
  
  // New state for dropdowns and search
  const [candidates, setCandidates] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [searchCandidate, setSearchCandidate] = useState('');
  const [searchJob, setSearchJob] = useState('');
  const [filteredCandidates, setFilteredCandidates] = useState([]);
  const [filteredJobs, setFilteredJobs] = useState([]);
  
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

  // Fetch candidates and jobs for dropdowns
  useEffect(() => {
    fetchCandidates();
    fetchJobs();
  }, []);

  const fetchCandidates = async () => {
    try {
      // Try public endpoint first
      let response = await fetch('http://localhost:8000/api/v1/candidates/public?limit=100');
      if (!response.ok) {
        // Fallback to non-public listing (no auth required)
        response = await fetch('http://localhost:8000/api/v1/candidates?skip=0&limit=100');
      }
      if (response && response.ok) {
        const data = await response.json();
        setCandidates(data);
        setFilteredCandidates(data);
      } else {
        console.error('Failed to fetch candidates (public and fallback).');
      }
    } catch (err) {
      console.error('Failed to fetch candidates:', err);
    }
  };

  const fetchJobs = async () => {
    try {
      // Try public endpoint first
      let response = await fetch('http://localhost:8000/api/v1/jobs/public?limit=100');
      if (!response.ok) {
        // Fallback to non-public listing (no auth required)
        response = await fetch('http://localhost:8000/api/v1/jobs?skip=0&limit=100');
      }
      if (response && response.ok) {
        const data = await response.json();
        setJobs(data);
        setFilteredJobs(data);
      } else {
        console.error('Failed to fetch jobs (public and fallback).');
      }
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    }
  };

  // Search functionality for candidates
  useEffect(() => {
    if (searchCandidate.trim() === '') {
      setFilteredCandidates(candidates);
    } else {
      const filtered = candidates.filter(candidate =>
        candidate.name?.toLowerCase().includes(searchCandidate.toLowerCase()) ||
        candidate.email?.toLowerCase().includes(searchCandidate.toLowerCase()) ||
        candidate.location?.toLowerCase().includes(searchCandidate.toLowerCase())
      );
      setFilteredCandidates(filtered);
    }
  }, [searchCandidate, candidates]);

  // Search functionality for jobs
  useEffect(() => {
    if (searchJob.trim() === '') {
      setFilteredJobs(jobs);
    } else {
      const filtered = jobs.filter(job =>
        job.title?.toLowerCase().includes(searchJob.toLowerCase()) ||
        job.company?.toLowerCase().includes(searchJob.toLowerCase()) ||
        job.location?.toLowerCase().includes(searchJob.toLowerCase())
      );
      setFilteredJobs(filtered);
    }
  }, [searchJob, jobs]);

  const fetchApplicationDetails = async (applicationId) => {
    try {
      // Use public endpoint for testing
      const response = await fetch(`http://localhost:8000/api/v1/applications/public/${applicationId}`);
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
      // Use public endpoint for testing
      // Use existing job applications route (no public suffix needed)
      const response = await fetch(`http://localhost:8000/api/v1/applications/job/${jobId}/applications`);
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
      // Use public endpoint for testing
      // Use correct public route path
      const response = await fetch(`http://localhost:8000/api/v1/applications/candidate/${candidateId}/applications/public`);
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
      // Use public endpoint for testing
      const response = await fetch('http://localhost:8000/api/v1/applications/public', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          candidate_id: parseInt(formData.candidate_id),
          job_id: parseInt(formData.job_id)
        })
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
      // Use public endpoint for testing
      const response = await fetch(`http://localhost:8000/api/v1/applications/${applicationId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
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
      setError('Please select either a Job or Candidate to filter applications');
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
      {/* Professional Header */}
      <div className="unified-header">
        <div className="header-content">
          <div className="header-left">
            <div className="header-icon">
              <i className="fas fa-briefcase"></i>
            </div>
            <div className="header-text">
              <h1 className="header-title">Applications Management</h1>
            </div>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-back" onClick={() => window.location.href = '/recruiter/dashboard'}>← Back to Dashboard</button>
          <button 
            className="btn btn-primary"
            onClick={() => setShowForm(true)}
          >
            <i className="fas fa-plus"></i>
            Create Application
          </button>
        </div>
      </div>

      {/* Messages */}
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

      {/* Main Content */}
      <div className="dashboard-content">
        {/* Filter Section */}
        <div className="content-section">
          <div className="section-header">
            <h2 className="section-title">
              <i className="fas fa-filter"></i>
              Filter Applications
            </h2>
            <p className="section-description">
              Search and filter applications by job, candidate, or status
            </p>
          </div>
          
          <div className="filters-container">
            <div className="filters-grid">
              <div className="filter-group">
                <label className="filter-label">Select Job</label>
                <div className="search-dropdown">
                  <input
                    type="text"
                    placeholder="Search jobs by title, company, or location..."
                    value={searchJob}
                    onChange={(e) => setSearchJob(e.target.value)}
                    className="search-input"
                  />
                  <select
                    value={filters.job_id}
                    onChange={(e) => setFilters({...filters, job_id: e.target.value, candidate_id: ''})}
                    className="dropdown-select"
                  >
                    <option value="">Select a job...</option>
                    {filteredJobs.map((job) => (
                      <option key={job.id} value={job.id}>
                        {job.title} - {job.company} ({job.location})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="filter-group">
                <label className="filter-label">Select Candidate</label>
                <div className="search-dropdown">
                  <input
                    type="text"
                    placeholder="Search candidates by name, email, or location..."
                    value={searchCandidate}
                    onChange={(e) => setSearchCandidate(e.target.value)}
                    className="search-input"
                  />
                  <select
                    value={filters.candidate_id}
                    onChange={(e) => setFilters({...filters, candidate_id: e.target.value, job_id: ''})}
                    className="dropdown-select"
                  >
                    <option value="">Select a candidate...</option>
                    {filteredCandidates.map((candidate) => (
                      <option key={candidate.id} value={candidate.id}>
                        {candidate.name} - {candidate.email} ({candidate.location})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="filter-group">
                <label className="filter-label">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({...filters, status: e.target.value})}
                  className="status-select"
                >
                  <option value="">All Statuses</option>
                  <option value="applied">Applied</option>
                  <option value="accepted">Accepted</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
            </div>

            <div className="filter-actions">
              <button 
                className="btn btn-secondary"
                onClick={handleFilterApplications}
              >
                <i className="fas fa-search"></i>
                Filter Applications
              </button>
            </div>
          </div>
        </div>

        {/* Applications List */}
        <div className="content-section">
          <div className="section-header">
            <h2 className="section-title">
              <i className="fas fa-list"></i>
              Applications ({applications.length})
            </h2>
            <p className="section-description">
              View and manage all job applications
            </p>
          </div>

          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading applications...</p>
            </div>
          ) : (
            <div className="applications-container">
              {applications.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">
                    <i className="fas fa-inbox"></i>
                  </div>
                  <h3>No Applications Found</h3>
                  <p>Try selecting a job or candidate to view applications</p>
                </div>
              ) : (
                <div className="applications-grid">
                  {applications.map(application => (
                    <div 
                      key={application.id} 
                      className={`application-card ${selectedApplication?.id === application.id ? 'selected' : ''}`}
                      onClick={() => fetchApplicationDetails(application.id)}
                    >
                      <div className="application-header">
                        <h3 className="application-title">Application #{application.id}</h3>
                        <span 
                          className="status-badge"
                          style={{ backgroundColor: getStatusColor(application.status) }}
                        >
                          {application.status}
                        </span>
                      </div>
                      
                      <div className="application-content">
                        <div className="application-info">
                          <p><strong>Candidate:</strong> {application.candidate?.name || 'N/A'}</p>
                          <p><strong>Job:</strong> {application.job?.title || 'N/A'}</p>
                          <p><strong>Applied:</strong> {new Date(application.created_at).toLocaleDateString()}</p>
                        </div>
                        
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
                            <option value="accepted">Accepted</option>
                            <option value="rejected">Rejected</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Application Details */}
        {selectedApplication && (
          <div className="content-section">
            <div className="section-header">
              <h2 className="section-title">
                <i className="fas fa-file-alt"></i>
                Application Details
              </h2>
            </div>
            
            <div className="application-details-container">
              <div className="details-grid">
                <div className="detail-section">
                  <h3 className="detail-title">Basic Information</h3>
                  <div className="detail-content">
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
                </div>

                <div className="detail-section">
                  <h3 className="detail-title">Candidate Information</h3>
                  <div className="detail-content">
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
                </div>

                <div className="detail-section">
                  <h3 className="detail-title">Job Information</h3>
                  <div className="detail-content">
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
                </div>
              </div>

              <div className="detail-actions">
                <h3 className="detail-title">Update Status</h3>
                <div className="status-update">
                  <select
                    value={selectedApplication.status}
                    onChange={(e) => handleUpdateApplicationStatus(selectedApplication.id, e.target.value)}
                    className="status-select"
                  >
                    <option value="applied">Applied</option>
                    <option value="accepted">Accepted</option>
                    <option value="rejected">Rejected</option>
                  </select>
                  <button 
                    className="btn btn-primary"
                    onClick={() => handleUpdateApplicationStatus(selectedApplication.id, selectedApplication.status)}
                  >
                    <i className="fas fa-save"></i>
                    Update Status
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Create Application Modal */}
        {showForm && (
          <div className="modal">
            <div className="modal-content">
              <div className="modal-header">
                <h3 className="modal-title">
                  <i className="fas fa-plus"></i>
                  Create New Application
                </h3>
                <button 
                  className="modal-close"
                  onClick={() => setShowForm(false)}
                >
                  <i className="fas fa-times"></i>
                </button>
              </div>
              
              <form onSubmit={handleCreateApplication} className="modal-form">
                <div className="form-group">
                  <label className="form-label">Select Candidate</label>
                  <div className="search-dropdown">
                    <input
                      type="text"
                      placeholder="Search candidates by name, email, or location..."
                      value={searchCandidate}
                      onChange={(e) => setSearchCandidate(e.target.value)}
                      className="search-input"
                    />
                    <select
                      value={formData.candidate_id}
                      onChange={(e) => setFormData({...formData, candidate_id: e.target.value})}
                      required
                      className="dropdown-select"
                    >
                      <option value="">Select a candidate...</option>
                      {filteredCandidates.map((candidate) => (
                        <option key={candidate.id} value={candidate.id}>
                          {candidate.name} - {candidate.email} ({candidate.location})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div className="form-group">
                  <label className="form-label">Select Job</label>
                  <div className="search-dropdown">
                    <input
                      type="text"
                      placeholder="Search jobs by title, company, or location..."
                      value={searchJob}
                      onChange={(e) => setSearchJob(e.target.value)}
                      className="search-input"
                    />
                    <select
                      value={formData.job_id}
                      onChange={(e) => setFormData({...formData, job_id: e.target.value})}
                      required
                      className="dropdown-select"
                    >
                      <option value="">Select a job...</option>
                      {filteredJobs.map((job) => (
                        <option key={job.id} value={job.id}>
                          {job.title} - {job.company} ({job.location})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div className="form-group">
                  <label className="form-label">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                    className="status-select"
                  >
                    <option value="applied">Applied</option>
                    <option value="accepted">Accepted</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
                
                <div className="form-actions">
                  <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? (
                      <>
                        <i className="fas fa-spinner fa-spin"></i>
                        Creating...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-plus"></i>
                        Create Application
                      </>
                    )}
                  </button>
                  <button 
                    type="button" 
                    className="btn btn-secondary"
                    onClick={() => setShowForm(false)}
                  >
                    <i className="fas fa-times"></i>
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