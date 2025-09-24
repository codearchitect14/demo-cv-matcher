import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './CandidatesDashboard.css';

const CandidatesDashboard = () => {
  const navigate = useNavigate();
  const [userProfile, setUserProfile] = useState(null);
  const [applications, setApplications] = useState([]);
  const [jobRecommendations, setJobRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [showJobModal, setShowJobModal] = useState(false);
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [showCVUpload, setShowCVUpload] = useState(false);
  const [cvFile, setCvFile] = useState(null);
  const [showSkillsManagement, setShowSkillsManagement] = useState(false);
  const [skills, setSkills] = useState([]);
  const [showAddSkillForm, setShowAddSkillForm] = useState(false);
  const [editingSkill, setEditingSkill] = useState(null);
  const [pendingSkills, setPendingSkills] = useState([]);
  
  const [profileData, setProfileData] = useState({
    name: '', email: '', location: '', domain: '',
    expected_salary_min: '', expected_salary_max: '', summary: '',
    phone: '', linkedin_url: '', github_url: '', total_experience_years: ''
  });

  const [skillFormData, setSkillFormData] = useState({
    skill: '',
    years: '',
    description: ''
  });

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.log('No authentication token found, redirecting to login');
      navigate('/login-new');
      return;
    }
    
    fetchUserProfile();
    fetchApplications();
    fetchJobRecommendations();
    fetchSkills();
  }, [navigate]);

  const fetchUserProfile = async () => {
    try {
      console.log('Fetching user profile...');
      const token = localStorage.getItem('access_token');
      console.log('Token available:', !!token);
      
      if (!token) {
        console.log('No token found, using default profile');
        setUserProfile({
          name: 'Demo Candidate',
          email: 'demo@example.com'
        });
        return;
      }
      
      const response = await fetch('http://localhost:8000/api/v1/candidates/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Profile response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('User profile data:', data);
        setUserProfile(data);
        setProfileData({
          name: data.name || '',
          email: data.email || '',
          location: data.location || '',
          domain: data.domain || '',
          expected_salary_min: data.expected_salary_min || '',
          expected_salary_max: data.expected_salary_max || '',
          summary: data.summary || '',
          phone: data.phone || '',
          linkedin_url: data.linkedin_url || '',
          github_url: data.github_url || '',
          total_experience_years: data.total_experience_years || ''
        });
      } else if (response.status === 401) {
        console.log('Unauthorized - using default profile');
        setUserProfile({
          name: 'Demo Candidate',
          email: 'demo@example.com'
        });
      } else {
        console.error('Failed to fetch user profile:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Profile error details:', errorText);
        setUserProfile({
          name: 'Demo Candidate',
          email: 'demo@example.com'
        });
      }
    } catch (error) {
      console.error('Error fetching user profile:', error);
      setUserProfile({
        name: 'Demo Candidate',
        email: 'demo@example.com'
      });
    }
  };

  const fetchApplications = async () => {
    try {
      console.log('Fetching applications...');
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        console.log('No token found, using empty applications');
        setApplications([]);
        return;
      }
      
      // First try the authenticated endpoint
      let response = await fetch('http://localhost:8000/api/v1/applications/my-applications', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Applications response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Applications data:', data);
        setApplications(data);
             } else if (response.status === 401 || response.status === 422) {
         console.log('Authentication issue - using empty applications for now');
         setApplications([]);
      } else {
        console.error('Failed to fetch applications:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Applications error details:', errorText);
        setApplications([]);
      }
    } catch (error) {
      console.error('Error fetching applications:', error);
      setApplications([]);
    }
  };

  const fetchJobRecommendations = async () => {
    try {
      console.log('Fetching job recommendations...');
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        console.log('No token found, using empty recommendations');
        setJobRecommendations([]);
        return;
      }
      
      const response = await fetch('http://localhost:8000/api/v1/jobs/recommendations', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Recommendations response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Job recommendations data:', data);
        setJobRecommendations(data);
             } else {
         console.error('Failed to fetch job recommendations:', response.status, response.statusText);
         const errorText = await response.text();
         console.error('Recommendations error details:', errorText);
         // If recommendations fail, fetch all available jobs as fallback
         console.log('Falling back to fetch all jobs...');
         await fetchAllJobs();
       }
    } catch (error) {
      console.error('Error fetching job recommendations:', error);
      // If recommendations fail, fetch all available jobs as fallback
      await fetchAllJobs();
    }
  };

  const fetchAllJobs = async () => {
    try {
      console.log('Fetching all available jobs as fallback...');
      const response = await fetch('http://localhost:8000/api/v1/jobs/', {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('All jobs data:', data);
        // Limit to first 6 jobs for dashboard display
        setJobRecommendations(data.slice(0, 6));
      } else {
        console.error('Failed to fetch all jobs:', response.status);
        setJobRecommendations([]);
      }
    } catch (error) {
      console.error('Error fetching all jobs:', error);
      setJobRecommendations([]);
    }
  };

  const handleApplyToRecommendedJob = async (jobId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        setError('Please log in to apply for jobs');
        return;
      }
      
      const response = await fetch('http://localhost:8000/api/v1/applications/public', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          job_id: jobId,
          candidate_id: userProfile?.id,
          status: 'APPLIED'
        })
      });

      if (response.ok) {
        const responseData = await response.json();
        
        // Check the message to determine if it's a new application or already applied
        if (responseData.message === "You have already applied to this job!") {
          setMessage('You have already applied to this job!');
          // Update the job recommendation to show as applied
          setJobRecommendations(prev => prev.map(job => 
            job.id === jobId ? { ...job, applied: true } : job
          ));
        } else {
          setMessage('Application submitted successfully!');
          // Refresh applications list
          fetchApplications();
          // Remove the applied job from recommendations
          setJobRecommendations(prev => prev.filter(job => job.id !== jobId));
        }
      } else {
        const errorData = await response.json();
        // Handle validation errors properly
        if (errorData.detail && typeof errorData.detail === 'object') {
          // This is a validation error object
          const errorMessages = [];
          if (Array.isArray(errorData.detail)) {
            errorData.detail.forEach(err => {
              if (err.msg) {
                errorMessages.push(err.msg);
              }
            });
          } else if (errorData.detail.msg) {
            errorMessages.push(errorData.detail.msg);
          }
          setError(errorMessages.join(', ') || 'Validation error occurred');
        } else {
          setError(typeof errorData.detail === 'string' ? errorData.detail : 'Failed to apply for job');
        }
      }
    } catch (error) {
      console.error('Error applying to job:', error);
      setError('Failed to apply for job. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleViewJobDetails = (job) => {
    setSelectedJob(job);
    setShowJobModal(true);
  };

  const closeJobDetails = () => {
    setShowJobModal(false);
    setSelectedJob(null);
  };

  // Skills Management Functions
  const fetchSkills = async () => {
    try {
      console.log('Fetching skills...');
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        console.log('No token found, using empty skills');
        setSkills([]);
        return;
      }
      
      // Get skills from user profile (experiences)
      const response = await fetch('http://localhost:8000/api/v1/candidates/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const profile = await response.json();
        console.log('Profile with experiences:', profile);
        setSkills(profile.experiences || []);
      } else {
        console.error('Failed to fetch skills:', response.status);
        setSkills([]);
      }
    } catch (error) {
      console.error('Error fetching skills:', error);
      setSkills([]);
    }
  };

  const handleAddSkillToPending = (e) => {
    e.preventDefault();
    
    // Validate form data
    if (!skillFormData.skill.trim() || !skillFormData.years) {
      setError('Please fill in skill name and years of experience');
      return;
    }
    
    // Add to pending skills
    const newSkill = {
      id: Date.now(), // Temporary ID for frontend
      skill: skillFormData.skill.trim(),
      years: parseInt(skillFormData.years),
      description: skillFormData.description.trim() || null,
      isNew: true
    };
    
    setPendingSkills([...pendingSkills, newSkill]);
    setSkillFormData({ skill: '', years: '', description: '' });
    setError('');
  };

  const handleRemovePendingSkill = (skillId) => {
    setPendingSkills(pendingSkills.filter(skill => skill.id !== skillId));
  };

  const handleSaveAllSkills = async () => {
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const token = localStorage.getItem('access_token');
      let successCount = 0;
      let errorCount = 0;

      // Save each pending skill
      for (const skill of pendingSkills) {
        try {
          const response = await fetch(`http://localhost:8000/api/v1/candidates/${userProfile.id}/experience`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              skill: skill.skill,
              years: skill.years,
              description: skill.description
            })
          });

          if (response.ok) {
            successCount++;
          } else {
            errorCount++;
          }
        } catch (error) {
          errorCount++;
        }
      }

      if (successCount > 0) {
        setMessage(`${successCount} skill${successCount > 1 ? 's' : ''} added successfully!`);
        setPendingSkills([]);
        fetchSkills(); // Refresh skills list
      }
      
      if (errorCount > 0) {
        setError(`Failed to add ${errorCount} skill${errorCount > 1 ? 's' : ''}. Please try again.`);
      }
    } catch (error) {
      setError('Failed to save skills. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEditSkill = (skill) => {
    setEditingSkill(skill);
    setSkillFormData({
      skill: skill.skill,
      years: skill.years.toString(),
      description: skill.description || ''
    });
    setShowAddSkillForm(true);
  };

  const handleUpdateSkill = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/candidates/${userProfile.id}/experience/${editingSkill.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          skill: skillFormData.skill,
          years: parseInt(skillFormData.years),
          description: skillFormData.description.trim() || null
        })
      });

      if (response.ok) {
        setMessage('Skill updated successfully!');
        setSkillFormData({ skill: '', years: '', description: '' });
        setEditingSkill(null);
        setShowAddSkillForm(false);
        fetchSkills(); // Refresh skills list
      } else {
        const errorData = await response.json();
        setError(typeof errorData.detail === 'string' ? errorData.detail : 'Failed to update skill');
      }
    } catch (error) {
      setError('Failed to update skill');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSkill = async (skillId) => {
    if (!window.confirm('Are you sure you want to delete this skill?')) {
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/candidates/${userProfile.id}/experience/${skillId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setMessage('Skill deleted successfully!');
        fetchSkills(); // Refresh skills list
      } else {
        const errorData = await response.json();
        setError(typeof errorData.detail === 'string' ? errorData.detail : 'Failed to delete skill');
      }
    } catch (error) {
      setError('Failed to delete skill');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/candidates/me', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileData)
      });

      if (response.ok) {
        setMessage('Profile updated successfully!');
        setShowProfileForm(false);
        fetchUserProfile();
      } else {
        const errorData = await response.json();
        setError(typeof errorData.detail === 'string' ? errorData.detail : 'Failed to update profile');
      }
    } catch (error) {
      setError('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleCVUpload = async (e) => {
    e.preventDefault();
    if (!cvFile) {
      setError('Please select a CV file');
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    try {
      const token = localStorage.getItem('access_token');
      const formData = new FormData();
      formData.append('cv_file', cvFile);

      const response = await fetch('http://localhost:8000/api/v1/candidates/upload-cv', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        setMessage('CV uploaded successfully!');
        setShowCVUpload(false);
        setCvFile(null);
      } else {
        const errorData = await response.json();
        setError(typeof errorData.detail === 'string' ? errorData.detail : 'Failed to upload CV');
      }
    } catch (error) {
      setError('Failed to upload CV');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyToJob = async (jobId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/applications/public', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          job_id: jobId,
          candidate_id: userProfile?.id,
          status: 'APPLIED'
        })
      });

      if (response.ok) {
        const responseData = await response.json();
        
        // Check the message to determine if it's a new application or already applied
        if (responseData.message === "You have already applied to this job!") {
          setMessage('You have already applied to this job!');
        } else {
          setMessage('Application submitted successfully!');
          fetchApplications();
        }
      } else {
        const errorData = await response.json();
        // Handle validation errors properly
        if (errorData.detail && typeof errorData.detail === 'object') {
          // This is a validation error object
          const errorMessages = [];
          if (Array.isArray(errorData.detail)) {
            errorData.detail.forEach(err => {
              if (err.msg) {
                errorMessages.push(err.msg);
              }
            });
          } else if (errorData.detail.msg) {
            errorMessages.push(errorData.detail.msg);
          }
          setError(errorMessages.join(', ') || 'Validation error occurred');
        } else {
          setError(typeof errorData.detail === 'string' ? errorData.detail : 'Failed to apply for job');
        }
      }
    } catch (error) {
      setError('Failed to apply for job');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    navigate('/login-new');
  };

  const getApplicationStatusColor = (status) => {
    switch (status) {
      case 'applied': return 'status-applied';
      case 'pending': return 'status-pending';
      case 'accepted': return 'status-accepted';
      case 'rejected': return 'status-rejected';
      default: return 'status-applied';
    }
  };

  const getApplicationStatusText = (status) => {
    switch (status) {
      case 'applied': return 'Applied';
      case 'pending': return 'Pending';
      case 'accepted': return 'Accepted';
      case 'rejected': return 'Rejected';
      default: return 'Applied';
    }
  };

  return (
    <div className="candidates-dashboard">
      {/* Professional Header */}
      <div className="unified-header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="header-title">Candidate Dashboard</h1>
            {userProfile && (
              <p className="welcome-text">Welcome back, {userProfile.name || 'Candidate'}!</p>
            )}
          </div>
          
          <div className="header-right">
            <button className="btn-secondary" onClick={() => navigate('/my-applications')}>
              <span>My applications</span>
            </button>
            <button className="btn-secondary" onClick={() => setShowSkillsManagement(true)}>
              <span>Manage Skills</span>
            </button>
            <button className="btn-profile" onClick={() => setShowProfileForm(true)}>
              <span>Profile</span>
            </button>
            <button className="btn-logout soft" onClick={handleLogout}>
              <span>Logout</span>
            </button>
          </div>
      </div>
      </div>

      {/* Main Content */}
      <div className="dashboard-content">
        {/* Summary Cards */}
        <div className="summary-cards">
          <div className="summary-card">
            <div className="card-icon documents">
              📋
            </div>
            <div className="card-content">
              <div className="card-count">{applications.length}</div>
              <div className="card-label">Total Applications</div>
            </div>
          </div>
          <div className="summary-card">
            <div className="card-icon pending">
              ⏳
            </div>
            <div className="card-content">
              <div className="card-count">{applications.filter(app => app.status === 'pending').length}</div>
              <div className="card-label">Pending Reviews</div>
            </div>
          </div>
          <div className="summary-card">
            <div className="card-icon accepted">
              ✅
            </div>
            <div className="card-content">
              <div className="card-count">{applications.filter(app => app.status === 'accepted').length}</div>
              <div className="card-label">Accepted</div>
            </div>
          </div>
          <div className="summary-card">
            <div className="card-icon recommendations">
              💼
            </div>
            <div className="card-content">
              <div className="card-count">{jobRecommendations.length}</div>
              <div className="card-label">Recommended Jobs</div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          <h2 className="section-title">Quick Actions</h2>
          <div className="actions-grid">
            <div className="action-card" onClick={() => setShowProfileForm(true)}>
              <div className="action-content">
                <h3>Update Profile</h3>
              </div>
              <div className="action-arrow">
                →
              </div>
            </div>
            <div className="action-card" onClick={() => setShowCVUpload(true)}>
              <div className="action-content">
                <h3>Upload CV</h3>
              </div>
              <div className="action-arrow">
                →
              </div>
            </div>
            <div className="action-card" onClick={() => navigate('/job-search')}>
              <div className="action-content">
                <h3>Search Jobs</h3>
              </div>
              <div className="action-arrow">
                →
              </div>
            </div>

          </div>
        </div>

        {/* Recent Applications removed per requirements */}

        {/* Recommended Jobs */}
        <div className="recommended-jobs">
          <h2 className="section-title">Recommended Jobs</h2>
          {jobRecommendations.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💼</div>
              <h3>No recommended jobs yet</h3>
              <p>Complete your profile to get personalized job recommendations!</p>
              <button 
                className="cta-button" 
                onClick={() => setShowProfileForm(true)}
              >
                👤 Complete Profile
              </button>
            </div>
          ) : (
            <div className="jobs-grid">
              {jobRecommendations.map((job, index) => (
              <div key={index} className="job-card">
                <div className="job-header">
                  <div className="job-logo">
                    {job.company ? job.company.charAt(0).toUpperCase() : '🏢'}
                  </div>
                  <div className="job-info">
                    <h3 className="job-title">{job.title}</h3>
                    <span className="company-name">{job.company}</span>
                  </div>
                </div>
                <div className="job-details">
                  <div className="job-meta">
                    <span className="location">📍 {job.location}</span>
                    <span className="salary">
                      💰 ${job.salary_min?.toLocaleString()} - ${job.salary_max?.toLocaleString()}
                    </span>
                  </div>
                  <div className="job-actions">
                    <button 
                      className="btn-view-details"
                      onClick={() => handleViewJobDetails(job)}
                    >
                      View Details
                    </button>
                    <button 
                      className="btn-apply-now"
                      onClick={() => handleApplyToRecommendedJob(job.id)}
                    >
                      Apply Now
                    </button>
                  </div>
                </div>
              </div>
            ))}
            </div>
          )}
        </div>
      </div>

      {/* Profile Update Modal */}
      {showJobModal && selectedJob && (
        <div className="modal-overlay" onClick={closeJobDetails}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedJob.title}</h3>
            </div>
            <div className="modal-body">
              <p><strong>Company:</strong> {selectedJob.company || '—'}</p>
              <p><strong>Location:</strong> {selectedJob.location || '—'}</p>
              <p><strong>Salary:</strong> {selectedJob.salary_min && selectedJob.salary_max ? `${selectedJob.salary_min} - ${selectedJob.salary_max}` : '—'}</p>
              {selectedJob.job_description && (
                <div>
                  <strong>Description:</strong>
                  <p>{selectedJob.job_description}</p>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-apply-now" onClick={() => handleApplyToRecommendedJob(selectedJob.id)}>Apply Now</button>
              <button className="btn-secondary" onClick={closeJobDetails}>Close</button>
            </div>
          </div>
        </div>
      )}
      {showProfileForm && (
        <div className="modal-overlay" onClick={() => setShowProfileForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header"></div>
            <form onSubmit={handleUpdateProfile}>
              <div className="form-row">
                <div className="form-group">
                  <label>Name</label>
                  <input
                    type="text"
                    value={profileData.name}
                    onChange={(e) => setProfileData({...profileData, name: e.target.value})}
                    required
                    placeholder="Enter your full name"
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={profileData.email}
                    onChange={(e) => setProfileData({...profileData, email: e.target.value})}
                    required
                    placeholder="Enter your email address"
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Location</label>
                  <input
                    type="text"
                    value={profileData.location}
                    onChange={(e) => setProfileData({...profileData, location: e.target.value})}
                    placeholder="City, Country"
                  />
                </div>
                <div className="form-group">
                  <label>Domain</label>
                  <input
                    type="text"
                    value={profileData.domain}
                    onChange={(e) => setProfileData({...profileData, domain: e.target.value})}
                    placeholder="e.g., Software Development"
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Total Professional Experience (Years)</label>
                  <input
                    type="number"
                    value={profileData.total_experience_years}
                    onChange={(e) => setProfileData({...profileData, total_experience_years: e.target.value})}
                    placeholder="0"
                    min="0"
                    max="50"
                    step="0.5"
                  />
                </div>
                <div className="form-group">
                  {/* Empty div to maintain two-column layout */}
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Expected Salary (Min)</label>
                  <input
                    type="number"
                    value={profileData.expected_salary_min}
                    onChange={(e) => setProfileData({...profileData, expected_salary_min: e.target.value})}
                    placeholder="Minimum salary"
                  />
                </div>
                <div className="form-group">
                  <label>Expected Salary (Max)</label>
                  <input
                    type="number"
                    value={profileData.expected_salary_max}
                    onChange={(e) => setProfileData({...profileData, expected_salary_max: e.target.value})}
                    placeholder="Maximum salary"
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>Professional Summary</label>
                <textarea
                  value={profileData.summary}
                  onChange={(e) => setProfileData({...profileData, summary: e.target.value})}
                  rows="4"
                  placeholder="Brief description of your experience and skills..."
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={profileData.phone}
                    onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
                <div className="form-group">
                  <label>LinkedIn URL</label>
                  <input
                    type="url"
                    value={profileData.linkedin_url}
                    onChange={(e) => setProfileData({...profileData, linkedin_url: e.target.value})}
                    placeholder="https://linkedin.com/in/yourprofile"
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>GitHub URL</label>
                <input
                  type="url"
                  value={profileData.github_url}
                  onChange={(e) => setProfileData({...profileData, github_url: e.target.value})}
                  placeholder="https://github.com/yourusername"
                />
              </div>
              
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowProfileForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-save" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CV Upload Modal */}
      {showCVUpload && (
        <div className="modal-overlay" onClick={() => setShowCVUpload(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Upload CV</h2>
            </div>
            <form onSubmit={handleCVUpload}>
              <div className="form-group">
                <label>Select CV File</label>
                <div className="file-upload">
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => setCvFile(e.target.files[0])}
                    required
                    id="cv-file"
                  />
                  <label 
                    htmlFor="cv-file" 
                    className={`file-upload-label ${cvFile ? 'has-file' : ''}`}
                  >
                    {cvFile ? (
                      <>
                        📄 {cvFile.name}
                        <div className="file-info">
                          File selected successfully
                        </div>
                      </>
                    ) : (
                      <>
                        📄 Click to select CV file
                        <div className="file-info">
                          Supported formats: PDF, DOC, DOCX (Max 10MB)
                        </div>
                      </>
                    )}
                  </label>
                </div>
              </div>
              
              <div className="form-group">
                <label>Additional Notes (Optional)</label>
                <textarea
                  placeholder="Any additional information about your CV or experience..."
                  rows="3"
                />
              </div>
              
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowCVUpload(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-save" disabled={loading || !cvFile}>
                  {loading ? 'Uploading...' : 'Upload CV'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Skills Management Modal */}
      {showSkillsManagement && (
        <div className="modal-overlay" onClick={() => setShowSkillsManagement(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header"></div>
            
            {/* Skills List Section */}
            <div className="skills-list-section">
              <div className="skills-header">
                <h3>Your Skills ({skills.length})</h3>
                <button 
                  className="btn-primary"
                  onClick={() => {
                    setShowAddSkillForm(true);
                    setEditingSkill(null);
                    setSkillFormData({ skill: '', years: '', description: '' });
                  }}
                >
                  + Add New Skill
                </button>
              </div>
              
              {skills.length === 0 ? (
                <div className="no-skills">
                  <p>No skills added yet. Add your first skill to get started!</p>
                </div>
              ) : (
                <div className="skills-list">
                  {skills.map((skill) => (
                    <div key={skill.id} className="skill-item">
                      <div className="skill-info">
                        <div className="skill-name">{skill.skill}</div>
                        <div className="skill-years">{skill.years} year{skill.years !== 1 ? 's' : ''} experience</div>
                        {skill.description && (
                          <div className="skill-description">{skill.description}</div>
                        )}
                      </div>
                      <div className="skill-actions">
                        <button 
                          className="btn-edit"
                          onClick={() => handleEditSkill(skill)}
                        >
                          Edit
                        </button>
                        <button 
                          className="btn-delete"
                          onClick={() => handleDeleteSkill(skill.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Pending Skills Section */}
            {pendingSkills.length > 0 && (
              <div className="pending-skills-section">
                <div className="pending-skills-header">
                  <h4>Skills to Add ({pendingSkills.length})</h4>
                  <button 
                    className="btn-save-all"
                    onClick={handleSaveAllSkills}
                    disabled={loading}
                  >
                    {loading ? 'Saving...' : 'Save All Skills'}
                  </button>
                </div>
                
                <div className="pending-skills-list">
                  {pendingSkills.map((skill) => (
                    <div key={skill.id} className="pending-skill-item">
                      <div className="pending-skill-info">
                        <div className="pending-skill-name">{skill.skill}</div>
                        <div className="pending-skill-years">{skill.years} year{skill.years !== 1 ? 's' : ''} experience</div>
                        {skill.description && (
                          <div className="pending-skill-description">{skill.description}</div>
                        )}
                      </div>
                      <button 
                        className="btn-remove-pending"
                        onClick={() => handleRemovePendingSkill(skill.id)}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Add/Edit Skill Form */}
            {showAddSkillForm && (
              <form onSubmit={editingSkill ? handleUpdateSkill : handleAddSkillToPending}>
                <div className="form-row">
                  <div className="form-group">
                    <label>Skill Name *</label>
                    <input
                      type="text"
                      value={skillFormData.skill}
                      onChange={(e) => setSkillFormData({...skillFormData, skill: e.target.value})}
                      placeholder="e.g., Python, JavaScript, React"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Years of Experience *</label>
                    <input
                      type="number"
                      value={skillFormData.years}
                      onChange={(e) => setSkillFormData({...skillFormData, years: e.target.value})}
                      placeholder="0"
                      min="0"
                      max="20"
                      required
                    />
                  </div>
                </div>
                
                <div className="form-group">
                  <label>Description (Optional)</label>
                  <textarea
                    value={skillFormData.description}
                    onChange={(e) => setSkillFormData({...skillFormData, description: e.target.value})}
                    placeholder="Brief description of your experience with this skill..."
                    rows="3"
                  />
                </div>
                
                <div className="modal-actions">
                  <button 
                    type="button" 
                    className="btn-cancel"
                    onClick={() => {
                      setShowAddSkillForm(false);
                      setEditingSkill(null);
                      setSkillFormData({ skill: '', years: '', description: '' });
                    }}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="btn-save"
                    disabled={loading}
                  >
                    {loading ? 'Adding...' : (editingSkill ? 'Update Skill' : 'Add to List')}
                  </button>
                </div>
              </form>
            )}
            
            {/* Close Modal Button */}
            <div className="modal-actions">
              <button 
                className="btn-cancel"
                onClick={() => {
                  setShowSkillsManagement(false);
                  setShowAddSkillForm(false);
                  setEditingSkill(null);
                  setPendingSkills([]);
                  setSkillFormData({ skill: '', years: '', description: '' });
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      {message && (
        <div className="success-message">
          {message}
        </div>
      )}
    </div>
  );
};

export default CandidatesDashboard; 