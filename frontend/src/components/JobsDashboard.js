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
    job_description: ''
  });
  const [skillsData, setSkillsData] = useState({
    skill: '',
    description: ''
  });

  useEffect(() => {
    fetchJobs();
  }, [filters]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const queryParams = new URLSearchParams({
        skip: filters.skip,
        limit: filters.limit,
        ...(filters.location && { location: filters.location })
      });
      
      const response = await fetch(`http://localhost:8000/api/v1/jobs/?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setJobs(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch jobs: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const fetchJobDetails = async (jobId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/jobs/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedJob(data);
        fetchJobApplications(jobId);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch job details: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to fetch job details');
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

  const handleCreateJob = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/jobs/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      if (response.ok) {
        alert('Job created successfully!');
        setShowForm(false);
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
        fetchJobs();
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to create job: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateJob = async (jobId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/jobs/${jobId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      if (response.ok) {
        alert('Job updated successfully!');
        setSelectedJob(null);
        fetchJobs();
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to update job: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
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
        alert('Job deleted successfully!');
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

  const handleAddMandatorySkill = async (jobId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/jobs/${jobId}/mandatory-skills`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(skillsData)
      });
      if (response.ok) {
        alert('Mandatory skill added successfully!');
        setShowSkillsForm(false);
        setSkillsData({ skill: '', description: '' });
        fetchJobDetails(jobId);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to add mandatory skill: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="jobs-dashboard">
      <div className="dashboard-header">
        <h1>Jobs Dashboard</h1>
        <button 
          className="btn-primary"
          onClick={() => setShowForm(true)}
        >
          Post New Job
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="filters-section">
        <div className="filter-group">
          <label>Location:</label>
          <input
            type="text"
            placeholder="Filter by location"
            value={filters.location}
            onChange={(e) => setFilters({...filters, location: e.target.value})}
          />
        </div>
        <div className="filter-group">
          <label>Limit:</label>
          <select
            value={filters.limit}
            onChange={(e) => setFilters({...filters, limit: parseInt(e.target.value)})}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="jobs-list">
          <h2>Jobs ({jobs.length})</h2>
          {loading ? (
            <div className="loading">Loading jobs...</div>
          ) : (
            <div className="jobs-grid">
              {jobs.map(job => (
                <div 
                  key={job.id} 
                  className={`job-card ${selectedJob?.id === job.id ? 'selected' : ''}`}
                  onClick={() => fetchJobDetails(job.id)}
                >
                  <h3>{job.title}</h3>
                  <p><strong>Company:</strong> {job.company}</p>
                  <p><strong>Location:</strong> {job.location}</p>
                  <p><strong>Domain:</strong> {job.domain}</p>
                  <p><strong>Salary:</strong> ${job.salary_min} - ${job.salary_max}</p>
                  <p><strong>Experience:</strong> {job.total_years_required} years</p>
                  <div className="job-actions">
                    <button 
                      className="btn-edit"
                      onClick={(e) => {
                        e.stopPropagation();
                        setFormData(job);
                        setSelectedJob(job);
                      }}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn-delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteJob(job.id);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedJob && (
          <div className="job-details">
            <h2>Job Details</h2>
            <div className="detail-section">
              <h3>Basic Information</h3>
              <p><strong>Title:</strong> {selectedJob.title}</p>
              <p><strong>Company:</strong> {selectedJob.company}</p>
              <p><strong>Location:</strong> {selectedJob.location}</p>
              <p><strong>Domain:</strong> {selectedJob.domain}</p>
              <p><strong>Salary Range:</strong> ${selectedJob.salary_min} - ${selectedJob.salary_max}</p>
              <p><strong>Experience Required:</strong> {selectedJob.total_years_required} years</p>
              <p><strong>Description:</strong></p>
              <div className="job-description">
                {selectedJob.job_description}
              </div>
            </div>

            <div className="detail-section">
              <h3>Mandatory Skills</h3>
              <button 
                className="btn-secondary"
                onClick={() => setShowSkillsForm(true)}
              >
                Add Mandatory Skill
              </button>
              {selectedJob.mandatory_skills?.map(skill => (
                <div key={skill.id} className="skill-item">
                  <p><strong>{skill.skill}</strong></p>
                  <p>{skill.description}</p>
                </div>
              ))}
            </div>

            <div className="detail-section">
              <h3>Applications ({applications.length})</h3>
              {applications.map(app => (
                <div key={app.id} className="application-item">
                  <p><strong>Candidate:</strong> {app.candidate?.name}</p>
                  <p><strong>Status:</strong> {app.status}</p>
                  <p><strong>Applied:</strong> {new Date(app.created_at).toLocaleDateString()}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Job Form */}
      {showForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>{selectedJob ? 'Edit Job' : 'Post New Job'}</h2>
            <form onSubmit={selectedJob ? (e) => { e.preventDefault(); handleUpdateJob(selectedJob.id); } : handleCreateJob}>
              <div className="form-group">
                <label>Job Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Company</label>
                <input
                  type="text"
                  value={formData.company}
                  onChange={(e) => setFormData({...formData, company: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Location</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                  required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Min Salary</label>
                  <input
                    type="number"
                    value={formData.salary_min}
                    onChange={(e) => setFormData({...formData, salary_min: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Max Salary</label>
                  <input
                    type="number"
                    value={formData.salary_max}
                    onChange={(e) => setFormData({...formData, salary_max: e.target.value})}
                    required
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Domain</label>
                <input
                  type="text"
                  value={formData.domain}
                  onChange={(e) => setFormData({...formData, domain: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Years of Experience Required</label>
                <input
                  type="number"
                  value={formData.total_years_required}
                  onChange={(e) => setFormData({...formData, total_years_required: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Job Description</label>
                <textarea
                  value={formData.job_description}
                  onChange={(e) => setFormData({...formData, job_description: e.target.value})}
                  required
                  rows="6"
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : (selectedJob ? 'Update' : 'Post Job')}
                </button>
                <button 
                  type="button" 
                  className="btn-secondary"
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

      {/* Add Mandatory Skill Form */}
      {showSkillsForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Add Mandatory Skill</h2>
            <form onSubmit={(e) => { e.preventDefault(); handleAddMandatorySkill(selectedJob.id); }}>
              <div className="form-group">
                <label>Skill Name</label>
                <input
                  type="text"
                  value={skillsData.skill}
                  onChange={(e) => setSkillsData({...skillsData, skill: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={skillsData.description}
                  onChange={(e) => setSkillsData({...skillsData, description: e.target.value})}
                  required
                  rows="4"
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : 'Add Skill'}
                </button>
                <button 
                  type="button" 
                  className="btn-secondary"
                  onClick={() => {
                    setShowSkillsForm(false);
                    setSkillsData({ skill: '', description: '' });
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