import React, { useState, useEffect } from 'react';
import './ApplicationsManagement.css';
import './AssignedJobs.css';

const RecruiterApplications = () => {
  const [applications, setApplications] = useState([]);
  const [assignedJobs, setAssignedJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [loading, setLoading] = useState(false);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [error, setError] = useState('');
  const [jobsError, setJobsError] = useState('');
  const [message, setMessage] = useState('');
  const [viewMode, setViewMode] = useState('card'); // 'card' or 'table'
  
  // Enhanced state for advanced filtering
  const [candidates, setCandidates] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [candidateSearch, setCandidateSearch] = useState('');
  const [jobSearch, setJobSearch] = useState('');
  const [candidateSuggestions, setCandidateSuggestions] = useState([]);
  const [jobSuggestions, setJobSuggestions] = useState([]);
  const [showCandidateSuggestions, setShowCandidateSuggestions] = useState(false);
  const [showJobSuggestions, setShowJobSuggestions] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  
  // Main search suggestions state
  const [mainSearchSuggestions, setMainSearchSuggestions] = useState([]);
  const [showMainSearchSuggestions, setShowMainSearchSuggestions] = useState(false);
  const [mainSearchLoading, setMainSearchLoading] = useState(false);
  
  const [filters, setFilters] = useState({
    status: '',
    location: '',
    qualification_filter: '',
    experience_range: '',
    salary_range: ''
  });

  // Status options for filtering
  const statusOptions = [
    { value: 'applied', label: 'Applied', color: '#6366f1' },
    { value: 'reviewing', label: 'Under Review', color: '#f59e0b' },
    { value: 'interview_scheduled', label: 'Interview Scheduled', color: '#10b981' },
    { value: 'hired', label: 'Hired', color: '#3b82f6' },
    { value: 'rejected', label: 'Rejected', color: '#ef4444' }
  ];

  // Filter applications based on current filters
  const filteredApplications = applications.filter(application => {
    const matchesStatus = !filters.status || application.status === filters.status;
    const matchesLocation = !filters.location || 
      application.candidate?.location?.toLowerCase().includes(filters.location.toLowerCase()) ||
      application.job?.location?.toLowerCase().includes(filters.location.toLowerCase());
    const matchesSearch = !searchTerm || 
      application.candidate?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      application.candidate?.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      application.job?.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      application.job?.company?.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesSearch && matchesStatus && matchesLocation;
  });

  const fetchAssignedJobs = async () => {
    const recruiterUser = localStorage.getItem('recruiterUser');
    if (!recruiterUser) return;
    
    const recruiterData = JSON.parse(recruiterUser);
    
    setJobsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/jobs-fast/public-fast?skip=0&limit=100`);
      if (response.ok) {
        const allJobs = await response.json();
        const recruiterJobs = allJobs.filter(job => job.recruiter_id === recruiterData.id);
        
        // Add application count to each job
        const jobsWithAppCount = await Promise.all(
          recruiterJobs.map(async (job) => {
            try {
              const appResponse = await fetch(`http://localhost:8000/api/v1/applications-public/public-fast?recruiter_id=${recruiterData.id}&job_id=${job.id}&limit=1000`);
              if (appResponse.ok) {
                const apps = await appResponse.json();
                return { ...job, applicationCount: apps.length };
              }
            } catch (err) {
              console.error('Error fetching app count for job:', job.id, err);
            }
            return { ...job, applicationCount: 0 };
          })
        );
        
        setAssignedJobs(jobsWithAppCount);
        
        if (jobsWithAppCount.length === 0) {
          setJobsError(`Currently no jobs are assigned to you by admin.`);
        } else {
          setJobsError('');
        }
      } else {
        setJobsError('Failed to fetch assigned jobs');
      }
    } catch (err) {
      console.error('Error fetching assigned jobs:', err);
      setJobsError('Failed to fetch assigned jobs');
    } finally {
      setJobsLoading(false);
    }
  };

  const fetchApplicationsForJob = async (jobId) => {
    if (!jobId) {
      setApplications([]);
      setError('');
      return;
    }

    setLoading(true);
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('limit', '100');
      queryParams.append('job_id', jobId);
      
      // Get recruiter info for additional filtering
      const recruiterUser = localStorage.getItem('recruiterUser');
      if (recruiterUser) {
        const recruiterData = JSON.parse(recruiterUser);
        queryParams.append('recruiter_id', recruiterData.id);
      }

      // Add current filters
      if (filters.status) queryParams.append('status_filter', filters.status);
      if (filters.qualification_filter) queryParams.append('qualification_filter', filters.qualification_filter);
      if (searchTerm) queryParams.append('search', searchTerm);
      
      const response = await fetch(`http://localhost:8000/api/v1/applications-public/public-fast?${queryParams.toString()}`);
      if (response.ok) {
        const data = await response.json();
        console.log(`Fetched applications for job ${jobId}:`, data);
        
        if (data.length === 0) {
          setError(`Currently no candidates applied to this job`);
        } else {
          setError('');
        }
        
        setApplications(data);
      } else {
        setError('Failed to fetch applications');
      }
    } catch (err) {
      console.error('Error fetching applications:', err);
      setError('Failed to fetch applications');
    } finally {
      setLoading(false);
    }
  };

  const handleJobClick = (job) => {
    setSelectedJob(job);
    fetchApplicationsForJob(job.id);
  };

  const handleLogout = () => {
    // Clear all stored data
    localStorage.removeItem('recruiterToken');
    localStorage.removeItem('recruiterUser');
    localStorage.removeItem('access_token');
    
    // Redirect to login page
    window.location.href = '/recruiter/login';
  };

  // Filter functions
  const applyFilters = () => {
    if (selectedJob) {
      fetchApplicationsForJob(selectedJob.id);
    }
  };

  const clearFilters = () => {
    setFilters({
      status: '',
      location: '',
      qualification_filter: '',
      experience_range: '',
      salary_range: ''
    });
    setSearchTerm('');
    if (selectedJob) {
      fetchApplicationsForJob(selectedJob.id);
    }
  };

  useEffect(() => {
    fetchAssignedJobs();
  }, []);

  useEffect(() => {
    // Re-fetch applications when filters change
    if (selectedJob) {
      fetchApplicationsForJob(selectedJob.id);
    }
  }, [filters]);

  return (
    <div className="applications-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <div className="header-text">
              <h1 className="header-title">Recruiter Applications</h1>
              <p className="header-subtitle">Manage applications for your assigned jobs</p>
            </div>
          </div>
          <div className="header-right">
            <button 
              className="logout-btn"
              onClick={handleLogout}
              title="Logout"
            >
              🚪 Logout
            </button>
          </div>
        </div>
      </div>

      {/* Two Panel Layout */}
      <div className="two-panel-layout">
        {/* Left Panel - Assigned Jobs */}
        <div className="jobs-panel">
          <div className="panel-header">
            <h2 className="panel-title">Your Assigned Jobs</h2>
            <p className="panel-subtitle">Click a job to view applications</p>
          </div>
          
          {jobsLoading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading assigned jobs...</p>
            </div>
          ) : assignedJobs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💼</div>
              <h3>Currently no jobs are assigned to you by admin</h3>
            </div>
          ) : (
            <div className="jobs-list">
              {assignedJobs.map((job) => (
                <div 
                  key={job.id} 
                  className={`job-item ${selectedJob?.id === job.id ? 'selected' : ''}`}
                  onClick={() => handleJobClick(job)}
                >
                  <div className="job-header">
                    <h3 className="job-title">{job.title}</h3>
                    <span className={`app-count ${job.applicationCount > 0 ? 'has-apps' : 'no-apps'}`}>
                      {job.applicationCount} applications
                    </span>
                  </div>
                  <div className="job-details">
                    <p><strong>{job.company}</strong> • {job.location}</p>
                    <p><span className="domain-badge">{job.domain}</span></p>
                    {job.salary_min && job.salary_max && (
                      <p className="salary">${job.salary_min?.toLocaleString()} - ${job.salary_max?.toLocaleString()}</p>
                    )}
                  </div>
                  <div className="job-status">
                    <span className={`status-badge ${job.is_active ? 'active' : 'inactive'}`}>
                      {job.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Panel - Applications for Selected Job */}
        <div className="applications-panel">
          {/* Filters for Applications - Always Visible */}
          <div className="applications-filters">
            <div className="filters-header">
              <h3>
                {selectedJob 
                  ? `Applications for: ${selectedJob.title}`
                  : 'Application Filters'
                }
              </h3>
            </div>
            
            <div className="filters-row">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search candidates..."
                className="filter-input"
                disabled={!selectedJob}
              />
              
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="filter-input"
                disabled={!selectedJob}
              >
                <option value="">All Statuses</option>
                {statusOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              
              <select
                value={filters.qualification_filter}
                onChange={(e) => setFilters({ ...filters, qualification_filter: e.target.value })}
                className="filter-input"
                disabled={!selectedJob}
              >
                <option value="">All Candidates</option>
                <option value="qualified">✅ Qualified Only</option>
                <option value="rejected">❌ Rejected Only</option>
              </select>
              
              <button 
                className="btn btn-primary" 
                onClick={applyFilters}
                disabled={!selectedJob}
              >
                Apply
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={clearFilters}
                disabled={!selectedJob}
              >
                Clear
              </button>
            </div>
          </div>

          {!selectedJob ? (
            <div className="no-job-selected">
              <div className="empty-icon">👈</div>
              <h3>Select a job to view applications</h3>
              <p>Click on any job from the left panel to see candidates who applied</p>
            </div>
          ) : (
            <>
              {/* Applications Content */}
              <div className="applications-content">
                <div className="results-header">
                  <h2 className="results-title">
                    Applications ({filteredApplications.length})
                    {loading && <span className="loading-spinner">Loading...</span>}
                  </h2>
                  <div className="view-controls">
                    <button 
                      className={`view-btn ${viewMode === 'card' ? 'active' : ''}`}
                      onClick={() => setViewMode('card')}
                    >
                      Card View
                    </button>
                    <button 
                      className={`view-btn ${viewMode === 'table' ? 'active' : ''}`}
                      onClick={() => setViewMode('table')}
                    >
                      Table View
                    </button>
                  </div>
                </div>

                {loading ? (
                  <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Loading applications...</p>
                  </div>
                ) : filteredApplications.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">📋</div>
                    <h3>{error || "Currently no candidates applied to this job"}</h3>
                  </div>
                ) : viewMode === 'card' ? (
                  <div className="applications-grid">
                    {filteredApplications.map(application => (
                      <div 
                        key={application.id} 
                        className={`application-card ${selectedApplication?.id === application.id ? 'selected' : ''}`}
                        onClick={() => setSelectedApplication(application)}
                      >
                        <div className="card-header">
                          <h3 className="candidate-name">{application.candidate?.name}</h3>
                          <span className={`status-badge status-${application.status}`}>
                            {application.status}
                          </span>
                        </div>
                        <div className="card-content">
                          <div className="candidate-info">
                            <p><strong>Email:</strong> {application.candidate?.email}</p>
                            <p><strong>Location:</strong> {application.candidate?.location}</p>
                            <p><strong>Domain:</strong> {application.candidate?.domain}</p>
                            <p><strong>Score:</strong> {application.candidate_score || 'N/A'}</p>
                            <p><strong>Qualified:</strong> {application.is_qualified ? '✅ Yes' : '❌ No'}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="applications-table-container">
                    <table className="applications-table">
                      <thead>
                        <tr>
                          <th>Candidate</th>
                          <th>Status</th>
                          <th>Score</th>
                          <th>Qualified</th>
                          <th>Applied Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredApplications.map(application => (
                          <tr 
                            key={application.id}
                            className={`table-row ${selectedApplication?.id === application.id ? 'selected' : ''}`}
                            onClick={() => setSelectedApplication(application)}
                          >
                            <td>
                              <div className="candidate-cell">
                                <strong>{application.candidate?.name}</strong>
                                <div className="candidate-email">{application.candidate?.email}</div>
                              </div>
                            </td>
                            <td>
                              <span className={`status-badge status-${application.status}`}>
                                {application.status}
                              </span>
                            </td>
                            <td>{application.candidate_score || 'N/A'}</td>
                            <td>
                              <span className={`qualification-badge ${application.is_qualified ? 'qualified' : 'not-qualified'}`}>
                                {application.is_qualified ? '✅' : '❌'}
                              </span>
                            </td>
                            <td>
                              {application.created_at ? new Date(application.created_at).toLocaleDateString() : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecruiterApplications;
