import React, { useState, useEffect } from 'react';
import './CompanyManagement.css';

const CompanyManagement = () => {
  const [company, setCompany] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showEditForm, setShowEditForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    description: '',
    max_recruiters: 10,
    max_jobs: 100,
    contact_email: '',
    contact_phone: '',
    address: '',
    subscription_plan: 'basic'
  });

  // Fetch company information
  const fetchCompanyInfo = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/company/my-company');
      if (response.ok) {
        const data = await response.json();
        setCompany(data);
        setFormData({
          name: data.name || '',
          domain: data.domain || '',
          description: data.description || '',
          max_recruiters: data.max_recruiters || 10,
          max_jobs: data.max_jobs || 100,
          contact_email: data.contact_email || '',
          contact_phone: data.contact_phone || '',
          address: data.address || '',
          subscription_plan: data.subscription_plan || 'basic'
        });
      } else {
        setError('Failed to fetch company information');
      }
    } catch (error) {
      setError('Error fetching company information: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch company statistics
  const fetchCompanyStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/company/my-company/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching company stats:', error);
    }
  };

  useEffect(() => {
    fetchCompanyInfo();
    fetchCompanyStats();
  }, []);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/company/my-company', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const result = await response.json();
        setCompany(result);
        setShowEditForm(false);
        fetchCompanyInfo();
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail) || 'Failed to update company';
        setError(errorMessage);
      }
    } catch (error) {
      setError('Error updating company: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle logout
  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  if (loading && !company) {
    return (
      <div className="company-management">
        <div className="loading">Loading company information...</div>
      </div>
    );
  }

  return (
    <div className="company-management">
      <div className="admin-header">
        <h1>Company Management</h1>
        <div className="header-actions">
          <button 
            className="btn-back"
            onClick={() => window.location.href = '/jobs-dashboard'}
          >
            ← Back to Dashboard
          </button>
          <button 
            className="btn-logout"
            onClick={handleLogout}
          >
            🚪 Logout
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {String(error)}
        </div>
      )}

      {company && (
        <div className="company-content">
          {/* Company Information Card */}
          <div className="info-card">
            <div className="card-header">
              <h2>Company Information</h2>
              <button 
                className="btn btn-secondary"
                onClick={() => setShowEditForm(true)}
              >
                ✏️ Edit Company
              </button>
            </div>
            
            <div className="info-grid">
              <div className="info-item">
                <label>Company Name</label>
                <span>{String(company.name || '')}</span>
              </div>
              
              <div className="info-item">
                <label>Domain</label>
                <span>{String(company.domain || '')}</span>
              </div>
              
              <div className="info-item">
                <label>Subscription Plan</label>
                <span className={`plan-badge ${company.subscription_plan}`}>
                  {String(company.subscription_plan || '').toUpperCase()}
                </span>
              </div>
              
              <div className="info-item">
                <label>Status</label>
                <span className={`status-badge ${company.is_active ? 'active' : 'inactive'}`}>
                  {company.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div className="info-item">
                <label>Contact Email</label>
                <span>{company.contact_email || 'Not provided'}</span>
              </div>
              
              <div className="info-item">
                <label>Contact Phone</label>
                <span>{company.contact_phone || 'Not provided'}</span>
              </div>
              
              <div className="info-item full-width">
                <label>Description</label>
                <span>{company.description || 'No description provided'}</span>
              </div>
              
              <div className="info-item full-width">
                <label>Address</label>
                <span>{company.address || 'No address provided'}</span>
              </div>
            </div>
          </div>

          {/* Company Statistics */}
          {stats && (
            <div className="stats-card">
              <h2>Company Statistics</h2>
              <div className="stats-grid">
                <div className="stat-item">
                  <div className="stat-number">{stats.total_recruiters}</div>
                  <div className="stat-label">Total Recruiters</div>
                </div>
                
                <div className="stat-item">
                  <div className="stat-number">{stats.active_recruiters}</div>
                  <div className="stat-label">Active Recruiters</div>
                </div>
                
                <div className="stat-item">
                  <div className="stat-number">{stats.total_jobs}</div>
                  <div className="stat-label">Total Jobs</div>
                </div>
                
                <div className="stat-item">
                  <div className="stat-number">{stats.active_jobs}</div>
                  <div className="stat-label">Active Jobs</div>
                </div>
                
                <div className="stat-item">
                  <div className="stat-number">{stats.total_applications}</div>
                  <div className="stat-label">Total Applications</div>
                </div>
                
                <div className="stat-item">
                  <div className="stat-number">{stats.pending_applications}</div>
                  <div className="stat-label">Pending Applications</div>
                </div>
              </div>
            </div>
          )}

          {/* Company Limits */}
          <div className="limits-card">
            <h2>Company Limits</h2>
            <div className="limits-grid">
              <div className="limit-item">
                <label>Maximum Recruiters</label>
                <span>{company.max_recruiters}</span>
              </div>
              
              <div className="limit-item">
                <label>Maximum Jobs</label>
                <span>{company.max_jobs}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Company Form Modal */}
      {showEditForm && (
        <div className="modal-overlay" onClick={() => setShowEditForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit Company Information</h2>
              <button className="modal-close" onClick={() => setShowEditForm(false)}>✕</button>
            </div>
            
            <form onSubmit={handleSubmit} className="company-form">
              <div className="form-grid">
                <div className="form-group">
                  <label>Company Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Domain *</label>
                  <select
                    value={formData.domain}
                    onChange={(e) => setFormData({...formData, domain: e.target.value})}
                    required
                    className="form-input"
                  >
                    <option value="">Select Domain</option>
                    <option value="IT">IT</option>
                    <option value="Healthcare">Healthcare</option>
                    <option value="Finance">Finance</option>
                    <option value="Education">Education</option>
                    <option value="Manufacturing">Manufacturing</option>
                    <option value="Retail">Retail</option>
                    <option value="Consulting">Consulting</option>
                    <option value="Media">Media</option>
                    <option value="Real Estate">Real Estate</option>
                    <option value="Transportation">Transportation</option>
                    <option value="Energy">Energy</option>
                    <option value="Telecommunications">Telecommunications</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Contact Email</label>
                  <input
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Contact Phone</label>
                  <input
                    type="tel"
                    value={formData.contact_phone}
                    onChange={(e) => setFormData({...formData, contact_phone: e.target.value})}
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Max Recruiters</label>
                  <input
                    type="number"
                    value={formData.max_recruiters}
                    onChange={(e) => setFormData({...formData, max_recruiters: parseInt(e.target.value)})}
                    min="1"
                    max="1000"
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Max Jobs</label>
                  <input
                    type="number"
                    value={formData.max_jobs}
                    onChange={(e) => setFormData({...formData, max_jobs: parseInt(e.target.value)})}
                    min="1"
                    max="10000"
                    className="form-input"
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  rows="3"
                  className="form-input"
                />
              </div>
              
              <div className="form-group">
                <label>Address</label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  rows="2"
                  className="form-input"
                />
              </div>
              
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowEditForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Updating...' : 'Update Company'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompanyManagement;
