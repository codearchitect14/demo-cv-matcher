import React, { useState, useEffect } from 'react';
import './InteractionsAnalytics.css';

const InteractionsAnalytics = () => {
  const [interactions, setInteractions] = useState([]);
  const [behaviorPatterns, setBehaviorPatterns] = useState({});
  const [similarUsers, setSimilarUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('interactions');
  const [searchName, setSearchName] = useState('');
  const [searchJobTitle, setSearchJobTitle] = useState('');
  const [sortBy, setSortBy] = useState({ key: 'timestamp', dir: 'desc' });
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [showLogForm, setShowLogForm] = useState(false);
  
  // New smart search states
  const [candidateSearch, setCandidateSearch] = useState('');
  const [candidateSuggestions, setCandidateSuggestions] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentInteractions, setRecentInteractions] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  
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
    interaction_type: 'VIEWED'
  });

    // Search candidates function with debouncing and performance optimizations
  const searchCandidates = async (searchTerm) => {
    if (!searchTerm || searchTerm.length < 2) {
      setCandidateSuggestions([]);
      setShowSuggestions(false);
      setSearchLoading(false);
      return;
    }

    setSearchLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      // Add timeout to prevent hanging requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      // Try to search candidates with error handling and timeout
      const response = await fetch(
        `http://localhost:8000/api/v1/candidates/?search=${encodeURIComponent(searchTerm)}&limit=10`, 
        { 
          headers,
          signal: controller.signal
        }
      );
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        setCandidateSuggestions(data || []);
        setShowSuggestions(true);
      } else {
        // If API fails, show empty suggestions
        console.warn('Candidate search API failed');
        setCandidateSuggestions([]);
        setShowSuggestions(false);
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.warn('Search request timed out');
      } else {
        console.error('Search error:', err);
      }
      // Fallback to empty suggestions on network error
      setCandidateSuggestions([]);
      setShowSuggestions(false);
    } finally {
      setSearchLoading(false);
    }
  };

  // Debounced search function with better performance
  const debouncedSearch = React.useCallback(
    React.useMemo(() => {
      let timeoutId;
      return (searchTerm) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          searchCandidates(searchTerm);
        }, 500); // Increased to 500ms for better performance
      };
    }, []),
    []
  );

  const fetchInteractionHistory = async (candidateId = null) => {
    const targetCandidateId = candidateId || selectedCandidate?.id;
    
    if (!targetCandidateId) {
      setError('Please select a candidate');
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

      // Use public (no-auth) endpoint if no token is present
      const basePath = token
        ? `http://localhost:8000/api/v1/interactions/candidates/${targetCandidateId}/interactions`
        : `http://localhost:8000/api/v1/interactions/public/candidates/${targetCandidateId}/interactions`;

      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      const response = await fetch(`${basePath}?${queryParams}`, { headers });
      
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

  // Fetch recent interactions for default view
  const fetchRecentInteractions = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      // Fetch recent interactions across all candidates
      const response = await fetch(`http://localhost:8000/api/v1/interactions/recent/?limit=20`, { headers });
      
      if (response.ok) {
        const data = await response.json();
        setRecentInteractions(data);
             } else {
         // Show empty interactions if API fails
         console.warn('Recent interactions API failed');
         setRecentInteractions([]);
       }
         } catch (err) {
       console.error('Network error:', err);
       // Fallback to empty interactions
       setRecentInteractions([]);
     } finally {
      setLoading(false);
    }
  };

  const filteredSorted = () => {
    try {
      let rows = Array.isArray(interactions) ? [...interactions] : [];
      
      // Apply independent filtering
      if (searchName.trim()) {
        const nameQuery = searchName.toLowerCase();
        rows = rows.filter(r => 
          (r.candidate_name || '').toLowerCase().includes(nameQuery)
        );
      }
      
      if (searchJobTitle.trim()) {
        const titleQuery = searchJobTitle.toLowerCase();
        rows = rows.filter(r => 
          (r.job_title || '').toLowerCase().includes(titleQuery)
        );
      }
      
      // Sort
      rows.sort((a, b) => {
        const { key, dir } = sortBy;
        const va = a[key];
        const vb = b[key];
        if (key === 'timestamp') {
          const da = new Date(va).getTime();
          const db = new Date(vb).getTime();
          return dir === 'asc' ? da - db : db - da;
        }
        if (va === vb) return 0;
        return dir === 'asc' ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
      });
      return rows;
    } catch (error) {
      console.error("Filter failed:", error);
      // Return full data as fallback
      return Array.isArray(interactions) ? [...interactions] : [];
    }
  };

  const paginated = () => {
    const rows = filteredSorted();
    const start = (page - 1) * perPage;
    return rows.slice(start, start + perPage);
  };

  const totalResults = () => filteredSorted().length;

  const toggleSort = (key) => {
    setSortBy(prev => {
      if (prev.key === key) {
        return { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' };
      }
      return { key, dir: 'asc' };
    });
  };

  const fetchBehaviorPatterns = async () => {
    if (!selectedCandidate) {
      setError('Please select a candidate');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const queryParams = new URLSearchParams({
        days_back: behaviorParams.days_back
      });

      const basePath = token
        ? `http://localhost:8000/api/v1/interactions/candidates/${selectedCandidate.id}/behavior-patterns`
        : `http://localhost:8000/api/v1/interactions/public/candidates/${selectedCandidate.id}/behavior-patterns`;
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const response = await fetch(`${basePath}?${queryParams}`, { headers });
      
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
    if (!selectedCandidate) {
      setError('Please select a candidate');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const queryParams = new URLSearchParams({
        limit: similarUsersParams.limit
      });

      const basePath = token
        ? `http://localhost:8000/api/v1/interactions/candidates/${selectedCandidate.id}/similar-users`
        : `http://localhost:8000/api/v1/interactions/public/candidates/${selectedCandidate.id}/similar-users`;
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const response = await fetch(`${basePath}?${queryParams}`, { headers });
      
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
          interaction_type: 'VIEWED'
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
      case 'VIEWED':
        return '#17a2b8';
      case 'APPLIED':
        return '#28a745';
      case 'REJECTED':
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

  // Handler functions for smart search
  const handleCandidateSearchChange = (e) => {
    const value = e.target.value;
    setCandidateSearch(value);
    debouncedSearch(value);
  };

  const handleCandidateSelect = (candidate) => {
    setSelectedCandidate(candidate);
    setCandidateSearch(`${candidate.name} — ${candidate.email}`);
    setShowSuggestions(false);
    // Automatically fetch interactions for selected candidate
    fetchInteractionHistory(candidate.id);
    // Also fetch behavior patterns if we're on the behavior tab
    if (activeTab === 'behavior') {
      fetchBehaviorPatterns();
    }
    // Also fetch similar users if we're on the similar tab
    if (activeTab === 'similar') {
      fetchSimilarUsers();
    }
  };

  const clearCandidateSelection = () => {
    setSelectedCandidate(null);
    setCandidateSearch('');
    setInteractions([]);
    setBehaviorPatterns({});
    setSimilarUsers([]);
    setShowSuggestions(false);
  };

  // Load recent interactions on component mount
  useEffect(() => {
    fetchRecentInteractions();
  }, []);

  // Debug log for table column alignment
  useEffect(() => {
    const debugTableAlignment = () => {
      try {
        const table = document.querySelector('.interactions-table table');
        if (table) {
          const headerCount = table.querySelectorAll('thead tr th').length;
          table.querySelectorAll('tbody tr').forEach((row, idx) => {
            const cellCount = row.querySelectorAll('td').length;
            if (cellCount !== headerCount) {
              console.warn(`[TableMismatch] row ${idx+1} has ${cellCount} cells but headers=${headerCount}`, row);
            }
          });
        }
      } catch (e) {
        console.error('[TableDebugError]', e);
      }
    };

    // Run debug check after table renders
    const timer = setTimeout(debugTableAlignment, 100);
    return () => clearTimeout(timer);
  }, [interactions, recentInteractions, selectedCandidate, page]);

  // Auto-fetch behavior patterns when switching to behavior tab if candidate is selected
  useEffect(() => {
    if (activeTab === 'behavior' && selectedCandidate && Object.keys(behaviorPatterns).length === 0) {
      fetchBehaviorPatterns();
    }
  }, [activeTab, selectedCandidate]);

  // Auto-fetch similar users when switching to similar tab if candidate is selected
  useEffect(() => {
    if (activeTab === 'similar' && selectedCandidate && similarUsers.length === 0) {
      fetchSimilarUsers();
    }
  }, [activeTab, selectedCandidate]);

  return (
    <div className="interactions-analytics">
      <div className="unified-header">
        <div className="header-content">
          <h1 className="header-title"><span className="title-icon">📊</span> Interactions Analytics</h1>
        </div>
        <div className="header-actions">
          <button className="btn-back" onClick={() => window.location.href = '/recruiter/dashboard'}>Back</button>
          <button 
            className="btn-primary"
            onClick={() => {
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              window.location.href = '/';
            }}
          >
            Logout
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
          <button onClick={() => setError('')}>×</button>
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
            
            {/* Dashboard Layout with Sidebar */}
            <div className="dashboard-layout">
              {/* Filters Sidebar */}
              <div className="filters-sidebar">
                <div className="sidebar-header">
                  <h3 className="sidebar-title">Search & Filter Candidates</h3>
                </div>

                {/* Smart Search Section */}
                <div className="filter-section">
                  <div className="filter-section-title">Search Candidate</div>
                  <div className="search-input-wrapper">
                    <input
                      type="text"
                      value={candidateSearch}
                      onChange={handleCandidateSearchChange}
                      placeholder="Search candidate by name or email..."
                      className="filter-input"
                    />
                    {selectedCandidate && (
                      <button 
                        className="clear-search-btn"
                        onClick={clearCandidateSelection}
                        title="Clear selection"
                      >
                        ✕
                      </button>
                    )}
                    
                    {/* Suggestions Dropdown */}
                    {showSuggestions && candidateSuggestions.length > 0 && (
                      <div className="suggestions-dropdown">
                        {candidateSuggestions.map((candidate) => (
                          <div
                            key={candidate.id}
                            className="suggestion-item"
                            onClick={() => handleCandidateSelect(candidate)}
                          >
                            <div className="suggestion-main">
                              <strong>{candidate.name}</strong>
                              <span className="suggestion-email">— {candidate.email}</span>
                            </div>
                            <div className="suggestion-sub">
                              {candidate.location && <span>Location: {candidate.location}</span>}
                              {candidate.domain && <span>Domain: {candidate.domain}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Selected Candidate Profile */}
                {selectedCandidate && (
                  <div className="filter-section">
                    <div className="filter-section-title">Selected Candidate</div>
                    <div className="job-info-compact">
                      <div className="job-detail-item">
                        <strong>Name:</strong> {selectedCandidate.name}
                      </div>
                      <div className="job-detail-item">
                        <strong>Email:</strong> {selectedCandidate.email}
                      </div>
                      {selectedCandidate.location && (
                        <div className="job-detail-item">
                          <strong>Location:</strong> {selectedCandidate.location}
                        </div>
                      )}
                      {selectedCandidate.domain && (
                        <div className="job-detail-item">
                          <strong>Domain:</strong> {selectedCandidate.domain}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Filter Controls */}
                <div className="filter-section">
                  <div className="filter-section-title">Time Period</div>
                  <select
                    className="filter-input"
                    value={interactionParams.days_back}
                    onChange={(e) => {
                      setInteractionParams({...interactionParams, days_back: parseInt(e.target.value)});
                      if (selectedCandidate) {
                        fetchInteractionHistory();
                      }
                    }}
                  >
                    <option value={7}>Last 7 days</option>
                    <option value={30}>Last 30 days</option>
                    <option value={90}>Last 90 days</option>
                  </select>
                </div>
                
                <div className="filter-section">
                  <div className="filter-section-title">Interaction Types</div>
                  <div className="filter-group">
                    {['VIEWED', 'APPLIED', 'REJECTED'].map(type => (
                      <label key={type} className="checkbox-label">
                        <input
                          type="checkbox"
                          checked={interactionParams.interaction_types.includes(type)}
                          onChange={(e) => {
                            const newTypes = e.target.checked
                              ? [...interactionParams.interaction_types, type]
                              : interactionParams.interaction_types.filter(t => t !== type);
                            setInteractionParams({
                              ...interactionParams,
                              interaction_types: newTypes
                            });
                            if (selectedCandidate) {
                              fetchInteractionHistory();
                            }
                          }}
                        />
                        <span className="checkbox-text">{type.charAt(0).toUpperCase() + type.slice(1)}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Table Search Filters */}
                <div className="filter-section">
                  <div className="filter-section-title">Filter Table Results</div>
                  <div className="search-grid">
                    <div className="search-field">
                      <label className="search-label">Search Candidate Name</label>
                      <input
                        type="text"
                        value={searchName}
                        onChange={(e) => setSearchName(e.target.value)}
                        placeholder="Search by candidate name..."
                        className="filter-input"
                      />
                    </div>
                    <div className="search-field">
                      <label className="search-label">Search Job Title</label>
                      <input
                        type="text"
                        value={searchJobTitle}
                        onChange={(e) => setSearchJobTitle(e.target.value)}
                        placeholder="Search by job title..."
                        className="filter-input"
                      />
                    </div>
                  </div>
                </div>

                {selectedCandidate && (
                  <div className="filter-actions">
                    <button 
                      className="btn-clear" 
                      onClick={clearCandidateSelection}
                    >
                      Clear Selection
                    </button>
                  </div>
                )}
              </div>

              {/* Results Content */}
              <div className="candidates-content">
                <div className="results-header">
                  <h3 className="results-title">
                    {selectedCandidate 
                      ? `Interactions for ${selectedCandidate.name}` 
                      : 'Recent Interactions'
                    }
                  </h3>
                </div>

              {/* Summary Cards */}
              {selectedCandidate && (
                <div className="summary-cards">
                  <div className="summary-card">
                    <span className="count">{interactions.length}</span>
                    <span className="label">Total</span>
                  </div>
                  <div className="summary-card">
                    <span className="count">{interactions.filter(i=>i.interaction_type==='APPLIED').length}</span>
                    <span className="label">Applications</span>
                  </div>
                  <div className="summary-card">
                    <span className="count">{interactions.filter(i=>i.interaction_type==='VIEWED').length}</span>
                    <span className="label">Views</span>
                  </div>
                  <div className="summary-card">
                    <span className="count">{interactions.filter(i=>i.interaction_type==='REJECTED').length}</span>
                    <span className="label">Rejections</span>
                  </div>
                </div>
              )}

              {/* Interactions Table */}
              {(selectedCandidate ? interactions.length > 0 : recentInteractions.length > 0) ? (
                <div className="table-scroll">
                  <div className="table-container">
                    <table className="interactions-table" role="table" aria-label="Interaction history">
                      <thead>
                        <tr>
                          <th scope="col" onClick={() => toggleSort('timestamp')} className="col-date">
                            Date <span className="sort-indicator">{sortBy.key==='timestamp' ? (sortBy.dir==='asc'?'▲':'▼') : ''}</span>
                          </th>
                          <th scope="col" onClick={() => toggleSort('interaction_type')} className="col-type">
                            Type <span className="sort-indicator">{sortBy.key==='interaction_type' ? (sortBy.dir==='asc'?'▲':'▼') : ''}</span>
                          </th>
                          {!selectedCandidate && (
                            <th scope="col" onClick={() => toggleSort('candidate_name')} className="col-candidate">
                              Candidate <span className="sort-indicator">{sortBy.key==='candidate_name' ? (sortBy.dir==='asc'?'▲':'▼') : ''}</span>
                            </th>
                          )}
                          <th scope="col" onClick={() => toggleSort('job_title')} className="col-job">
                            Job Title <span className="sort-indicator">{sortBy.key==='job_title' ? (sortBy.dir==='asc'?'▲':'▼') : ''}</span>
                          </th>
                          <th scope="col" className="col-company">
                            Company
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {(selectedCandidate ? filteredSorted() : recentInteractions).slice((page-1)*perPage, page*perPage).map((row, idx) => (
                          <tr key={row.id || idx}>
                            <td className="col-date">
                              {new Date(row.timestamp).toLocaleDateString()}
                            </td>
                            <td className="col-type">
                              <span className={`status-badge ${row.interaction_type==='APPLIED'?'status-APPLIED': row.interaction_type==='REJECTED'?'status-REJECTED':'status-VIEWED'}`}>
                                {row.interaction_type}
                              </span>
                            </td>
                            {!selectedCandidate && (
                              <td className="col-candidate">
                                <div>
                                  <div className="candidate-name">{row.candidate_name || 'Unknown'}</div>
                                  <div className="candidate-email">{row.candidate_email || ''}</div>
                                </div>
                              </td>
                            )}
                            <td className="col-job">
                              {row.job_title || `Job #${row.job_id}`}
                            </td>
                            <td className="col-company">
                              {row.company || 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="no-results">
                  {selectedCandidate 
                    ? "No interactions found for this candidate in the selected time period."
                    : "No recent interactions found."
                  }
                </div>
              )}

              {/* Pagination */}
              <div className="table-footer">
                <div className="results-count">
                  Showing {((page-1)*perPage + 1)} to {Math.min(page*perPage, selectedCandidate ? interactions.length : recentInteractions.length)} 
                  of {selectedCandidate ? interactions.length : recentInteractions.length} results
                </div>
                <div className="pagination">
                  <button 
                    className="page-btn" 
                    onClick={() => setPage(p => Math.max(1, p-1))}
                    disabled={page === 1}
                  >
                    Previous
                  </button>
                  <span className="page-info">Page {page}</span>
                  <button 
                    className="page-btn" 
                    onClick={() => setPage(p => p+1)}
                    disabled={page * perPage >= (selectedCandidate ? interactions.length : recentInteractions.length)}
                  >
                    Next
                  </button>
                </div>
                <select 
                  className="per-page" 
                  value={perPage} 
                  onChange={(e) => {setPerPage(parseInt(e.target.value)); setPage(1);}}
                >
                  {[10,25,50].map(n => <option key={n} value={n}>{n}/page</option>)}
                </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'behavior' && (
          <div className="analytics-section">
            <h2>Behavior Patterns</h2>
            
            {/* Dashboard Layout with Sidebar */}
            <div className="dashboard-layout">
              {/* Filters Sidebar */}
              <div className="filters-sidebar">
                <div className="sidebar-header">
                  <h3 className="sidebar-title">Search & Filter Candidates</h3>
                </div>

                {/* Smart Search Section */}
                <div className="filter-section">
                  <div className="filter-section-title">Search Candidate</div>
                  <div className="search-input-wrapper">
                    <input
                      type="text"
                      value={candidateSearch}
                      onChange={handleCandidateSearchChange}
                      placeholder="Search candidate by name or email..."
                      className="filter-input"
                    />
                    {selectedCandidate && (
                      <button 
                        className="clear-search-btn"
                        onClick={clearCandidateSelection}
                        title="Clear selection"
                      >
                        ✕
                      </button>
                    )}
                    
                    {/* Suggestions Dropdown */}
                    {showSuggestions && candidateSuggestions.length > 0 && (
                      <div className="suggestions-dropdown">
                        {candidateSuggestions.map((candidate) => (
                          <div
                            key={candidate.id}
                            className="suggestion-item"
                            onClick={() => handleCandidateSelect(candidate)}
                          >
                            <div className="suggestion-main">
                              <strong>{candidate.name}</strong>
                              <span className="suggestion-email">— {candidate.email}</span>
                            </div>
                            <div className="suggestion-sub">
                              {candidate.location && <span>Location: {candidate.location}</span>}
                              {candidate.domain && <span>Domain: {candidate.domain}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Selected Candidate Profile */}
                {selectedCandidate && (
                  <div className="filter-section">
                    <div className="filter-section-title">Selected Candidate</div>
                    <div className="job-info-compact">
                      <div className="job-detail-item">
                        <strong>Name:</strong> {selectedCandidate.name}
                      </div>
                      <div className="job-detail-item">
                        <strong>Email:</strong> {selectedCandidate.email}
                      </div>
                      {selectedCandidate.location && (
                        <div className="job-detail-item">
                          <strong>Location:</strong> {selectedCandidate.location}
                        </div>
                      )}
                      {selectedCandidate.domain && (
                        <div className="job-detail-item">
                          <strong>Domain:</strong> {selectedCandidate.domain}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Filter Controls */}
                <div className="filter-section">
                  <div className="filter-section-title">Time Period</div>
                  <select
                    className="filter-input"
                    value={behaviorParams.days_back}
                    onChange={(e) => {
                      setBehaviorParams({...behaviorParams, days_back: parseInt(e.target.value)});
                      if (selectedCandidate) {
                        fetchBehaviorPatterns();
                      }
                    }}
                  >
                    <option value={30}>30 days</option>
                    <option value={90}>90 days</option>
                    <option value={180}>180 days</option>
                    <option value={365}>365 days</option>
                  </select>
                </div>

                {/* Action Buttons */}
                <div className="filter-section">
                  <button 
                    className="btn-primary"
                    onClick={fetchBehaviorPatterns}
                    disabled={!selectedCandidate || loading}
                  >
                    {loading ? 'Loading...' : 'Analyze Behavior'}
                  </button>
                </div>
              </div>

              {/* Results Section */}
              <div className="results-section">
                <div className="results-header">
                  <h3 className="results-title">
                    Behavior Analysis Results
                    {selectedCandidate && ` for ${selectedCandidate.name}`}
                  </h3>
                </div>

                {error && (
                  <div className="error-message">
                    {error}
                  </div>
                )}

                {Object.keys(behaviorPatterns).length > 0 ? (
                  <div className="behavior-results">
                    {/* Summary Cards */}
                    <div className="summary-cards">
                      <div className="summary-card">
                        <div className="card-title">Total Interactions</div>
                        <div className="card-value">{behaviorPatterns.total_interactions || 0}</div>
                      </div>
                      <div className="summary-card">
                        <div className="card-title">Applications</div>
                        <div className="card-value">{behaviorPatterns.total_applications || 0}</div>
                      </div>
                      <div className="summary-card">
                        <div className="card-title">Application Rate</div>
                        <div className="card-value">
                          {behaviorPatterns.application_rate 
                            ? `${(behaviorPatterns.application_rate * 100).toFixed(1)}%`
                            : '0%'
                          }
                        </div>
                      </div>
                      <div className="summary-card">
                        <div className="card-title">Engagement Score</div>
                        <div className="card-value">{behaviorPatterns.engagement_score || 0}</div>
                      </div>
                    </div>

                    {/* Detailed Analysis */}
                    <div className="behavior-details">
                      {/* Preferred Domains */}
                      {behaviorPatterns.preferred_domains && Object.keys(behaviorPatterns.preferred_domains).length > 0 && (
                        <div className="behavior-section">
                          <h4>Preferred Domains</h4>
                          <div className="behavior-list">
                            {Object.entries(behaviorPatterns.preferred_domains)
                              .sort(([,a], [,b]) => b - a)
                              .map(([domain, count]) => (
                                <div key={domain} className="behavior-item">
                                  <span className="behavior-label">{domain}</span>
                                  <span className="behavior-count">{count} interactions</span>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}

                      {/* Preferred Locations */}
                      {behaviorPatterns.preferred_locations && Object.keys(behaviorPatterns.preferred_locations).length > 0 && (
                        <div className="behavior-section">
                          <h4>Preferred Locations</h4>
                          <div className="behavior-list">
                            {Object.entries(behaviorPatterns.preferred_locations)
                              .sort(([,a], [,b]) => b - a)
                              .map(([location, count]) => (
                                <div key={location} className="behavior-item">
                                  <span className="behavior-label">{location}</span>
                                  <span className="behavior-count">{count} interactions</span>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}

                      {/* Interaction Types */}
                      {behaviorPatterns.interaction_types && Object.keys(behaviorPatterns.interaction_types).length > 0 && (
                        <div className="behavior-section">
                          <h4>Interaction Types</h4>
                          <div className="behavior-list">
                            {Object.entries(behaviorPatterns.interaction_types)
                              .sort(([,a], [,b]) => b - a)
                              .map(([type, count]) => (
                                <div key={type} className="behavior-item">
                                  <span className="behavior-label">{type}</span>
                                  <span className="behavior-count">{count} times</span>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}

                      {/* Salary Preferences */}
                      {behaviorPatterns.salary_preferences && behaviorPatterns.salary_preferences.avg > 0 && (
                        <div className="behavior-section">
                          <h4>Salary Preferences</h4>
                          <div className="behavior-item">
                            <span className="behavior-label">Average Salary</span>
                            <span className="behavior-count">
                              ${behaviorPatterns.salary_preferences.avg.toLocaleString()}
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Recent Activity */}
                      {behaviorPatterns.most_recent_application && (
                        <div className="behavior-section">
                          <h4>Recent Activity</h4>
                          <div className="behavior-item">
                            <span className="behavior-label">Last Application</span>
                            <span className="behavior-count">
                              {new Date(behaviorPatterns.most_recent_application).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      )}

                      {/* View to Apply Time */}
                      {behaviorPatterns.avg_view_to_apply_hours > 0 && (
                        <div className="behavior-section">
                          <h4>Engagement Speed</h4>
                          <div className="behavior-item">
                            <span className="behavior-label">Avg. Time to Apply</span>
                            <span className="behavior-count">
                              {behaviorPatterns.avg_view_to_apply_hours.toFixed(1)} hours
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="no-results">
                    {selectedCandidate 
                      ? "No behavior patterns found for this candidate in the selected time period."
                      : "Please select a candidate to analyze their behavior patterns."
                    }
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'similar' && (
          <div className="analytics-section">
            <h2>Similar Users</h2>
            
            {/* Dashboard Layout with Sidebar */}
            <div className="dashboard-layout">
              {/* Filters Sidebar */}
              <div className="filters-sidebar">
                <div className="sidebar-header">
                  <h3 className="sidebar-title">Search & Filter Candidates</h3>
                </div>

                {/* Smart Search Section */}
                <div className="filter-section">
                  <div className="filter-section-title">Search Candidate</div>
                  <div className="search-input-wrapper">
                    <input
                      type="text"
                      value={candidateSearch}
                      onChange={handleCandidateSearchChange}
                      placeholder="Search candidate by name or email..."
                      className="filter-input"
                    />
                    {selectedCandidate && (
                      <button 
                        className="clear-search-btn"
                        onClick={clearCandidateSelection}
                        title="Clear selection"
                      >
                        ✕
                      </button>
                    )}
                    
                    {/* Suggestions Dropdown */}
                    {showSuggestions && candidateSuggestions.length > 0 && (
                      <div className="suggestions-dropdown">
                        {candidateSuggestions.map((candidate) => (
                          <div
                            key={candidate.id}
                            className="suggestion-item"
                            onClick={() => handleCandidateSelect(candidate)}
                          >
                            <div className="suggestion-main">
                              <strong>{candidate.name}</strong>
                              <span className="suggestion-email">— {candidate.email}</span>
                            </div>
                            <div className="suggestion-sub">
                              {candidate.location && <span>Location: {candidate.location}</span>}
                              {candidate.domain && <span>Domain: {candidate.domain}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Selected Candidate Profile */}
                {selectedCandidate && (
                  <div className="filter-section">
                    <div className="filter-section-title">Selected Candidate</div>
                    <div className="job-info-compact">
                      <div className="job-detail-item">
                        <strong>Name:</strong> {selectedCandidate.name}
                      </div>
                      <div className="job-detail-item">
                        <strong>Email:</strong> {selectedCandidate.email}
                      </div>
                      {selectedCandidate.location && (
                        <div className="job-detail-item">
                          <strong>Location:</strong> {selectedCandidate.location}
                        </div>
                      )}
                      {selectedCandidate.domain && (
                        <div className="job-detail-item">
                          <strong>Domain:</strong> {selectedCandidate.domain}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Filter Controls */}
                <div className="filter-section">
                  <div className="filter-section-title">Number of Similar Users</div>
                  <select
                    className="filter-input"
                    value={similarUsersParams.limit}
                    onChange={(e) => {
                      setSimilarUsersParams({...similarUsersParams, limit: parseInt(e.target.value)});
                      if (selectedCandidate) {
                        fetchSimilarUsers();
                      }
                    }}
                  >
                    <option value={5}>5 users</option>
                    <option value={10}>10 users</option>
                    <option value={20}>20 users</option>
                    <option value={50}>50 users</option>
                  </select>
                </div>

                {/* Action Buttons */}
                <div className="filter-section">
                  <button 
                    className="btn-primary"
                    onClick={fetchSimilarUsers}
                    disabled={!selectedCandidate || loading}
                  >
                    {loading ? 'Loading...' : 'Find Similar Users'}
                  </button>
                </div>
              </div>

              {/* Results Section */}
              <div className="results-section">
                <div className="results-header">
                  <h3 className="results-title">
                    Similar Users Results
                    {selectedCandidate && ` for ${selectedCandidate.name}`}
                  </h3>
                </div>

                {error && (
                  <div className="error-message">
                    {error}
                  </div>
                )}

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
                  <div className="no-results">
                    {selectedCandidate 
                      ? "No similar users found for this candidate."
                      : "Please select a candidate to find similar users."
                    }
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>


    </div>
  );
};

export default InteractionsAnalytics; 