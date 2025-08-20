import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FaClipboardList, 
  FaUsers, 
  FaCheck, 
  FaChartBar, 
  FaFileAlt, 
  FaUser, 
  FaSignOutAlt, 
  FaBolt, 
  FaClock,
  FaArrowRight
} from 'react-icons/fa';
import './RecruiterDashboard.css';

const RecruiterDashboard = () => {
  const navigate = useNavigate();
  const [recruiterData, setRecruiterData] = useState(null);
  const [stats, setStats] = useState({
    totalJobs: 12,
    activeJobs: 8,
    totalApplications: 45,
    pendingApplications: 23
  });
  const [recentActivity] = useState([
    {
      id: 1,
      type: 'job_posted',
      title: 'New job posted: Senior Python Developer',
      time: '2 hours ago',
      icon: <FaClipboardList />,
      color: '#667eea'
    },
    {
      id: 2,
      type: 'applications',
      title: '5 new applications for React Developer position',
      time: '4 hours ago',
      icon: <FaUsers />,
      color: '#e74c3c'
    },
    {
      id: 3,
      type: 'reviewed',
      title: 'Application reviewed: John Doe for Frontend Developer',
      time: '1 day ago',
      icon: <FaCheck />,
      color: '#28a745'
    }
  ]);

  useEffect(() => {
    // Get recruiter data from localStorage
    const recruiterUser = localStorage.getItem('recruiterUser');
    if (recruiterUser) {
      setRecruiterData(JSON.parse(recruiterUser));
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('recruiterToken');
    localStorage.removeItem('recruiterUser');
    navigate('/recruiter/login');
  };

  const dashboardActions = [
    {
      title: "Manage Job Posts",
      description: "Create, edit, and manage your job postings",
      action: () => navigate('/jobs-dashboard'),
      color: "#667eea",
      icon: <FaClipboardList />,
      gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    },
    {
      title: "Find Candidates",
      description: "Search and match candidates for your jobs",
      action: () => navigate('/enhanced-recruiter-recommendations'),
      color: "#e74c3c",
      icon: <FaUsers />,
      gradient: "linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)"
    },
    {
      title: "View Analytics",
      description: "Track job performance and candidate interactions",
      action: () => navigate('/interactions-analytics'),
      color: "#28a745",
      icon: <FaChartBar />,
      gradient: "linear-gradient(135deg, #28a745 0%, #20c997 100%)"
    },
    {
      title: "Applications",
      description: "Manage and review job applications",
      action: () => navigate('/applications-management'),
      color: "#fd7e14",
      icon: <FaFileAlt />,
      gradient: "linear-gradient(135deg, #fd7e14 0%, #ff6b35 100%)"
    }
  ];

  return (
    <div className="modern-recruiter-dashboard">
      {/* Animated Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <div className="header-text">
              <h1 className="header-title">Recruiter Dashboard</h1>
              <p className="header-subtitle">Welcome back, {recruiterData?.full_name || 'Recruiter'}!</p>
            </div>
          </div>
          <div className="header-actions">
            <button className="btn-profile" onClick={() => alert('Profile settings coming soon!')}>
              <span className="btn-icon"><FaUser /></span>
              Profile
            </button>
            <button className="btn-logout" onClick={handleLogout}>
              <span className="btn-icon"><FaSignOutAlt /></span>
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-section">
        <div className="stats-grid">
          <div className="stat-card" style={{animationDelay: '0.1s'}}>
            <div className="stat-icon"><FaClipboardList /></div>
            <div className="stat-content">
              <h3 className="stat-number">{stats.totalJobs}</h3>
              <p className="stat-label">Total Jobs</p>
            </div>
            <div className="stat-progress">
              <div className="progress-bar" style={{width: '75%'}}></div>
            </div>
          </div>
          
          <div className="stat-card" style={{animationDelay: '0.2s'}}>
            <div className="stat-icon"><FaCheck /></div>
            <div className="stat-content">
              <h3 className="stat-number">{stats.activeJobs}</h3>
              <p className="stat-label">Active Jobs</p>
            </div>
            <div className="stat-progress">
              <div className="progress-bar" style={{width: '60%'}}></div>
            </div>
          </div>
          
          <div className="stat-card" style={{animationDelay: '0.3s'}}>
            <div className="stat-icon"><FaFileAlt /></div>
            <div className="stat-content">
              <h3 className="stat-number">{stats.totalApplications}</h3>
              <p className="stat-label">Total Applications</p>
            </div>
            <div className="stat-progress">
              <div className="progress-bar" style={{width: '85%'}}></div>
            </div>
          </div>
          
          <div className="stat-card" style={{animationDelay: '0.4s'}}>
            <div className="stat-icon"><FaClock /></div>
            <div className="stat-content">
              <h3 className="stat-number">{stats.pendingApplications}</h3>
              <p className="stat-label">Pending Reviews</p>
            </div>
            <div className="stat-progress">
              <div className="progress-bar" style={{width: '45%'}}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="actions-section">
        <h2 className="section-title">
          <span className="title-icon"><FaBolt /></span>
          Quick Actions
        </h2>
        <div className="actions-grid">
          {dashboardActions.map((action, index) => (
            <div 
              key={index} 
              className="action-card"
              style={{
                animationDelay: `${0.5 + index * 0.1}s`,
                background: action.gradient
              }}
              onClick={action.action}
            >
              <div className="action-icon">{action.icon}</div>
              <div className="action-content">
                <h3 className="action-title">{action.title}</h3>
                <p className="action-description">{action.description}</p>
              </div>
              <div className="action-arrow"><FaArrowRight /></div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="activity-section">
        <h2 className="section-title">
          <span className="title-icon"><FaChartBar /></span>
          Recent Activity
        </h2>
        <div className="activity-list">
          {recentActivity.map((activity, index) => (
            <div 
              key={activity.id} 
              className="activity-item"
              style={{animationDelay: `${0.9 + index * 0.1}s`}}
            >
              <div className="activity-icon" style={{backgroundColor: activity.color}}>
                {activity.icon}
              </div>
              <div className="activity-content">
                <h4 className="activity-title">{activity.title}</h4>
                <p className="activity-time">{activity.time}</p>
              </div>
              <div className="activity-status"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RecruiterDashboard; 