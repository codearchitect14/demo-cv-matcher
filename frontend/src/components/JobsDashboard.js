import React, { useState, useEffect } from 'react';
import './JobsDashboard.css';

const JobsDashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [showSkillsForm, setShowSkillsForm] = useState(false);
  const [filters, setFilters] = useState({
    location: '',
    skip: 0,
    limit: 10
  });
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    location: '',
    salary_min: '',
    salary_max: '',
    domain: '',
    total_years_required: '',
    job_description: '',
    skills: []  // Array for skill-specific experience
  });
  const [skillsData, setSkillsData] = useState({
    skill: '',
    min_experience: ''
  });

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

  const fetchJobs = async () => {
    setLoading(true);
    try {
      console.log('Fetching jobs...');
      
      const queryParams = new URLSearchParams({
        skip: filters.skip,
        limit: filters.limit,
        ...(filters.location && { location: filters.location })
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
        mandatory_skills: formData.skills  // Include skills data
      };
      
      console.log('Sending job data:', jobData);
      
      const response = await fetch('http://localhost:8000/api/v1/jobs/public', {
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
      <div className="dashboard-header">
        <div className="header-content">
          <h1 className="header-title">
            <span className="title-icon">💼</span>
            Jobs Dashboard
          </h1>
          <p className="header-subtitle">Manage and track your job postings</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-post-job"
            onClick={() => setShowForm(true)}
          >
            <span className="btn-icon">➕</span>
            Post New Job
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="dashboard-content">
        {/* Filters Section */}
        <div className="filters-section">
          <div className="filter-group">
            <label>Location</label>
            <input
              type="text"
              placeholder="Filter by location"
              value={filters.location}
              onChange={(e) => setFilters({...filters, location: e.target.value})}
              className="filter-input"
            />
          </div>
          <div className="filter-group">
            <label>Limit</label>
            <select
              value={filters.limit}
              onChange={(e) => setFilters({...filters, limit: parseInt(e.target.value)})}
              className="filter-select"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-banner">
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

        {/* Jobs Grid */}
        <div className="jobs-section">
          <h2 className="section-title">
            Jobs ({jobs.length})
            {loading && <span className="loading-spinner">⏳</span>}
          </h2>
          
          {jobs.length === 0 && !loading ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h3>No jobs found</h3>
              <p>Start by posting your first job!</p>
              <button 
                className="btn-primary"
                onClick={() => setShowForm(true)}
              >
                Post Your First Job
              </button>
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
                        onClick={(e) => {
                          e.stopPropagation();
                          setFormData(job);
                          setSelectedJob(job);
                          setShowForm(true);
                        }}
                      >
                        ✏️ Edit
                      </button>
                      <button 
                        className="btn-delete"
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
                {formData.skills.length > 0 && (
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
                      job_description: ''
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
    </div>
  );
};

export default JobsDashboard; 