import React, { useState, useEffect } from 'react';
import './ApplicationsManagement.css';
import './AssignedJobs.css';

const ApplicationsManagement = () => {
  const [applications, setApplications] = useState([]);
  const [assignedJobs, setAssignedJobs] = useState([]);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [loading, setLoading] = useState(false);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [error, setError] = useState('');
  const [jobsError, setJobsError] = useState('');
  const [message, setMessage] = useState('');
  const [showForm, setShowForm] = useState(false);
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
    job_id: '',
    candidate_id: '',
    status: '',
    experience_range: '',
    location: '',
    qualification_filter: ''
  });
  
  const [formData, setFormData] = useState({
    candidate_id: '',
    job_id: '',
    status: 'applied'
  });

  // Experience ranges for filtering
  const experienceRanges = [
    { value: '', label: 'All Experience Levels' },
    { value: '0-2', label: '0-2 years' },
    { value: '3-5', label: '3-5 years' },
    { value: '6-8', label: '6-8 years' },
    { value: '9+', label: '9+ years' }
  ];

  // Enhanced status workflow
  const statusOptions = [
    { value: 'applied', label: 'Applied', color: '#6b7280' },
    { value: 'reviewed', label: 'Reviewed', color: '#10b981' },
    { value: 'interview_scheduled', label: 'Interview Scheduled', color: '#10b981' },
    { value: 'hired', label: 'Hired', color: '#3b82f6' },
    { value: 'rejected', label: 'Rejected', color: '#ef4444' }
  ];

  // Fetch candidates and jobs for dropdowns
  useEffect(() => {
    fetchCandidates();
    fetchJobs();
    fetchAllApplications();
    fetchAssignedJobs(); // Also fetch assigned jobs for recruiters
  }, []);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.search-input-wrapper')) {
        setShowMainSearchSuggestions(false);
        setShowCandidateSuggestions(false);
        setShowJobSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const fetchCandidates = async () => {
    try {
      let response = await fetch('http://localhost:8000/api/v1/candidates/public?limit=100');
      if (!response.ok) {
        response = await fetch('http://localhost:8000/api/v1/candidates?skip=0&limit=100');
      }
      if (response && response.ok) {
        const data = await response.json();
        setCandidates(data);
      }
    } catch (err) {
      console.error('Failed to fetch candidates:', err);
    }
  };

  const fetchJobs = async () => {
    try {
      let response = await fetch('http://localhost:8000/api/v1/jobs/public?limit=100');
      if (!response.ok) {
        response = await fetch('http://localhost:8000/api/v1/jobs?skip=0&limit=100');
      }
      if (response && response.ok) {
        const data = await response.json();
        setJobs(data);
      }
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    }
  };

  const fetchAssignedJobs = async () => {
    const recruiterUser = localStorage.getItem('recruiterUser');
    if (!recruiterUser) {
      setAssignedJobs([]);
      setJobsError('');
      return;
    }
    
    const recruiterData = JSON.parse(recruiterUser);
    if (recruiterData.role !== 'recruiter') {
      // Admin or other roles - don't show assigned jobs section
      setAssignedJobs([]);
      setJobsError('');
      return;
    }
    
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

  const fetchAllApplications = async () => {
    setLoading(true);
    try {
      // Build query parameters for qualification filtering
      const queryParams = new URLSearchParams();
      queryParams.append('limit', '100');
      
      // Admin view - show all applications (no filtering by recruiter)
      console.log('Admin view - showing all applications');
      
      if (filters.qualification_filter) {
        queryParams.append('qualification_filter', filters.qualification_filter);
      }
      
      const response = await fetch(`http://localhost:8000/api/v1/applications-public/public-fast?${queryParams.toString()}`);
      if (response.ok) {
        const data = await response.json();
        console.log('Fetched applications:', data);
        
        // Admin view - show appropriate message
        if (data.length === 0) {
          setError('No applications found in the system');
        } else {
          setError(''); // Clear any previous error
          // Scoring-based qualification removed from Applications Management UI
        }
        
        setApplications(data);
      } else {
        setError('Failed to fetch applications');
      }
    } catch (err) {
      setError('Failed to fetch applications');
    } finally {
      setLoading(false);
    }
  };

  // Smart search for candidates
  const searchCandidates = async (searchTerm) => {
    if (!searchTerm || searchTerm.length < 2) {
      setCandidateSuggestions([]);
      setShowCandidateSuggestions(false);
      setSearchLoading(false);
      return;
    }

    setSearchLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/candidates/?search=${encodeURIComponent(searchTerm)}&limit=10`
      );
      
      if (response.ok) {
        const data = await response.json();
        setCandidateSuggestions(data || []);
        setShowCandidateSuggestions(true);
      } else {
        setCandidateSuggestions([]);
        setShowCandidateSuggestions(false);
      }
    } catch (err) {
      console.error('Search error:', err);
      setCandidateSuggestions([]);
      setShowCandidateSuggestions(false);
    } finally {
      setSearchLoading(false);
    }
  };

  // Smart search for jobs
  const searchJobs = async (searchTerm) => {
    if (!searchTerm || searchTerm.length < 2) {
      setJobSuggestions([]);
      setShowJobSuggestions(false);
      setSearchLoading(false);
      return;
    }

    setSearchLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/jobs/?search=${encodeURIComponent(searchTerm)}&limit=10`
      );
      
      if (response.ok) {
        const data = await response.json();
        setJobSuggestions(data || []);
        setShowJobSuggestions(true);
      } else {
        setJobSuggestions([]);
        setShowJobSuggestions(false);
      }
    } catch (err) {
      console.error('Search error:', err);
      setJobSuggestions([]);
      setShowJobSuggestions(false);
    } finally {
      setSearchLoading(false);
    }
  };

  // Main search functionality with suggestions
  const searchApplications = async (searchTerm) => {
    if (!searchTerm || searchTerm.length < 2) {
      setMainSearchSuggestions([]);
      setShowMainSearchSuggestions(false);
      setMainSearchLoading(false);
      return;
    }

    setMainSearchLoading(true);
    try {
      console.log('Searching candidates and jobs for:', searchTerm);
      
      // Search candidates
      const candidateResponse = await fetch(
        `http://localhost:8000/api/v1/candidates/?search=${encodeURIComponent(searchTerm)}&limit=5`
      );
      
      // Search jobs
      const jobResponse = await fetch(
        `http://localhost:8000/api/v1/jobs/?search=${encodeURIComponent(searchTerm)}&limit=5`
      );
      
      const suggestions = [];
      
      if (candidateResponse.ok) {
        const candidateData = await candidateResponse.json();
        console.log('Candidate search results:', candidateData);
        candidateData.forEach(candidate => {
          suggestions.push({
            type: 'candidate',
            id: candidate.id,
            name: candidate.name,
            email: candidate.email,
            location: candidate.location,
            displayText: `${candidate.name} (${candidate.email})`
          });
        });
      }
      
      if (jobResponse.ok) {
        const jobData = await jobResponse.json();
        console.log('Job search results:', jobData);
        jobData.forEach(job => {
          suggestions.push({
            type: 'job',
            id: job.id,
            title: job.title,
            company: job.company,
            location: job.location,
            displayText: `${job.title} at ${job.company}`
          });
        });
      }
      
      console.log('Total suggestions:', suggestions.length);
      setMainSearchSuggestions(suggestions);
      setShowMainSearchSuggestions(true);
    } catch (err) {
      console.error('Main search error:', err);
      setMainSearchSuggestions([]);
      setShowMainSearchSuggestions(false);
    } finally {
      setMainSearchLoading(false);
    }
  };

  const selectMainSearchSuggestion = (suggestion) => {
    if (suggestion.type === 'candidate') {
      setSearchTerm(suggestion.name);
    } else if (suggestion.type === 'job') {
      setSearchTerm(suggestion.title);
    }
    setShowMainSearchSuggestions(false);
  };

  // Debounced search handlers
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (candidateSearch) {
        searchCandidates(candidateSearch);
      } else {
        setCandidateSuggestions([]);
        setShowCandidateSuggestions(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [candidateSearch]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (jobSearch) {
        searchJobs(jobSearch);
      } else {
        setJobSuggestions([]);
        setShowJobSuggestions(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [jobSearch]);

  // Debounced main search handler
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchTerm) {
        console.log('Searching for:', searchTerm);
        searchApplications(searchTerm);
      } else {
        setMainSearchSuggestions([]);
        setShowMainSearchSuggestions(false);
        // Refresh applications when search is cleared
        fetchAllApplications();
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  // No need for auto-apply since filtering is done client-side

  const handleCandidateSearchChange = (e) => {
    setCandidateSearch(e.target.value);
  };

  const handleJobSearchChange = (e) => {
    setJobSearch(e.target.value);
  };

  const selectCandidate = (candidate) => {
    setFormData({ ...formData, candidate_id: candidate.id });
    setCandidateSearch(candidate.name);
    setShowCandidateSuggestions(false);
  };

  const selectJob = (job) => {
    setFormData({ ...formData, job_id: job.id });
    setJobSearch(job.title);
    setShowJobSuggestions(false);
  };

  const clearFilters = () => {
    setFilters({
      job_id: '',
      candidate_id: '',
      status: '',
      experience_range: '',
      location: '',
      qualification_filter: ''
    });
    setSearchTerm('');
    setMainSearchSuggestions([]);
    setShowMainSearchSuggestions(false);
    fetchAllApplications();
  };

  const applyFilters = () => {
    // Filters are applied client-side, so we just need to refresh the data
    fetchAllApplications();
  };

  const getStatusColor = (status) => {
    const statusOption = statusOptions.find(option => option.value === status);
    return statusOption ? statusOption.color : '#6b7280';
  };

  const getExperienceRange = (years) => {
    if (years <= 2) return '0-2';
    if (years <= 5) return '3-5';
    if (years <= 8) return '6-8';
    return '9+';
  };

  // Apply client-side filtering since backend filtering has connection issues
  const filteredApplications = applications.filter(app => {
    // Debug logging
    if (searchTerm) {
      console.log('Filtering app:', app.id, 'candidate:', app.candidate?.name, 'job:', app.job?.title);
    }
    
    // Search filter
    const matchesSearch = !searchTerm || 
      (app.candidate?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
       app.candidate?.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
       app.job?.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
       app.job?.company?.toLowerCase().includes(searchTerm.toLowerCase()));
    
    // Status filter
    const matchesStatus = !filters.status || filters.status === '' || app.status === filters.status;
    
    // Location filter
    const matchesLocation = !filters.location || filters.location === '' || 
      (app.candidate?.location?.toLowerCase().includes(filters.location.toLowerCase()) ||
       app.job?.location?.toLowerCase().includes(filters.location.toLowerCase()));
    
         return matchesSearch && matchesStatus && matchesLocation;
  });

  const handleUpdateApplicationStatus = async (applicationId, newStatus) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/applications/${applicationId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
      });
      
      if (response.ok) {
        setMessage('Application status updated successfully');
        fetchAllApplications();
        if (selectedApplication?.id === applicationId) {
          setSelectedApplication({ ...selectedApplication, status: newStatus });
        }
      } else {
        setError('Failed to update application status');
      }
    } catch (err) {
      setError('Failed to update application status');
    }
  };

  // Legacy recalculate qualification function removed - replaced by assessment-based system

  const handleCreateApplication = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/applications/public-fast', {
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
        setMessage('Application created successfully');
        setFormData({
          candidate_id: '',
          job_id: '',
          status: 'applied'
        });
        setShowForm(false);
        setCandidateSearch('');
        setJobSearch('');
        fetchAllApplications();

        // Auto-assign assessment for the created application (mock fast path)
        try {
          const created = await response.json();
          console.log('Created application:', created);
          
          // Check if job has MCQs configured
          const mcqsRes = await fetch(`http://localhost:8000/api/v1/assessments-fast/mcqs/${created.job_id}`);
          if (mcqsRes.ok) {
            const mcqsData = await mcqsRes.json();
            if (mcqsData.mcqs && mcqsData.mcqs.length > 0) {
              // Assign assessment only if MCQs exist
              const assignRes = await fetch(`http://localhost:8000/api/v1/assessments-fast/assign?application_id=${created.id}&candidate_id=${created.candidate_id}&job_id=${created.job_id}&validity_hours=24`, { method: 'POST' });
              if (assignRes.ok) {
                console.log('Assessment assigned successfully');
              } else {
                console.warn('Assessment assignment failed:', await assignRes.text());
              }
            } else {
              console.warn('No MCQs configured for this job');
            }
          } else {
            console.warn('Failed to check MCQs for job');
          }
        } catch (e) {
          console.warn('Assessment assignment error', e);
        }
      } else {
        const errorData = await response.json();
        setError(`Failed to create application: ${errorData.detail}`);
      }
    } catch (err) {
      setError('Failed to create application');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="applications-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <div className="header-text">
              <h1 className="header-title">Applications Management</h1>
              <p className="header-subtitle">Manage and track job applications</p>
            </div>
          </div>
          <div className="header-actions">
            <button className="btn btn-secondary" onClick={() => window.location.href = '/recruiter/dashboard'}>
              Dashboard
            </button>
            <button className="btn btn-primary" onClick={() => setShowForm(true)}>
              Create Application
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="dashboard-layout">
        {/* Filters Sidebar */}
        <div className="filters-sidebar">
          <div className="sidebar-header">
            <h3 className="sidebar-title">Search & Filter Applications</h3>
          </div>

          <div className="filter-section">
            <div className="filter-section-title">Search Applications</div>
            <div className="search-input-wrapper" style={{position: 'relative'}}>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by candidate name, email, job title, company..."
                className="filter-input"
              />
              {mainSearchLoading && (
                <div className="search-loading">Searching...</div>
              )}
              {showMainSearchSuggestions && mainSearchSuggestions.length > 0 && (
                <div className="suggestions-dropdown" style={{zIndex: 1000, position: 'absolute', top: '100%', left: 0, right: 0, backgroundColor: 'white', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', maxHeight: '300px', overflowY: 'auto'}}>
                  {mainSearchSuggestions.map((suggestion, index) => (
                    <div 
                      key={`${suggestion.type}-${suggestion.id}-${index}`}
                      className="suggestion-item"
                      onClick={() => selectMainSearchSuggestion(suggestion)}
                      style={{padding: '12px', cursor: 'pointer', borderBottom: '1px solid #eee', display: 'flex', flexDirection: 'column', gap: '4px'}}
                    >
                      <div className="suggestion-main">
                        <strong>{suggestion.displayText}</strong>
                      </div>
                      <div className="suggestion-sub">
                        <span className="suggestion-type">{suggestion.type === 'candidate' ? '👤 Candidate' : '💼 Job'}</span>
                        {suggestion.location && <span>{suggestion.location}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="filter-section">
            <div className="filter-section-title">Status Filter</div>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="filter-input"
            >
              <option value="">All Statuses</option>
              {statusOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          

          <div className="filter-section">
            <div className="filter-section-title">Location Filter</div>
            <input
              type="text"
              value={filters.location}
              onChange={(e) => setFilters({ ...filters, location: e.target.value })}
              placeholder="Filter by location..."
              className="filter-input"
            />
          </div>

          <div className="filter-section">
            <div className="filter-section-title">Qualification Filter</div>
            <select
              value={filters.qualification_filter}
              onChange={(e) => setFilters({ ...filters, qualification_filter: e.target.value })}
              className="filter-input"
            >
              <option value="">All Candidates</option>
              <option value="qualified">✅ Qualified Only</option>
              <option value="rejected">❌ Rejected Only</option>
            </select>
          </div>


          <div className="filter-actions">
            <button className="btn btn-primary btn-find" onClick={applyFilters}>
              Apply Filters
            </button>
            <button className="btn btn-clear" onClick={clearFilters}>
              Clear All
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}
          {message && <div className="success-message">{message}</div>}
        </div>

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
              <h3>{error || "No Applications Found"}</h3>
              {!error && <p>Try adjusting your search criteria or create a new application.</p>}
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
                    <h4 className="card-title">Application #{application.id}</h4>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span 
                        className="status-badge"
                        style={{ backgroundColor: getStatusColor(application.status) }}
                      >
                        {application.status.replace('_', ' ').toUpperCase()}
                      </span>
                      {application.assessment && (
                        <span 
                          className="qualification-badge"
                          style={{ 
                            backgroundColor: (application.assessment.status === 'completed' && (application.assessment.score || 0) >= 50) ? '#10b981' : '#e5e7eb',
                            color: (application.assessment.status === 'completed' && (application.assessment.score || 0) >= 50) ? 'white' : '#374151',
                            padding: '4px 8px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            fontWeight: 'bold'
                          }}
                        >
                          {application.assessment.status?.toUpperCase()} {application.assessment.score != null ? `· ${application.assessment.score}%` : ''}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="card-content">
                    {/* Candidate Profile Highlights */}
                    <div className="profile-section">
                      <h5 className="section-title">Candidate Profile</h5>
                      <div className="profile-info">
                                                 <p className="profile-name">{application.candidate?.name || 'N/A'}</p>
                         <p className="profile-email">{application.candidate?.email || 'N/A'}</p>
                         <p className="profile-location">{application.candidate?.location || 'N/A'}</p>
                      </div>
                    </div>

                    {/* Job Context */}
                    <div className="job-section">
                      <h5 className="section-title">Job Context</h5>
                      <div className="job-info">
                        <p className="job-title">{application.job?.title || 'N/A'}</p>
                        <p className="job-company">{application.job?.company || 'N/A'}</p>
                        <p className="job-location">{application.job?.location || 'N/A'}</p>
                        {/* Threshold/legacy scoring removed from this page */}
                        {application.recruiter && (
                          <div className="recruiter-info" style={{ marginTop: '8px', padding: '6px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                            <p style={{ fontSize: '12px', color: '#666', margin: '0 0 2px 0' }}>Assigned Recruiter:</p>
                            <p style={{ fontSize: '13px', fontWeight: 'bold', margin: '0', color: '#2c3e50' }}>
                              {application.recruiter.name}
                            </p>
                            <p style={{ fontSize: '11px', color: '#666', margin: '0' }}>
                              {application.recruiter.email}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="application-meta">
                      <p className="applied-date">
                        Applied: {new Date(application.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  {/* Manual status changes disabled - status updates occur after assessment evaluation */}
                </div>
              ))}
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="applications-table">
                <thead>
                  <tr>
                    <th>Application ID</th>
                    <th>Candidate</th>
                    <th>Email</th>
                    <th>Location</th>
                    <th>Job Title</th>
                    <th>Company</th>
                    <th>Job Location</th>
                    <th>Assessment Score</th>
                    <th>Assessment Status</th>
                    <th>Cheating Attempts</th>
                    <th>Recruiter</th>
                    <th>Status</th>
                    <th>Applied Date</th>
                    {/* Actions removed; status driven by assessments */}
                  </tr>
                </thead>
                <tbody>
                  {filteredApplications.map(application => (
                    <tr key={application.id}>
                      <td>#{application.id}</td>
                      <td>{application.candidate?.name || 'N/A'}</td>
                      <td>{application.candidate?.email || 'N/A'}</td>
                      <td>{application.candidate?.location || 'N/A'}</td>
                      <td>{application.job?.title || 'N/A'}</td>
                      <td>{application.job?.company || 'N/A'}</td>
                      <td>{application.job?.location || 'N/A'}</td>
                      <td>{application.assessment?.score != null ? `${application.assessment.score}%` : 'N/A'}</td>
                      <td>{application.assessment?.status ? application.assessment.status.replace('_',' ') : 'N/A'}</td>
                      <td>{application.assessment?.cheat_attempts != null ? application.assessment.cheat_attempts : 0}</td>
                      <td>
                        {application.recruiter ? (
                          <div style={{ fontSize: '12px' }}>
                            <div style={{ fontWeight: 'bold', color: '#2c3e50' }}>
                              {application.recruiter.name}
                            </div>
                            <div style={{ color: '#666', fontSize: '11px' }}>
                              {application.recruiter.email}
                            </div>
                          </div>
                        ) : (
                          <span style={{ color: '#999', fontSize: '12px' }}>Unassigned</span>
                        )}
                      </td>
                      <td>
                        <span 
                          className="status-badge"
                          style={{ backgroundColor: getStatusColor(application.status) }}
                        >
                          {application.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </td>
                      <td>{new Date(application.created_at).toLocaleDateString()}</td>
                      {/* Manual status changes disabled */}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Application Details Modal */}
      {selectedApplication && (
        <div className="modal-overlay" onClick={() => setSelectedApplication(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Application Details #{selectedApplication.id}</h2>
              <button className="modal-close" onClick={() => setSelectedApplication(null)}>
                ×
              </button>
            </div>
            
            <div className="modal-content">
              <div className="details-grid">
                <div className="detail-section">
                  <h3>Basic Information</h3>
                  <div className="detail-content">
                    <p><strong>Application ID:</strong> {selectedApplication.id}</p>
                    <p><strong>Status:</strong> 
                      <span 
                        className="status-badge"
                        style={{ backgroundColor: getStatusColor(selectedApplication.status) }}
                      >
                        {selectedApplication.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </p>
                    <p><strong>Applied Date:</strong> {new Date(selectedApplication.created_at).toLocaleDateString()}</p>
                    <p><strong>Last Updated:</strong> {new Date(selectedApplication.updated_at).toLocaleDateString()}</p>
                    
                    {/* Assessment summary */}
                    <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                      <h4 style={{ margin: '0 0 8px 0', color: '#333' }}>Assessment</h4>
                      <p><strong>Status:</strong> {selectedApplication.assessment?.status || 'N/A'}</p>
                      <p><strong>Score:</strong> {selectedApplication.assessment?.score != null ? `${selectedApplication.assessment.score}%` : 'N/A'}</p>
                      {selectedApplication.assessment?.start_time && (
                        <p><strong>Started:</strong> {new Date(selectedApplication.assessment.start_time).toLocaleString()}</p>
                      )}
                      {selectedApplication.assessment?.completion_time && (
                        <p><strong>Completed:</strong> {new Date(selectedApplication.assessment.completion_time).toLocaleString()}</p>
                      )}
                      {selectedApplication.assessment?.cheat_attempts != null && (
                        <p><strong>Cheating Attempts:</strong> {selectedApplication.assessment.cheat_attempts}</p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h3>Candidate Information</h3>
                  <div className="detail-content">
                    {selectedApplication.candidate ? (
                      <>
                        <p><strong>Name:</strong> {selectedApplication.candidate.name}</p>
                        <p><strong>Email:</strong> {selectedApplication.candidate.email}</p>
                        <p><strong>Location:</strong> {selectedApplication.candidate.location}</p>
                        <p><strong>Domain:</strong> {selectedApplication.candidate.domain}</p>
                        <p><strong>Experience:</strong> {selectedApplication.candidate.total_years_experience || 'N/A'} years</p>
                        <p><strong>Expected Salary:</strong> ${selectedApplication.candidate.expected_salary_min || 'N/A'} - ${selectedApplication.candidate.expected_salary_max || 'N/A'}</p>
                      </>
                    ) : (
                      <p>Candidate information not available</p>
                    )}
                  </div>
                </div>

                <div className="detail-section">
                  <h3>Job Information</h3>
                  <div className="detail-content">
                    {selectedApplication.job ? (
                      <>
                        <p><strong>Title:</strong> {selectedApplication.job.title}</p>
                        <p><strong>Company:</strong> {selectedApplication.job.company}</p>
                        <p><strong>Location:</strong> {selectedApplication.job.location}</p>
                        <p><strong>Domain:</strong> {selectedApplication.job.domain}</p>
                        <p><strong>Salary Range:</strong> ${selectedApplication.job.salary_min || 'N/A'} - ${selectedApplication.job.salary_max || 'N/A'}</p>
                        <p><strong>Experience Required:</strong> {selectedApplication.job.total_years_required || 'N/A'} years</p>
                      </>
                    ) : (
                      <p>Job information not available</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Manual status update and legacy qualification actions removed */}
            </div>
          </div>
        </div>
      )}

      {/* Create Application Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Application</h2>
              <button className="modal-close" onClick={() => setShowForm(false)}>
                ×
              </button>
            </div>
            
            <form onSubmit={handleCreateApplication} className="modal-form">
              <div className="form-group">
                <label>Select Candidate</label>
                <div className="search-input-wrapper">
                  <input
                    type="text"
                    placeholder="Search candidates by name, email, or location..."
                    value={candidateSearch}
                    onChange={handleCandidateSearchChange}
                    className="search-input"
                  />
                  {showCandidateSuggestions && (
                    <div className="suggestions-dropdown">
                      {candidateSuggestions.map((candidate) => (
                        <div 
                          key={candidate.id} 
                          className="suggestion-item"
                          onClick={() => selectCandidate(candidate)}
                        >
                          <div className="suggestion-main">
                            <strong>{candidate.name}</strong>
                          </div>
                          <div className="suggestion-email">{candidate.email}</div>
                          <div className="suggestion-sub">
                            <span>{candidate.location}</span>
                            {candidate.total_years_experience && (
                              <span>{candidate.total_years_experience} years exp</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="form-group">
                <label>Select Job</label>
                <div className="search-input-wrapper">
                  <input
                    type="text"
                    placeholder="Search jobs by title, company, or location..."
                    value={jobSearch}
                    onChange={handleJobSearchChange}
                    className="search-input"
                  />
                  {showJobSuggestions && (
                    <div className="suggestions-dropdown">
                      {jobSuggestions.map((job) => (
                        <div 
                          key={job.id} 
                          className="suggestion-item"
                          onClick={() => selectJob(job)}
                        >
                          <div className="suggestion-main">
                            <strong>{job.title}</strong>
                          </div>
                          <div className="suggestion-email">{job.company}</div>
                          <div className="suggestion-sub">
                            <span>{job.location}</span>
                            {job.total_years_required && (
                              <span>{job.total_years_required} years req</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="form-group">
                <label>Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({...formData, status: e.target.value})}
                  className="status-select"
                >
                  {statusOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
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
  );
};

export default ApplicationsManagement; 