import React, { useState, useEffect, useMemo } from 'react';
import './InteractionsAnalytics.css';
// Charts
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler
);

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

  // Chart filters - default to show recent data (last 30 days from today)
  const [chartFilters, setChartFilters] = useState({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Last 30 days
    endDate: new Date().toISOString().split('T')[0], // Today
    types: { VIEWED: true, APPLIED: true, REJECTED: true, INTERVIEW_SCHEDULED: true },
    jobTitle: ''
  });

  // Chart visibility - only show when clicked
  const [activeChart, setActiveChart] = useState('daily-trends'); // null, 'daily-trends', 'job-wise', 'distribution', 'funnel'
  
  // Keyboard navigation for carousel
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'ArrowLeft') {
        const charts = ['daily-trends', 'job-wise', 'funnel'];
        const currentIndex = charts.indexOf(activeChart);
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : charts.length - 1;
        setActiveChart(charts[prevIndex]);
      } else if (e.key === 'ArrowRight') {
        const charts = ['daily-trends', 'job-wise', 'funnel'];
        const currentIndex = charts.indexOf(activeChart);
        const nextIndex = currentIndex < charts.length - 1 ? currentIndex + 1 : 0;
        setActiveChart(charts[nextIndex]);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [activeChart]);

  // Touch/swipe support for mobile
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);

  const minSwipeDistance = 50;

  const onTouchStart = (e) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe || isRightSwipe) {
      const charts = ['daily-trends', 'job-wise', 'funnel'];
      const currentIndex = charts.indexOf(activeChart);
      
      if (isLeftSwipe) {
        // Swipe left - go to next chart
        const nextIndex = currentIndex < charts.length - 1 ? currentIndex + 1 : 0;
        setActiveChart(charts[nextIndex]);
      } else if (isRightSwipe) {
        // Swipe right - go to previous chart
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : charts.length - 1;
        setActiveChart(charts[prevIndex]);
      }
    }
  };
  
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

  // ===== Charts: derive data from interactions (same source as table) =====
  const interactionsForCharts = useMemo(() => {
    const list = Array.isArray(recentInteractions) ? recentInteractions : [];
    console.log('📊 Chart data calculation - Total interactions:', list.length);
    console.log('📊 Chart filters:', chartFilters);
    
    // Date range filter
    const start = chartFilters.startDate ? new Date(chartFilters.startDate) : null;
    const end = chartFilters.endDate ? new Date(chartFilters.endDate) : null;
    const jobFilter = (chartFilters.jobTitle || '').toLowerCase();

    const filtered = list.filter(it => {
      // type filter
      if (it.interaction_type && chartFilters.types[it.interaction_type] === false) {
        return false;
      }
      // date filter
      if (it.timestamp) {
        const d = new Date(it.timestamp);
        if (start && d < start) return false;
        if (end) {
          // Include the end date by setting to end-of-day
          const endDay = new Date(end);
          endDay.setHours(23, 59, 59, 999);
          if (d > endDay) return false;
        }
      }
      // job title filter
      if (jobFilter) {
        const jt = (it.job_title || '').toLowerCase();
        if (!jt.includes(jobFilter)) return false;
      }
      return true;
    });
    
    console.log('📊 Filtered interactions for charts:', filtered.length);
    return filtered;
  }, [recentInteractions, chartFilters]);

  // KPI cards (today)
  const kpis = useMemo(() => {
    const today = new Date();
    const y = today.getFullYear(), m = today.getMonth(), d = today.getDate();
    let applied = 0, viewed = 0, rejected = 0;
    interactionsForCharts.forEach(it => {
      if (!it.timestamp) return;
      const t = new Date(it.timestamp);
      if (t.getFullYear() === y && t.getMonth() === m && t.getDate() === d) {
        if (it.interaction_type === 'APPLIED') applied += 1;
        else if (it.interaction_type === 'VIEWED') viewed += 1;
        else if (it.interaction_type === 'REJECTED') rejected += 1;
      }
    });
    return { applied, viewed, rejected };
  }, [interactionsForCharts]);

  // Daily trends (per date per type)
  const dailyTrends = useMemo(() => {
    const map = {}; // dateKey -> { VIEWED, APPLIED, REJECTED }
    interactionsForCharts.forEach(it => {
      if (!it.timestamp) return;
      const d = new Date(it.timestamp);
      const key = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
      if (!map[key]) map[key] = { VIEWED: 0, APPLIED: 0, REJECTED: 0, INTERVIEW_SCHEDULED: 0 };
      const t = it.interaction_type || '';
      if (map[key][t] !== undefined) map[key][t] += 1;
    });
    const labels = Object.keys(map).sort();
    console.log(' Daily trends data:', { labels, map });
    return {
      labels,
      VIEWED: labels.map(l => map[l].VIEWED),
      APPLIED: labels.map(l => map[l].APPLIED),
      REJECTED: labels.map(l => map[l].REJECTED),
      INTERVIEW_SCHEDULED: labels.map(l => map[l].INTERVIEW_SCHEDULED)
    };
  }, [interactionsForCharts]);

  // Job-wise applications (counts by job_title and type)
  const jobWise = useMemo(() => {
    const map = {}; // job_title -> { VIEWED, APPLIED, REJECTED }
    interactionsForCharts.forEach(it => {
      const title = it.job_title || 'Untitled Job';
      if (!map[title]) map[title] = { VIEWED: 0, APPLIED: 0, REJECTED: 0 };
      const t = it.interaction_type || '';
      if (map[title][t] !== undefined) map[title][t] += 1;
    });
    // Sort by total ascending and take top 5 (reverse order)
    const entries = Object.entries(map)
      .map(([title, v]) => ({ title, total: v.VIEWED + v.APPLIED + v.REJECTED, ...v }))
      .sort((a, b) => a.total - b.total)
      .slice(0, 5);
    console.log(' Job-wise data:', entries);
    return entries;
  }, [interactionsForCharts]);

  // Distribution donut
  const distribution = useMemo(() => {
    let viewed = 0, applied = 0, rejected = 0;
    interactionsForCharts.forEach(it => {
      if (it.interaction_type === 'VIEWED') viewed += 1;
      else if (it.interaction_type === 'APPLIED') applied += 1;
      else if (it.interaction_type === 'REJECTED') rejected += 1;
    });
    console.log('🍩 Distribution data:', { viewed, applied, rejected });
    return { viewed, applied, rejected };
  }, [interactionsForCharts]);

  // Funnel data (Viewed -> Applied -> Interview -> Rejected)
  const funnel = useMemo(() => {
    let viewed = 0, applied = 0, interview = 0, rejected = 0;
    interactionsForCharts.forEach(it => {
      if (it.interaction_type === 'VIEWED') viewed += 1;
      if (it.interaction_type === 'APPLIED') applied += 1;
      if (it.interaction_type === 'INTERVIEW_SCHEDULED') interview += 1;
      if (it.interaction_type === 'REJECTED') rejected += 1;
    });
    console.log('🔄 Funnel data:', { viewed, applied, interview, rejected });
    return { viewed, applied, interview, rejected };
  }, [interactionsForCharts]);

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

  // Prevent switching to disabled tabs
  useEffect(() => {
    if (activeTab === 'behavior' || activeTab === 'similar') {
      setActiveTab('interactions');
    }
  }, [activeTab]);

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

      {/* Analytics Dashboard */}
      <div className="analytics-dashboard" style={{marginTop: '12px', marginBottom: '20px'}}>
        {/* Improved Date Range & Chart Controls */}
        <div style={{
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px'
        }}>
          {/* Date Range Controls */}
          <div style={{display:'flex', gap:'16px', alignItems:'center'}}>
            <div style={{display:'flex', alignItems:'center', gap:'8px'}}>
              <label style={{fontSize:14, fontWeight:600, color:'#374151', minWidth:'40px'}}>From:</label>
              <input 
                type="date" 
                value={chartFilters.startDate}
                onChange={(e) => setChartFilters({...chartFilters, startDate: e.target.value})}
                style={{
                  padding:'10px 12px', 
                  border:'1px solid #d1d5db', 
                  borderRadius:6, 
                  fontSize:14,
                  background:'#fff',
                  minWidth:'140px'
                }}
              />
            </div>
            <div style={{display:'flex', alignItems:'center', gap:'8px'}}>
              <label style={{fontSize:14, fontWeight:600, color:'#374151', minWidth:'30px'}}>To:</label>
              <input 
                type="date" 
                value={chartFilters.endDate}
                onChange={(e) => setChartFilters({...chartFilters, endDate: e.target.value})}
                style={{
                  padding:'10px 12px', 
                  border:'1px solid #d1d5db', 
                  borderRadius:6, 
                  fontSize:14,
                  background:'#fff',
                  minWidth:'140px'
                }}
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{display:'flex', gap:'12px', alignItems:'center'}}>
            <button 
              onClick={() => {
                setChartFilters({
                  startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                  endDate: new Date().toISOString().split('T')[0],
                  types: { VIEWED: true, APPLIED: true, REJECTED: true, INTERVIEW_SCHEDULED: true },
                  jobTitle: ''
                });
                fetchRecentInteractions(); // Refresh data
              }}
              style={{
                background:'#3b82f6', 
                color:'white', 
                border:'none', 
                borderRadius:6, 
                padding:'10px 16px', 
                cursor:'pointer',
                fontSize:14,
                fontWeight:500,
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#2563eb';
                e.target.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = '#3b82f6';
                e.target.style.transform = 'translateY(0)';
              }}
            >
               Show Last 7 Days
            </button>
            <button 
              onClick={() => setActiveChart(null)}
              style={{
                background:'#ef4444', 
                color:'white', 
                border:'none', 
                borderRadius:6, 
                padding:'10px 16px', 
                cursor:'pointer',
                fontSize:14,
                fontWeight:500,
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#dc2626';
                e.target.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = '#ef4444';
                e.target.style.transform = 'translateY(0)';
              }}
            >
               Hide Charts
            </button>
          </div>
        </div>

        {/* Tabbed Charts Section */}
        <div style={{
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: '12px',
          marginBottom: '20px',
          overflow: 'hidden'
        }}>
          {/* Chart Tabs */}
          <div style={{
            display: 'flex',
            borderBottom: '1px solid #e5e7eb',
            background: '#f9fafb'
          }}>
            {[
              { id: 'daily-trends', label: 'Daily Trends', icon: '' },
              { id: 'job-wise', label: 'Job-wise Applications', icon: '' },
              { id: 'funnel', label: 'Candidate Funnel', icon: '' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveChart(tab.id)}
                style={{
                  flex: 1,
                  padding: '16px 20px',
                  border: 'none',
                  background: activeChart === tab.id ? '#fff' : 'transparent',
                  borderBottom: activeChart === tab.id ? '3px solid #3b82f6' : '3px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  fontSize: '14px',
                  fontWeight: activeChart === tab.id ? '600' : '500',
                  color: activeChart === tab.id ? '#1f2937' : '#6b7280'
                }}
              >
                <span style={{fontSize: '16px'}}>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>

          {/* Chart Content */}
          <div style={{padding: '20px'}}>
            {/* Daily Trends Chart */}
            {activeChart === 'daily-trends' && (
              <div style={{height: '45vh', minHeight: '400px'}}>
                {dailyTrends.labels.length > 0 ? (
                  <Bar
                    data={{
                      labels: dailyTrends.labels,
                      datasets: [
                        { 
                          label:'Viewed', 
                          data: dailyTrends.VIEWED, 
                          backgroundColor:'#3b82f6',
                          borderColor: '#2563eb',
                          borderWidth: 1
                        },
                        { 
                          label:'Applied', 
                          data: dailyTrends.APPLIED, 
                          backgroundColor:'#10b981',
                          borderColor: '#059669',
                          borderWidth: 1
                        },
                        { 
                          label:'Rejected', 
                          data: dailyTrends.REJECTED, 
                          backgroundColor:'#ef4444',
                          borderColor: '#dc2626',
                          borderWidth: 1
                        },
                        { 
                          label:'Interview', 
                          data: dailyTrends.INTERVIEW_SCHEDULED, 
                          backgroundColor:'#8b5cf6',
                          borderColor: '#7c3aed',
                          borderWidth: 1
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins:{ 
                        legend:{ 
                          position:'top',
                          labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: { size: 12 }
                          }
                        }
                      },
                      scales:{ 
                        x:{ 
                          grid:{ display:true, color: 'rgba(0,0,0,0.1)' },
                          title: {
                            display: true,
                            text: 'Date',
                            font: { size: 12, weight: 'bold' }
                          },
                          ticks: {
                            font: { size: 11 },
                            maxRotation: 45,
                            minRotation: 0
                          }
                        }, 
                        y:{ 
                          beginAtZero:true,
                          title: {
                            display: true,
                            text: 'Count',
                            font: { size: 12, weight: 'bold' }
                          },
                          ticks: {
                            font: { size: 11 },
                            stepSize: 1
                          }
                        } 
                      },
                      interaction: {
                        intersect: false,
                        mode: 'index'
                      }
                    }}
                    height={400}
                  />
                ) : (
                  <div style={{textAlign:'center', padding:'60px', color:'#6b7280'}}>
                    <div style={{fontSize:18, marginBottom:8}}>No data available</div>
                    <div>No interactions found for the selected date range.</div>
                  </div>
                )}
              </div>
            )}

            {/* Job-wise Applications Chart */}
            {activeChart === 'job-wise' && (
              <div style={{height: '45vh', minHeight: '400px'}}>
                {jobWise.length > 0 ? (
                  <Bar
                    data={{
                      labels: jobWise.map(j => j.title.length > 25 ? j.title.substring(0, 25) + '...' : j.title),
                      datasets: [
                        { 
                          label:'Viewed', 
                          data: jobWise.map(j => j.VIEWED || 0), 
                          backgroundColor:'#3b82f6',
                          borderColor: '#2563eb',
                          borderWidth: 1
                        },
                        { 
                          label:'Applied', 
                          data: jobWise.map(j => j.APPLIED || 0), 
                          backgroundColor:'#10b981',
                          borderColor: '#059669',
                          borderWidth: 1
                        },
                        { 
                          label:'Rejected', 
                          data: jobWise.map(j => j.REJECTED || 0), 
                          backgroundColor:'#ef4444',
                          borderColor: '#dc2626',
                          borderWidth: 1
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins:{ 
                        legend:{ 
                          position:'top',
                          labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: { size: 12 }
                          }
                        }
                      },
                      scales:{ 
                        x:{ 
                          title: {
                            display: true,
                            text: 'Job Titles',
                            font: { size: 12, weight: 'bold' }
                          },
                          ticks: {
                            font: { size: 11 },
                            maxRotation: 45,
                            minRotation: 0
                          }
                        },
                        y: {
                          beginAtZero:true,
                          title: {
                            display: true,
                            text: 'Count',
                            font: { size: 12, weight: 'bold' }
                          },
                          ticks: {
                            font: { size: 11 },
                            stepSize: 1
                          }
                        }
                      }
                    }}
                    height={400}
                  />
                ) : (
                  <div style={{textAlign:'center', padding:'60px', color:'#6b7280'}}>
                    <div style={{fontSize:18, marginBottom:8}}>No data available</div>
                    <div>No job applications found for the selected date range.</div>
                  </div>
                )}
              </div>
            )}

            {/* Candidate Funnel Chart - Compact Widget */}
            {activeChart === 'funnel' && (
              <div style={{height: '120px', display: 'flex', alignItems: 'center'}}>
                {(funnel.viewed + funnel.applied + funnel.interview + funnel.rejected) > 0 ? (
                  <div style={{display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:'16px', width: '100%'}}>
                    {[
                      {label:'Viewed', value:funnel.viewed, color:'#3b82f6'},
                      {label:'Applied', value:funnel.applied, color:'#10b981'},
                      {label:'Interview', value:funnel.interview, color:'#8b5cf6'},
                      {label:'Rejected', value:funnel.rejected, color:'#ef4444'}
                    ].map(step => (
                      <div key={step.label} style={{
                        background:'#f9fafb', 
                        border:'1px solid #e5e7eb', 
                        borderRadius:8, 
                        padding:12, 
                        textAlign:'center',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        height: '100px'
                      }}>
                        <div style={{fontSize:12, fontWeight:600, color:'#374151', marginBottom:4}}>{step.label}</div>
                        <div style={{height:4, background:'#e5e7eb', borderRadius:999, marginBottom:6}}>
                          <div style={{width:`${step.value === 0 ? 2 : 100}%`, maxWidth:'100%', height:'100%', background:step.color, borderRadius:999}} />
                        </div>
                        <div style={{fontSize:20, fontWeight:700, color:step.color}}>{step.value}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{textAlign:'center', padding:'20px', color:'#6b7280', width: '100%'}}>
                    <div style={{fontSize:16, marginBottom:4}}>No data available</div>
                    <div style={{fontSize:12}}>No candidate funnel data found for the selected date range.</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

      </div>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'interactions' ? 'active' : ''}`}
          onClick={() => setActiveTab('interactions')}
        >
          Interaction History
        </button>
        <button 
          className={`tab disabled ${activeTab === 'behavior' ? 'active' : ''}`}
          onClick={() => {}} // Disabled - no action
          disabled
          title="Behavior Patterns feature is currently disabled"
        >
          Behavior Patterns
        </button>
        <button 
          className={`tab disabled ${activeTab === 'similar' ? 'active' : ''}`}
          onClick={() => {}} // Disabled - no action
          disabled
          title="Similar Users feature is currently disabled"
        >
          Similar Users
        </button>
      </div>

      <div className="content-area">
        {activeTab === 'interactions' && (
          <div className="analytics-section">
            <h2>Interaction History</h2>
            
            {/* Dashboard Layout with Sidebar */}
            <div className="dashboard-layout" style={{maxWidth: '100%', overflow: 'hidden'}}>
              {/* Filters Sidebar */}
              <div className="filters-sidebar">
                <div className="sidebar-header">
                  <h3 className="sidebar-title">Filter & Search</h3>
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
              <div className="candidates-content" style={{maxWidth: '100%', overflow: 'hidden'}}>
                <div className="results-header">
                  <h3 className="results-title">
                    {selectedCandidate 
                      ? `Interactions for ${selectedCandidate.name}` 
                      : 'Recent Interactions'
                    }
                  </h3>
                </div>

                {/* Table Filter Bar */}
                <div style={{
                  background: '#f8fafc',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '16px 20px',
                  marginBottom: '16px',
                  display: 'flex',
                  gap: '16px',
                  alignItems: 'center',
                  flexWrap: 'wrap'
                }}>
                  <div style={{display: 'flex', alignItems: 'center', gap: '8px', minWidth: '200px'}}>
                    <label style={{fontSize: '14px', fontWeight: '600', color: '#374151', minWidth: '80px'}}>
                      Candidate:
                    </label>
                    <input
                      type="text"
                      value={searchName}
                      onChange={(e) => setSearchName(e.target.value)}
                      placeholder="Search by candidate name..."
                      style={{
                        padding: '8px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        fontSize: '14px',
                        background: '#fff',
                        flex: 1,
                        minWidth: '120px'
                      }}
                    />
                  </div>
                  <div style={{display: 'flex', alignItems: 'center', gap: '8px', minWidth: '200px'}}>
                    <label style={{fontSize: '14px', fontWeight: '600', color: '#374151', minWidth: '60px'}}>
                      Job:
                    </label>
                    <input
                      type="text"
                      value={searchJobTitle}
                      onChange={(e) => setSearchJobTitle(e.target.value)}
                      placeholder="Search by job title..."
                      style={{
                        padding: '8px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        fontSize: '14px',
                        background: '#fff',
                        flex: 1,
                        minWidth: '120px'
                      }}
                    />
                  </div>
                  <div style={{marginLeft: 'auto'}}>
                    <button
                      onClick={() => {
                        setSearchName('');
                        setSearchJobTitle('');
                      }}
                      style={{
                        padding: '8px 16px',
                        background: '#6b7280',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: '500'
                      }}
                    >
                      Clear Filters
                    </button>
                  </div>
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
          <div className="analytics-section disabled-section">
            <h2>Behavior Patterns</h2>
            <div className="disabled-message">
              <p>🚫 Behavior Patterns feature is currently disabled</p>
              <p>This functionality is temporarily unavailable.</p>
            </div>
            
            {/* Dashboard Layout with Sidebar */}
            <div className="dashboard-layout">
              {/* Filters Sidebar */}
              <div className="filters-sidebar">
                <div className="sidebar-header">
                  <h3 className="sidebar-title">Filter & Search</h3>
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
          <div className="analytics-section disabled-section">
            <h2>Similar Users</h2>
            <div className="disabled-message">
              <p>🚫 Similar Users feature is currently disabled</p>
              <p>This functionality is temporarily unavailable.</p>
            </div>
            
            {/* Dashboard Layout with Sidebar */}
            <div className="dashboard-layout">
              {/* Filters Sidebar */}
              <div className="filters-sidebar">
                <div className="sidebar-header">
                  <h3 className="sidebar-title">Filter & Search</h3>
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