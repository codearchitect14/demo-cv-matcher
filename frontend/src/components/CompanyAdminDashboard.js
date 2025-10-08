import React, { useState, useEffect } from 'react';
import CompanyManagement from './CompanyManagement';
import RecruiterAdmin from './RecruiterAdmin';
import './CompanyAdminDashboard.css';

const CompanyAdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('company');
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch company information on component mount
  useEffect(() => {
    const fetchCompanyInfo = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/company/my-company');
        if (response.ok) {
          const data = await response.json();
          setCompany(data);
        } else {
          console.error('Failed to fetch company info:', response.status);
        }
      } catch (error) {
        console.error('Error fetching company info:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCompanyInfo();
  }, []);

  // Handle logout
  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  if (loading) {
    return (
      <div className="company-admin-dashboard">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="company-admin-dashboard">
      <div className="admin-header">
        <div className="header-left">
          <h1>Company Admin Dashboard</h1>
          {company && (
            <div className="company-info">
              <span className="company-name">{company.name}</span>
              <span className="company-domain">({company.domain})</span>
            </div>
          )}
        </div>
        
        <div className="header-actions">
          <button 
            className="btn-back"
            onClick={() => window.location.href = '/jobs-dashboard'}
          >
            ← Back to Jobs
          </button>
          <button 
            className="btn-logout"
            onClick={handleLogout}
          >
            🚪 Logout
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="tab-navigation">
          <button 
            className={`tab-button ${activeTab === 'company' ? 'active' : ''}`}
            onClick={() => setActiveTab('company')}
          >
            🏢 Company Management
          </button>
          <button 
            className={`tab-button ${activeTab === 'recruiters' ? 'active' : ''}`}
            onClick={() => setActiveTab('recruiters')}
          >
            👥 Recruiter Management
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'company' && <CompanyManagement />}
          {activeTab === 'recruiters' && <RecruiterAdmin />}
        </div>
      </div>
    </div>
  );
};

export default CompanyAdminDashboard;
