import React, { useState, useEffect } from 'react';
import './JobsDashboard.css';
import RecruiterMCQEditor from './RecruiterMCQEditor';

const JobsDashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [showMCQEditor, setShowMCQEditor] = useState(false);
  const [showSkillsForm, setShowSkillsForm] = useState(false);
  const [filters, setFilters] = useState({
    location: '',
    title: '',
    company: '',
    skip: 0,
    limit: 10
  });
  const [locationSuggestions, setLocationSuggestions] = useState([]);
  const [titleSuggestions, setTitleSuggestions] = useState([]);
  const [companySuggestions, setCompanySuggestions] = useState([]);
  const [showLocationSuggestions, setShowLocationSuggestions] = useState(false);
  const [showTitleSuggestions, setShowTitleSuggestions] = useState(false);
  const [showCompanySuggestions, setShowCompanySuggestions] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    location: '',
    salary_min: '',
    salary_max: '',
    domain: '',
    total_years_required: '',
    job_description: '',
    recruiter_id: '',  // Add recruiter assignment
    skills: []  // Array for skill-specific experience
  });
  const [skillsData, setSkillsData] = useState({
    skill: '',
    min_experience: ''
  });
  const [recruiters, setRecruiters] = useState([]);
  const [loadingRecruiters, setLoadingRecruiters] = useState(false);

  // Normalize a job record from the API into our local form shape
  const normalizeJobToForm = (jobObj) => {
    if (!jobObj) return {
      title: '', company: '', location: '', salary_min: '', salary_max: '', domain: '', total_years_required: '', job_description: '', recruiter_id: '', skills: []
    };
    const mappedSkills = Array.isArray(jobObj.mandatory_skills)
      ? jobObj.mandatory_skills.map((s) => ({
          skill: s.skill || s.name || '',
          min_experience: s.min_experience ?? s.min_years_experience ?? 0,
        }))
      : (Array.isArray(jobObj.skills) ? jobObj.skills : []);
    return {
      title: jobObj.title || '',
      company: jobObj.company || '',
      location: jobObj.location || '',
      salary_min: jobObj.salary_min ?? '',
      salary_max: jobObj.salary_max ?? '',
      domain: jobObj.domain || '',
      total_years_required: jobObj.total_years_required ?? '',
      job_description: jobObj.job_description || '',
      recruiter_id: jobObj.recruiter_id || '',
      skills: mappedSkills || [],
    };
  };

  // Debug: Log when jobs state changes
  useEffect(() => {
    console.log('🔄 Jobs state changed:', jobs);
    console.log('📊 Jobs length:', jobs.length);
    if (jobs.length > 0) {
      console.log('🔍 First job in state:', jobs[0]);
    }
  }, [jobs]);

  // Debug: Log when component renders
  useEffect(() => {
    console.log('🎨 JobsDashboard component rendered');
    console.log('📋 Current jobs state:', jobs);
    console.log('⏳ Loading state:', loading);
    console.log('❌ Error state:', error);
  });

  useEffect(() => {
    fetchJobs();
  }, [filters]);

  // Fetch recruiters on component mount
  useEffect(() => {
    const fetchRecruiters = async () => {
      setLoadingRecruiters(true);
      try {
        const response = await fetch('http://localhost:8000/api/v1/jobs-fast/recruiters-fast');
        if (response.ok) {
          const data = await response.json();
          setRecruiters(data);
        }
      } catch (error) {
        console.error('Error fetching recruiters:', error);
      } finally {
        setLoadingRecruiters(false);
      }
    };

    fetchRecruiters();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      console.log('Fetching jobs with filters:', filters);
      
      const queryParams = new URLSearchParams({
        skip: filters.skip,
        limit: filters.limit,
        ...(filters.location && { location: filters.location }),
        ...(filters.title && { title: filters.title }),
        ...(filters.company && { company: filters.company })
      });
      
      const url = `http://localhost:8000/api/v1/jobs/?${queryParams}`;
      console.log('Fetching from URL:', url);
      
      const response = await fetch(url);
      console.log('Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Jobs data received:', data);
        console.log('Number of jobs:', data.length);
        setJobs(data);
        setError(''); // Clear any previous errors
      } else {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch jobs: ${errorMessage}`);
      }
    } catch (err) {
      console.error('Fetch jobs error:', err);
      setError('Failed to fetch jobs: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Autocomplete functions
  const fetchLocationSuggestions = async (query) => {
    if (query.length < 2) {
      setLocationSuggestions([]);
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/api/v1/jobs/autocomplete/locations?q=${encodeURIComponent(query)}&limit=5`);
      if (response.ok) {
        const data = await response.json();
        setLocationSuggestions(data.suggestions || []);
      }
    } catch (err) {
      console.error('Error fetching location suggestions:', err);
    }
  };

  const fetchTitleSuggestions = async (query) => {
    if (query.length < 2) {
      setTitleSuggestions([]);
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/api/v1/jobs/autocomplete/titles?q=${encodeURIComponent(query)}&limit=5`);
      if (response.ok) {
        const data = await response.json();
        setTitleSuggestions(data.suggestions || []);
      }
    } catch (err) {
      console.error('Error fetching title suggestions:', err);
    }
  };

  const fetchCompanySuggestions = async (query) => {
    if (query.length < 2) {
      setCompanySuggestions([]);
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/api/v1/jobs/autocomplete/companies?q=${encodeURIComponent(query)}&limit=5`);
      if (response.ok) {
        const data = await response.json();
        setCompanySuggestions(data.suggestions || []);
      }
    } catch (err) {
      console.error('Error fetching company suggestions:', err);
    }
  };

  const clearAllFilters = () => {
    setFilters({
      location: '',
      title: '',
      company: '',
      skip: 0,
      limit: 10
    });
  };

  const handleCreateJob = async (e) => {
    e.preventDefault();
    console.log('Form submitted with data:', formData);
    
    if (!formData.title || !formData.location || !formData.domain || !formData.job_description) {
      setError('Please fill in all required fields');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const jobData = {
        ...formData,
        salary_min: formData.salary_min ? parseInt(formData.salary_min) : null,
        salary_max: formData.salary_max ? parseInt(formData.salary_max) : null,
        total_years_required: formData.total_years_required ? parseInt(formData.total_years_required) : 0,
        recruiter_id: formData.recruiter_id ? parseInt(formData.recruiter_id) : null,
        mandatory_skills: formData.skills  // Include skills data
      };
      
      console.log('Sending job data:', jobData);
      
      const response = await fetch('http://localhost:8000/api/v1/jobs-fast/public-fast', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(jobData)
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Job created successfully:', result);
        
        // Reset form
        setFormData({
          title: '',
          company: '',
          location: '',
          salary_min: '',
          salary_max: '',
          domain: '',
          total_years_required: '',
          job_description: '',
          recruiter_id: '',
          skills: []
        });
        setSelectedJob(null);
        setShowForm(false);
        
        // Refresh jobs list
        fetchJobs();
        
        // Show success message
        alert('Job posted successfully! 🎉');
      } else {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to post job: ${errorMessage}`);
      }
    } catch (err) {
      console.error('Post job error:', err);
      setError('Failed to post job: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (!confirm('Are you sure you want to delete this job?')) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/jobs/${jobId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        // Show success animation
        const successMessage = document.createElement('div');
        successMessage.className = 'success-toast';
        successMessage.innerHTML = `
          <div class="success-icon">🗑️</div>
          <div class="success-text">Job deleted successfully!</div>
        `;
        document.body.appendChild(successMessage);
        
        setTimeout(() => {
          document.body.removeChild(successMessage);
        }, 3000);
        
        setSelectedJob(null);
        fetchJobs();
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to delete job: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const addSkill = () => {
    if (skillsData.skill && skillsData.min_experience) {
      setFormData({
        ...formData,
        skills: [...formData.skills, {
          skill: skillsData.skill,
          min_experience: parseInt(skillsData.min_experience)
        }]
      });
      setSkillsData({ skill: '', min_experience: '' });
    }
  };

  const removeSkill = (index) => {
    const newSkills = formData.skills.filter((_, i) => i !== index);
    setFormData({ ...formData, skills: newSkills });
  };

  return (
    <div className="modern-jobs-dashboard">
      {/* Header Section */}
      <div className="unified-header">
        <div className="header-content">
          <h1 className="header-title">
            <span className="title-icon">💼</span>
            Jobs Dashboard
          </h1>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={() => window.location.href = '/company-admin'}>
            🏢 Company Admin
          </button>
          <button className="btn-secondary" onClick={() => window.location.href = '/job-assignments'}>
            📋 View Assignments
          </button>
          <button className="btn-back" onClick={() => window.location.href = '/recruiter/dashboard'}>
            ← Back to Dashboard
          </button>
          <button 
            className="btn-post-job"
            aria-label="Post new job"
            onClick={() => {
              setSelectedJob(null);  // Clear selected job for new job creation
              setShowForm(true);
            }}
          >
            <span className="btn-icon">➕</span>
            Post New Job
          </button>
        </div>
      </div>

      {/* Main Content - Sidebar Layout */}
      <div className="dashboard-layout">
        {/* Left Sidebar - Search Filters */}
        <div className="filters-sidebar">
          <div className="sidebar-header">
            <h3 className="sidebar-title">Search & Filter Jobs</h3>
            <button 
              className="btn-clear-filters"
              onClick={clearAllFilters}
              title="Clear all filters"
            >
              Clear All
            </button>
          </div>

          {/* Job Filters */}
          <div className="filter-section">
            
            {/* Location Filter with Autocomplete */}
            <div className="filter-group autocomplete-group">
              <label htmlFor="filter-location">Location</label>
              <div className="autocomplete-wrapper">
                <input
                  id="filter-location"
                  type="text"
                  placeholder="e.g., New York, USA"
                  value={filters.location}
                  onChange={(e) => {
                    setFilters({...filters, location: e.target.value});
                    fetchLocationSuggestions(e.target.value);
                    setShowLocationSuggestions(true);
                  }}
                  onBlur={() => setTimeout(() => setShowLocationSuggestions(false), 200)}
                  className="filter-input"
                />
                {showLocationSuggestions && locationSuggestions.length > 0 && (
                  <div className="autocomplete-dropdown">
                    {locationSuggestions.map((suggestion, index) => (
                      <div
                        key={index}
                        className="autocomplete-item"
                        onClick={() => {
                          setFilters({...filters, location: suggestion});
                          setShowLocationSuggestions(false);
                        }}
                      >
                        {suggestion}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Job Title Filter with Autocomplete */}
            <div className="filter-group autocomplete-group">
              <label htmlFor="filter-title">Job Title</label>
              <div className="autocomplete-wrapper">
                <input
                  id="filter-title"
                  type="text"
                  placeholder="e.g., Software Engineer"
                  value={filters.title}
                  onChange={(e) => {
                    setFilters({...filters, title: e.target.value});
                    fetchTitleSuggestions(e.target.value);
                    setShowTitleSuggestions(true);
                  }}
                  onBlur={() => setTimeout(() => setShowTitleSuggestions(false), 200)}
                  className="filter-input"
                />
                {showTitleSuggestions && titleSuggestions.length > 0 && (
                  <div className="autocomplete-dropdown">
                    {titleSuggestions.map((suggestion, index) => (
                      <div
                        key={index}
                        className="autocomplete-item"
                        onClick={() => {
                          setFilters({...filters, title: suggestion});
                          setShowTitleSuggestions(false);
                        }}
                      >
                        {suggestion}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Company Filter with Autocomplete */}
            <div className="filter-group autocomplete-group">
              <label htmlFor="filter-company">Company</label>
              <div className="autocomplete-wrapper">
                <input
                  id="filter-company"
                  type="text"
                  placeholder="e.g., Google, Microsoft"
                  value={filters.company}
                  onChange={(e) => {
                    setFilters({...filters, company: e.target.value});
                    fetchCompanySuggestions(e.target.value);
                    setShowCompanySuggestions(true);
                  }}
                  onBlur={() => setTimeout(() => setShowCompanySuggestions(false), 200)}
                  className="filter-input"
                />
                {showCompanySuggestions && companySuggestions.length > 0 && (
                  <div className="autocomplete-dropdown">
                    {companySuggestions.map((suggestion, index) => (
                      <div
                        key={index}
                        className="autocomplete-item"
                        onClick={() => {
                          setFilters({...filters, company: suggestion});
                          setShowCompanySuggestions(false);
                        }}
                      >
                        {suggestion}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>

        {/* Right Side - Job Results */}
        <div className="jobs-content">
          {/* Error Message */}
          {error && (
            <div className="error-banner" role="alert" aria-live="polite">
              <span className="error-icon">⚠️</span>
              {error}
              <button 
                className="error-close"
                onClick={() => setError('')}
              >
                ✕
              </button>
            </div>
          )}

          {/* Results Header */}
          <div className="results-header">
            <h2 className="results-title">
              Job Results ({jobs.length})
              {loading && <span className="loading-spinner">⏳</span>}
            </h2>
            <div className="results-info">
              {Object.values(filters).some(value => value && value !== 0 && value !== 10) && (
                <span className="filters-active">Filters Active</span>
              )}
            </div>
          </div>
          
          {jobs.length === 0 && !loading ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h3>No jobs found</h3>
              <p>Try adjusting your search filters or post your first job!</p>
              <div className="empty-actions">
                <button 
                  className="btn-primary"
                  onClick={() => {
                    setSelectedJob(null);  // Clear selected job for new job creation
                    setShowForm(true);
                  }}
                >
                  <span className="btn-icon">➕</span>
                  Post New Job
                </button>
                <button 
                  className="btn-secondary"
                  onClick={clearAllFilters}
                >
                  <span className="btn-icon">🗑️</span>
                  Clear Filters
                </button>
              </div>
            </div>
          ) : (
            <div className="jobs-grid">
              {jobs.map((job, index) => {
                console.log(`Rendering job ${index}:`, job);
                return (
                  <div 
                    key={job.id} 
                    className="job-card"
                    onClick={() => setSelectedJob(job)}
                  >
                    <div className="card-header">
                      <h3 className="job-title">{job.title || 'No Title'}</h3>
                      <div className="job-company">{job.company || 'No Company'}</div>
                    </div>
                    
                    <div className="card-content">
                      <div className="job-details">
                        <div className="detail-item">
                          <span className="detail-icon">📍</span>
                          <span style={{color: '#2c3e50', fontWeight: 'bold', fontSize: '14px'}}>{job.location || 'No Location'}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-icon">🏢</span>
                          <span style={{color: '#2c3e50', fontWeight: 'bold', fontSize: '14px'}}>{job.domain || 'No Domain'}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-icon">💰</span>
                          <span style={{color: '#2c3e50', fontWeight: 'bold', fontSize: '14px'}}>${job.salary_min?.toLocaleString() || '0'} - ${job.salary_max?.toLocaleString() || '0'}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-icon">⏱️</span>
                          <span style={{color: '#2c3e50', fontWeight: 'bold', fontSize: '14px'}}>{job.total_years_required || '0'} years experience</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="card-actions">
                      <button 
                        className="btn-edit"
                        aria-label={`Edit job ${job.title || 'job'}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          setFormData(normalizeJobToForm(job));
                          setSelectedJob(job);
                          setShowForm(true);
                        }}
                      >
                        ✏️ Edit
                      </button>
                      <button 
                        className="btn-mcq"
                        aria-label={`Manage MCQs for ${job.title || 'job'}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedJob(job);
                          setShowMCQEditor(true);
                        }}
                      >
                        📝 MCQs
                      </button>
                      <button 
                        className="btn-delete"
                        aria-label={`Delete job ${job.title || 'job'}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteJob(job.id);
                        }}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Modern Job Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modern-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">
                {selectedJob ? 'Edit Job' : 'Post New Job'}
              </h2>
              <button 
                className="modal-close"
                onClick={() => setShowForm(false)}
              >
                ✕
              </button>
            </div>
            
            <form onSubmit={handleCreateJob} className="modern-form">
              {/* Basic Job Information */}
              <div className="form-section">
                <h3 className="section-title">Basic Information</h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label">
                      Job Title <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => setFormData({...formData, title: e.target.value})}
                      required
                      placeholder="e.g., Senior Python Developer"
                      className="form-input"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="form-label">Company</label>
                    <input
                      type="text"
                      value={formData.company}
                      onChange={(e) => setFormData({...formData, company: e.target.value})}
                      placeholder="e.g., Tech Corp"
                      className="form-input"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="form-label">
                      Location <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.location}
                      onChange={(e) => setFormData({...formData, location: e.target.value})}
                      required
                      placeholder="e.g., New York, NY"
                      className="form-input"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="form-label">
                      Domain <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.domain}
                      onChange={(e) => setFormData({...formData, domain: e.target.value})}
                      required
                      placeholder="e.g., Software Development"
                      className="form-input"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="form-label">Assigned Recruiter</label>
                    <select
                      value={formData.recruiter_id}
                      onChange={(e) => setFormData({...formData, recruiter_id: e.target.value})}
                      className="form-input"
                    >
                      <option value="">Select recruiter (optional)</option>
                      {loadingRecruiters ? (
                        <option disabled>Loading recruiters...</option>
                      ) : (
                        recruiters.map(recruiter => (
                          <option key={recruiter.id} value={recruiter.id}>
                            {recruiter.name} ({recruiter.email})
                          </option>
                        ))
                      )}
                    </select>
                    <small style={{color: '#666', fontSize: '12px', marginTop: '4px', display: 'block'}}>
                      Leave empty to assign later or for admin assignment
                    </small>
                  </div>
                </div>
              </div>

              {/* Salary and Experience */}
              <div className="form-section">
                <h3 className="section-title">Salary & Experience</h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label">Min Salary</label>
                    <input
                      type="number"
                      value={formData.salary_min}
                      onChange={(e) => setFormData({...formData, salary_min: e.target.value})}
                      placeholder="0"
                      min="0"
                      className="form-input"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="form-label">Max Salary</label>
                    <input
                      type="number"
                      value={formData.salary_max}
                      onChange={(e) => setFormData({...formData, salary_max: e.target.value})}
                      placeholder="0"
                      min="0"
                      className="form-input"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="form-label">Total Experience Required</label>
                    <input
                      type="number"
                      value={formData.total_years_required}
                      onChange={(e) => setFormData({...formData, total_years_required: e.target.value})}
                      placeholder="0"
                      min="0"
                      max="50"
                      className="form-input"
                    />
                  </div>
                </div>
              </div>

              {/* Skill-Specific Experience */}
              <div className="form-section">
                <h3 className="section-title">Skill-Specific Experience</h3>
                <p className="section-description">
                  Add specific skills and their required experience (e.g., Python: 2 years, SQL: 3 years)
                </p>
                
                <div className="skills-input-group">
                  <div className="skill-input-row">
                    <div className="form-group">
                      <label className="form-label">Skill</label>
                      <input
                        type="text"
                        value={skillsData.skill}
                        onChange={(e) => setSkillsData({...skillsData, skill: e.target.value})}
                        placeholder="e.g., Python, SQL, React"
                        className="form-input"
                      />
                    </div>
                    
                    <div className="form-group">
                      <label className="form-label">Min Experience (years)</label>
                      <input
                        type="number"
                        value={skillsData.min_experience}
                        onChange={(e) => setSkillsData({...skillsData, min_experience: e.target.value})}
                        placeholder="2"
                        min="0"
                        max="20"
                        className="form-input"
                      />
                    </div>
                    
                    <button
                      type="button"
                      onClick={addSkill}
                      className="btn-add-skill"
                    >
                      Add Skill
                    </button>
                  </div>
                </div>

                {/* Display Added Skills */}
                {Array.isArray(formData.skills) && formData.skills.length > 0 && (
                  <div className="skills-list">
                    <h4>Added Skills:</h4>
                    {formData.skills.map((skill, index) => (
                      <div key={index} className="skill-item">
                        <span className="skill-name">{skill.skill}</span>
                        <span className="skill-experience">{skill.min_experience} years</span>
                        <button
                          type="button"
                          onClick={() => removeSkill(index)}
                          className="btn-remove-skill"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Job Description */}
              <div className="form-section">
                <h3 className="section-title">Job Description</h3>
                <div className="form-group full-width">
                  <label className="form-label">
                    Job Description <span className="required">*</span>
                  </label>
                  <textarea
                    value={formData.job_description}
                    onChange={(e) => setFormData({...formData, job_description: e.target.value})}
                    required
                    rows="6"
                    placeholder="Enter detailed job description, requirements, and responsibilities..."
                    className="form-textarea"
                  />
                </div>
              </div>
              
              <div className="form-actions">
                <button 
                  type="submit" 
                  className="btn-submit"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className="loading-spinner">⏳</span>
                      Posting...
                    </>
                  ) : (
                    <>
                      <span className="btn-icon">🚀</span>
                      {selectedJob ? 'Update Job' : 'Post Job'}
                    </>
                  )}
                </button>
                <button 
                  type="button" 
                  className="btn-cancel"
                  onClick={() => {
                    setShowForm(false);
                    setSelectedJob(null);
                    setFormData({
                      title: '',
                      company: '',
                      location: '',
                      salary_min: '',
                      salary_max: '',
                      domain: '',
                      total_years_required: '',
                      job_description: '',
                      recruiter_id: '',
                      skills: []
                    });
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MCQ Editor Modal */}
      {showMCQEditor && selectedJob && (
        <div className="modal-overlay" onClick={() => setShowMCQEditor(false)}>
          <div className="modern-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">
                Assessment Questions - {selectedJob.title}
              </h2>
              <button 
                className="modal-close"
                onClick={() => setShowMCQEditor(false)}
              >
                ✕
              </button>
            </div>
            
            <div className="modal-content">
              <RecruiterMCQEditor 
                jobId={selectedJob.id} 
                onSaved={() => {
                  setShowMCQEditor(false);
                  setSelectedJob(null);
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobsDashboard; 