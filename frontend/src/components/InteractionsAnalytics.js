import React, { useState, useEffect } from 'react';
import './InteractionsAnalytics.css';

const InteractionsAnalytics = () => {
  const [interactions, setInteractions] = useState([]);
  const [behaviorPatterns, setBehaviorPatterns] = useState({});
  const [similarUsers, setSimilarUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('interactions');
  const [showLogForm, setShowLogForm] = useState(false);
  
  // Interaction history params
  const [interactionParams, setInteractionParams] = useState({
    candidate_id: '',
    days_back: 30,
    interaction_types: []
  });

  // Behavior patterns params
  const [behaviorParams, setBehaviorParams] = useState({
    candidate_id: '',
    days_back: 90
  });

  // Similar users params
  const [similarUsersParams, setSimilarUsersParams] = useState({
    candidate_id: '',
    limit: 10
  });

  // Log interaction form
  const [logFormData, setLogFormData] = useState({
    user_id: '',
    job_id: '',
    interaction_type: 'viewed'
  });

  const fetchInteractionHistory = async () => {
    if (!interactionParams.candidate_id) {
      setError('Please enter a candidate ID');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const queryParams = new URLSearchParams({
        days_back: interactionParams.days_back,
        ...(interactionParams.interaction_types.length > 0 && { 
          interaction_types: interactionParams.interaction_types.join(',') 
        })
      });

      const response = await fetch(`http://localhost:8000/api/v1/interactions/candidates/${interactionParams.candidate_id}/interactions?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setInteractions(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch interaction history: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const fetchBehaviorPatterns = async () => {
    if (!behaviorParams.candidate_id) {
      setError('Please enter a candidate ID');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const queryParams = new URLSearchParams({
        days_back: behaviorParams.days_back
      });

      const response = await fetch(`http://localhost:8000/api/v1/interactions/candidates/${behaviorParams.candidate_id}/behavior-patterns?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setBehaviorPatterns(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch behavior patterns: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const fetchSimilarUsers = async () => {
    if (!similarUsersParams.candidate_id) {
      setError('Please enter a candidate ID');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const queryParams = new URLSearchParams({
        limit: similarUsersParams.limit
      });

      const response = await fetch(`http://localhost:8000/api/v1/interactions/candidates/${similarUsersParams.candidate_id}/similar-users?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSimilarUsers(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch similar users: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const logInteraction = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/interactions/log-interaction/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(logFormData)
      });
      
      if (response.ok) {
        alert('Interaction logged successfully!');
        setShowLogForm(false);
        setLogFormData({
          user_id: '',
          job_id: '',
          interaction_type: 'viewed'
        });
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to log interaction: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const getInteractionTypeColor = (type) => {
    switch (type) {
      case 'viewed':
        return '#17a2b8';
      case 'applied':
        return '#28a745';
      case 'rejected':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  };

  const getSimilarityColor = (similarity) => {
    if (similarity >= 0.8) return '#28a745';
    if (similarity >= 0.6) return '#ffc107';
    if (similarity >= 0.4) return '#fd7e14';
    return '#dc3545';
  };

  return (
    <div className="interactions-analytics">
      <div className="dashboard-header">
        <h1>Interactions Analytics</h1>
        <button 
          className="btn-primary"
          onClick={() => setShowLogForm(true)}
        >
          Log Interaction
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'interactions' ? 'active' : ''}`}
          onClick={() => setActiveTab('interactions')}
        >
          Interaction History
        </button>
        <button 
          className={`tab ${activeTab === 'behavior' ? 'active' : ''}`}
          onClick={() => setActiveTab('behavior')}
        >
          Behavior Patterns
        </button>
        <button 
          className={`tab ${activeTab === 'similar' ? 'active' : ''}`}
          onClick={() => setActiveTab('similar')}
        >
          Similar Users
        </button>
      </div>

      <div className="content-area">
        {activeTab === 'interactions' && (
          <div className="analytics-section">
            <h2>Interaction History</h2>
            <div className="params-section">
              <div className="param-group">
                <label>Candidate ID:</label>
                <input
                  type="number"
                  value={interactionParams.candidate_id}
                  onChange={(e) => setInteractionParams({...interactionParams, candidate_id: e.target.value})}
                  placeholder="Enter candidate ID"
                />
              </div>
              <div className="param-group">
                <label>Days Back:</label>
                <select
                  value={interactionParams.days_back}
                  onChange={(e) => setInteractionParams({...interactionParams, days_back: parseInt(e.target.value)})}
                >
                  <option value={7}>7 days</option>
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                  <option value={365}>365 days</option>
                </select>
              </div>
              <div className="param-group">
                <label>Interaction Types:</label>
                <div className="checkbox-group">
                  {['viewed', 'applied', 'rejected'].map(type => (
                    <label key={type}>
                      <input
                        type="checkbox"
                        checked={interactionParams.interaction_types.includes(type)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setInteractionParams({
                              ...interactionParams,
                              interaction_types: [...interactionParams.interaction_types, type]
                            });
                          } else {
                            setInteractionParams({
                              ...interactionParams,
                              interaction_types: interactionParams.interaction_types.filter(t => t !== type)
                            });
                          }
                        }}
                      />
                      {type}
                    </label>
                  ))}
                </div>
              </div>
              <button 
                className="btn-primary"
                onClick={fetchInteractionHistory}
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Get Interaction History'}
              </button>
            </div>

            <div className="results-section">
              <h3>Results ({interactions.length})</h3>
              {interactions.length > 0 ? (
                <div className="interactions-grid">
                  {interactions.map((interaction, index) => (
                    <div key={interaction.id || index} className="interaction-card">
                      <div className="interaction-header">
                        <span 
                          className="interaction-type"
                          style={{ backgroundColor: getInteractionTypeColor(interaction.interaction_type) }}
                        >
                          {interaction.interaction_type}
                        </span>
                        <span className="timestamp">
                          {new Date(interaction.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                      <p><strong>Job ID:</strong> {interaction.job_id}</p>
                      <p><strong>User ID:</strong> {interaction.user_id}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-results">No interactions found</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'behavior' && (
          <div className="analytics-section">
            <h2>Behavior Patterns</h2>
            <div className="params-section">
              <div className="param-group">
                <label>Candidate ID:</label>
                <input
                  type="number"
                  value={behaviorParams.candidate_id}
                  onChange={(e) => setBehaviorParams({...behaviorParams, candidate_id: e.target.value})}
                  placeholder="Enter candidate ID"
                />
              </div>
              <div className="param-group">
                <label>Days to Analyze:</label>
                <select
                  value={behaviorParams.days_back}
                  onChange={(e) => setBehaviorParams({...behaviorParams, days_back: parseInt(e.target.value)})}
                >
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                  <option value={180}>180 days</option>
                  <option value={365}>365 days</option>
                </select>
              </div>
              <button 
                className="btn-primary"
                onClick={fetchBehaviorPatterns}
                disabled={loading}
              >
                {loading ? 'Analyzing...' : 'Analyze Behavior Patterns'}
              </button>
            </div>

            <div className="results-section">
              <h3>Behavior Analysis</h3>
              {Object.keys(behaviorPatterns).length > 0 ? (
                <div className="behavior-patterns">
                  <div className="pattern-card">
                    <h4>Interaction Summary</h4>
                    <p><strong>Total Interactions:</strong> {behaviorPatterns.total_interactions || 0}</p>
                    <p><strong>Total Applications:</strong> {behaviorPatterns.total_applications || 0}</p>
                    <p><strong>Application Rate:</strong> {((behaviorPatterns.application_rate || 0) * 100).toFixed(1)}%</p>
                    <p><strong>Engagement Score:</strong> {behaviorPatterns.engagement_score || 0}</p>
                  </div>
                  
                  <div className="pattern-card">
                    <h4>Preferred Domains</h4>
                    {behaviorPatterns.preferred_domains && Object.keys(behaviorPatterns.preferred_domains).length > 0 ? (
                      Object.entries(behaviorPatterns.preferred_domains).map(([domain, count]) => (
                        <div key={domain} className="pattern-item">
                          <span className="category">{domain}</span>
                          <span className="count">({count} interactions)</span>
                        </div>
                      ))
                    ) : (
                      <p>No domain preferences found</p>
                    )}
                  </div>
                  
                  <div className="pattern-card">
                    <h4>Preferred Locations</h4>
                    {behaviorPatterns.preferred_locations && Object.keys(behaviorPatterns.preferred_locations).length > 0 ? (
                      Object.entries(behaviorPatterns.preferred_locations).map(([location, count]) => (
                        <div key={location} className="pattern-item">
                          <span className="category">{location}</span>
                          <span className="count">({count} interactions)</span>
                        </div>
                      ))
                    ) : (
                      <p>No location preferences found</p>
                    )}
                  </div>
                  
                  <div className="pattern-card">
                    <h4>Salary Preferences</h4>
                    <p><strong>Average Salary:</strong> ${behaviorPatterns.salary_preferences?.avg?.toLocaleString() || 'N/A'}</p>
                    {behaviorPatterns.most_recent_application && (
                      <p><strong>Last Application:</strong> {new Date(behaviorPatterns.most_recent_application).toLocaleDateString()}</p>
                    )}
                    {behaviorPatterns.avg_view_to_apply_hours !== undefined && (
                      <p><strong>Avg Hours to Apply:</strong> {behaviorPatterns.avg_view_to_apply_hours} hours</p>
                    )}
                  </div>
                  
                  <div className="pattern-card">
                    <h4>Interaction Types</h4>
                    {behaviorPatterns.interaction_types && Object.keys(behaviorPatterns.interaction_types).length > 0 ? (
                      Object.entries(behaviorPatterns.interaction_types).map(([type, count]) => (
                        <div key={type} className="pattern-item">
                          <span className="category">{type}</span>
                          <span className="count">({count} times)</span>
                        </div>
                      ))
                    ) : (
                      <p>No interaction type data</p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="no-results">No behavior patterns found</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'similar' && (
          <div className="analytics-section">
            <h2>Similar Users</h2>
            <div className="params-section">
              <div className="param-group">
                <label>Candidate ID:</label>
                <input
                  type="number"
                  value={similarUsersParams.candidate_id}
                  onChange={(e) => setSimilarUsersParams({...similarUsersParams, candidate_id: e.target.value})}
                  placeholder="Enter candidate ID"
                />
              </div>
              <div className="param-group">
                <label>Number of Similar Users:</label>
                <select
                  value={similarUsersParams.limit}
                  onChange={(e) => setSimilarUsersParams({...similarUsersParams, limit: parseInt(e.target.value)})}
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>
              <button 
                className="btn-primary"
                onClick={fetchSimilarUsers}
                disabled={loading}
              >
                {loading ? 'Finding...' : 'Find Similar Users'}
              </button>
            </div>

            <div className="results-section">
              <h3>Similar Users ({similarUsers.length})</h3>
              {similarUsers.length > 0 ? (
                <div className="similar-users-grid">
                  {similarUsers.map((user, index) => (
                    <div key={user.id || index} className="similar-user-card">
                      <div className="user-header">
                        <h4>{user.name}</h4>
                        <span 
                          className="similarity-score"
                          style={{ backgroundColor: getSimilarityColor(user.similarity) }}
                        >
                          {user.similarity?.toFixed(3) || 'N/A'}
                        </span>
                      </div>
                      <p><strong>Email:</strong> {user.email}</p>
                      <p><strong>Location:</strong> {user.location}</p>
                      <p><strong>Domain:</strong> {user.domain}</p>
                      <p><strong>Expected Salary:</strong> ${user.expected_salary_min} - ${user.expected_salary_max}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-results">No similar users found</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Log Interaction Form */}
      {showLogForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Log New Interaction</h2>
            <form onSubmit={logInteraction}>
              <div className="form-group">
                <label>User ID:</label>
                <input
                  type="number"
                  value={logFormData.user_id}
                  onChange={(e) => setLogFormData({...logFormData, user_id: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Job ID:</label>
                <input
                  type="number"
                  value={logFormData.job_id}
                  onChange={(e) => setLogFormData({...logFormData, job_id: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Interaction Type:</label>
                <select
                  value={logFormData.interaction_type}
                  onChange={(e) => setLogFormData({...logFormData, interaction_type: e.target.value})}
                  required
                >
                  <option value="viewed">Viewed</option>
                  <option value="applied">Applied</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Logging...' : 'Log Interaction'}
                </button>
                <button 
                  type="button" 
                  className="btn-secondary"
                  onClick={() => {
                    setShowLogForm(false);
                    setLogFormData({
                      user_id: '',
                      job_id: '',
                      interaction_type: 'viewed'
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

export default InteractionsAnalytics; 