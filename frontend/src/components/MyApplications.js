import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { apiService } from '../api';
import './JobSearch.css';

const MyApplications = () => {
  const navigate = useNavigate();
  const [userProfile, setUserProfile] = useState(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [applications, setApplications] = useState([]);

  useEffect(() => {
    const init = async () => {
      try {
        const user = await apiService.validateToken().catch(() => null);
        if (!user) {
          navigate('/login');
          return;
        }
        setUserProfile(user);
        await loadApplications(user.id, '');
      } catch (e) {
        navigate('/login');
      }
    };
    init();
  }, [navigate]);

  const loadApplications = async (candidateId, search) => {
    try {
      setLoading(true);
      setError('');
      const res = await api.get('/applications/public', {
        params: {
          candidate_id: candidateId,
          search: search || undefined,
          limit: 200
        }
      });
      const data = res.data;
      setApplications(Array.isArray(data) ? data : []);
    } catch (e) {
      setError('Failed to load applications');
      setApplications([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!userProfile?.id) return;
    await loadApplications(userProfile.id, query.trim());
  };

  return (
    <div className="job-search">{/* reuse unified header + colors from JobSearch */}
      <div className="unified-header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="header-title">My Applications</h1>
            {userProfile && (
              <p className="welcome-text">{userProfile.name || userProfile.email}</p>
            )}
          </div>
          <div className="header-actions">
            <button className="btn-back" onClick={() => navigate('/candidates-dashboard')}>
              ← Back to Dashboard
            </button>
            <button className="btn-logout" onClick={() => navigate('/login')}>Logout</button>
          </div>
        </div>
      </div>

      <div className="job-search-container">
        <div className="filters-sidebar">
          <div className="filters-content">
            <h2 className="filters-title">Search My Applications</h2>
            <form className="search-section" onSubmit={handleSearch}>
              <div className="search-box">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="search-input"
                  placeholder="Search by job title, company..."
                />
                <button type="submit" className="search-button" disabled={loading}>
                  Search
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="main-content">
          <div className="results-header">
            <h2 className="results-title">Applications ({applications.length})</h2>
          </div>

          {error && (
            <div className="error-message">
              <span>{error}</span>
              <button className="error-close" onClick={() => setError('')}>×</button>
            </div>
          )}

          <div className="search-results">
            <div className="search-results-list">
              <div className="applications-table-wrapper">
                <table className="applications-table">
                  <thead>
                    <tr>
                      <th>Applied On</th>
                      <th>Job Title</th>
                      <th>Company</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {applications.length === 0 && !loading && (
                      <tr>
                        <td colSpan={4} style={{ textAlign: 'center' }}>No applications found</td>
                      </tr>
                    )}
                    {applications.map((a, i) => (
                      <tr key={i}>
                        <td>{a.applied_at ? new Date(a.applied_at).toLocaleDateString() : (a.created_at ? new Date(a.created_at).toLocaleDateString() : '')}</td>
                        <td>{(a.job && a.job.title) || a.job_title || '—'}</td>
                        <td>{(a.job && a.job.company) || a.company || '—'}</td>
                        <td>{a.status || 'APPLIED'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MyApplications;


