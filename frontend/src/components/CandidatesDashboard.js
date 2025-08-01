import React, { useState, useEffect } from 'react';
import './CandidatesDashboard.css';

const CandidatesDashboard = () => {
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [candidateApplications, setCandidateApplications] = useState([]);
  const [candidateInteractions, setCandidateInteractions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showViewDetails, setShowViewDetails] = useState(false);
  const [showExperienceForm, setShowExperienceForm] = useState(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    location: '',
    domain: '',
    expected_salary_min: '',
    expected_salary_max: '',
    summary: ''
  });
  const [experienceFormData, setExperienceFormData] = useState({
    skill: '',
    years: '',
    description: ''
  });

  useEffect(() => {
    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/candidates/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setCandidates(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch candidates: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to fetch candidates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCandidate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/candidates/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });
      if (response.ok) {
        const data = await response.json();
        setMessage('Candidate created successfully');
        setFormData({
          name: '',
          email: '',
          location: '',
          domain: '',
          expected_salary_min: '',
          expected_salary_max: '',
          summary: ''
        });
        setShowCreateForm(false);
        fetchCandidates(); // Refresh the list
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to create candidate: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to create candidate');
    } finally {
      setLoading(false);
    }
  };

  const handleViewCandidateDetails = async () => {
    if (!selectedCandidateId) {
      setError('Please enter a candidate ID');
      return;
    }
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/candidates/${selectedCandidateId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedCandidate(data);
        fetchCandidateApplications(selectedCandidateId);
        fetchCandidateInteractions(selectedCandidateId);
        setShowViewDetails(true);
        setError('');
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch candidate details: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to fetch candidate details');
    } finally {
      setLoading(false);
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
        setCandidateApplications(data);
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

  const fetchCandidateInteractions = async (candidateId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/interactions/candidates/${candidateId}/interactions`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setCandidateInteractions(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch candidate interactions: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to fetch candidate interactions');
    }
  };

  const handleDeleteCandidate = async (candidateId) => {
    if (!window.confirm('Are you sure you want to delete this candidate?')) {
      return;
    }
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/candidates/${candidateId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        setMessage('Candidate deleted successfully');
        setSelectedCandidate(null);
        setShowViewDetails(false);
        fetchCandidates(); // Refresh the list
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to delete candidate: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to delete candidate');
    } finally {
      setLoading(false);
    }
  };

  const handleAddExperience = async (candidateId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/candidates/${candidateId}/experience`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(experienceFormData)
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedCandidate(data);
        setMessage('Experience added successfully');
        setExperienceFormData({
          skill: '',
          years: '',
          description: ''
        });
        setShowExperienceForm(false);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to add experience: ${errorMessage}`);
      }
    } catch (err) {
      setError('Failed to add experience');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="candidates-dashboard">
      <div className="dashboard-header">
        <h1>Candidates Dashboard</h1>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setShowCreateForm(true)}
          >
            Create Candidate Profile
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
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
        {/* Candidates List */}
        <div className="candidates-section">
          <h2>Candidates List ({candidates.length})</h2>
          {loading ? (
            <div className="loading">Loading candidates...</div>
          ) : (
            <div className="candidates-grid">
              {candidates.map(candidate => (
                <div key={candidate.id} className="candidate-card">
                  <h3>{candidate.name}</h3>
                  <p><strong>Email:</strong> {candidate.email}</p>
                  <p><strong>Location:</strong> {candidate.location}</p>
                  <p><strong>Domain:</strong> {candidate.domain}</p>
                  <p><strong>Salary Range:</strong> ${candidate.expected_salary_min} - ${candidate.expected_salary_max}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* View Candidate Details Section */}
        <div className="view-details-section">
          <h2>View Candidate Details</h2>
          <div className="view-details-form">
            <div className="input-group">
              <input
                type="number"
                placeholder="Enter Candidate ID"
                value={selectedCandidateId}
                onChange={(e) => setSelectedCandidateId(e.target.value)}
              />
              <button 
                className="btn btn-secondary"
                onClick={handleViewCandidateDetails}
              >
                View Details
              </button>
            </div>
          </div>
        </div>

        {/* Candidate Details Display */}
        {showViewDetails && selectedCandidate && (
          <div className="candidate-details">
            <h2>Candidate Details</h2>
            <div className="detail-section">
              <h3>Basic Information</h3>
              <p><strong>Name:</strong> {selectedCandidate.name}</p>
              <p><strong>Email:</strong> {selectedCandidate.email}</p>
              <p><strong>Location:</strong> {selectedCandidate.location}</p>
              <p><strong>Domain:</strong> {selectedCandidate.domain}</p>
              <p><strong>Salary Range:</strong> ${selectedCandidate.expected_salary_min} - ${selectedCandidate.expected_salary_max}</p>
              <p><strong>Summary:</strong> {selectedCandidate.summary}</p>
            </div>

            <div className="detail-section">
              <h3>Experience</h3>
              {selectedCandidate.experiences && selectedCandidate.experiences.length > 0 ? (
                selectedCandidate.experiences.map(exp => (
                  <div key={exp.id} className="experience-item">
                    <p><strong>{exp.skill}</strong> - {exp.years} years</p>
                    <p>{exp.description}</p>
                  </div>
                ))
              ) : (
                <p>No experience listed</p>
              )}
            </div>

            <div className="detail-section">
              <h3>Applications ({candidateApplications.length})</h3>
              {candidateApplications.length > 0 ? (
                candidateApplications.map(app => (
                  <div key={app.id} className="application-item">
                    <p><strong>Job:</strong> {app.job?.title || 'N/A'}</p>
                    <p><strong>Status:</strong> {app.status}</p>
                    <p><strong>Applied:</strong> {new Date(app.created_at).toLocaleDateString()}</p>
                  </div>
                ))
              ) : (
                <p>No applications found</p>
              )}
            </div>

            <div className="detail-section">
              <h3>Interactions ({candidateInteractions.length})</h3>
              {candidateInteractions.length > 0 ? (
                candidateInteractions.map(interaction => (
                  <div key={interaction.id} className="interaction-item">
                    <p><strong>Job:</strong> {interaction.job?.title || 'N/A'}</p>
                    <p><strong>Type:</strong> {interaction.interaction_type}</p>
                    <p><strong>Date:</strong> {new Date(interaction.timestamp).toLocaleDateString()}</p>
                  </div>
                ))
              ) : (
                <p>No interactions found</p>
              )}
            </div>

            <div className="actions">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowExperienceForm(true)}
              >
                Add Experience
              </button>
              <button 
                className="btn btn-danger"
                onClick={() => handleDeleteCandidate(selectedCandidate.id)}
              >
                Delete Candidate
              </button>
            </div>
          </div>
        )}

        {/* Create Candidate Form */}
        {showCreateForm && (
          <div className="modal">
            <div className="modal-content">
              <h3>Create New Candidate</h3>
              <form onSubmit={handleCreateCandidate}>
                <div className="form-group">
                  <label>Name:</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Email:</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Location:</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({...formData, location: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Domain:</label>
                  <input
                    type="text"
                    value={formData.domain}
                    onChange={(e) => setFormData({...formData, domain: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Expected Salary Min:</label>
                  <input
                    type="number"
                    value={formData.expected_salary_min}
                    onChange={(e) => setFormData({...formData, expected_salary_min: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Expected Salary Max:</label>
                  <input
                    type="number"
                    value={formData.expected_salary_max}
                    onChange={(e) => setFormData({...formData, expected_salary_max: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Summary:</label>
                  <textarea
                    value={formData.summary}
                    onChange={(e) => setFormData({...formData, summary: e.target.value})}
                    required
                  />
                </div>
                <div className="form-actions">
                  <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Creating...' : 'Create Candidate'}
                  </button>
                  <button 
                    type="button" 
                    className="btn btn-secondary"
                    onClick={() => setShowCreateForm(false)}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Add Experience Form */}
        {showExperienceForm && selectedCandidate && (
          <div className="modal">
            <div className="modal-content">
              <h3>Add Experience</h3>
              <form onSubmit={(e) => {
                e.preventDefault();
                handleAddExperience(selectedCandidate.id);
              }}>
                <div className="form-group">
                  <label>Skill:</label>
                  <input
                    type="text"
                    value={experienceFormData.skill}
                    onChange={(e) => setExperienceFormData({...experienceFormData, skill: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Years:</label>
                  <input
                    type="number"
                    value={experienceFormData.years}
                    onChange={(e) => setExperienceFormData({...experienceFormData, years: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Description:</label>
                  <textarea
                    value={experienceFormData.description}
                    onChange={(e) => setExperienceFormData({...experienceFormData, description: e.target.value})}
                    required
                  />
                </div>
                <div className="form-actions">
                  <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Adding...' : 'Add Experience'}
                  </button>
                  <button 
                    type="button" 
                    className="btn btn-secondary"
                    onClick={() => setShowExperienceForm(false)}
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

export default CandidatesDashboard; 