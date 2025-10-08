import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './RecruiterDashboard.css';

const RecruiterDashboard = () => {
  const navigate = useNavigate();
  const [recruiterData, setRecruiterData] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
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
      iconClass: 'fa-clipboard-list',
      color: '#667eea'
    },
    {
      id: 2,
      type: 'applications',
      title: '5 new applications for React Developer position',
      time: '4 hours ago',
      iconClass: 'fa-users',
      color: '#e74c3c'
    },
    {
      id: 3,
      type: 'reviewed',
      title: 'Application reviewed: John Doe for Frontend Developer',
      time: '1 day ago',
      iconClass: 'fa-circle-check',
      color: '#28a745'
    }
  ]);

  useEffect(() => {
    // Get recruiter data from localStorage
    const recruiterUser = localStorage.getItem('recruiterUser');
    if (recruiterUser) {
      setRecruiterData(JSON.parse(recruiterUser));
    }
    
    // Fetch notifications when component mounts
    if (recruiterUser) {
      fetchNotifications();
    }
  }, []);

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('recruiterToken');
      const response = await fetch('/api/v1/recruiter-notifications/my-notifications', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const notificationsData = await response.json();
        // Filter notifications from last 7 days
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        
        const filteredNotifications = notificationsData.filter(notification => 
          new Date(notification.created_at) >= sevenDaysAgo
        );
        
        setNotifications(filteredNotifications);
        setUnreadCount(filteredNotifications.filter(n => !n.is_read).length);
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markNotificationAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem('recruiterToken');
      await fetch(`/api/v1/recruiter-notifications/${notificationId}/mark-read`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      // Update local state
      setNotifications(notifications.map(notification => 
        notification.id === notificationId 
          ? { ...notification, is_read: true }
          : notification
      ));
      
      // Recalculate unread count
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllNotificationsAsRead = async () => {
    try {
      const token = localStorage.getItem('recruiterToken');
      await fetch('/api/v1/recruiter-notifications/mark-all-read', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      // Update local state
      setNotifications(notifications.map(notification => 
        ({ ...notification, is_read: true })
      ));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

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
      icon: "ðŸ“‹",
      gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    },
    {
      title: "Find Candidates",
      description: "Search and match candidates for your jobs",
      action: () => navigate('/enhanced-recruiter-recommendations'),
      color: "#e74c3c",
      icon: "ðŸ‘¥",
      gradient: "linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)"
    },
    {
      title: "View Analytics",
      description: "Track job performance and candidate interactions",
      action: () => navigate('/interactions-analytics'),
      color: "#28a745",
      icon: "ðŸ“Š",
      gradient: "linear-gradient(135deg, #28a745 0%, #20c997 100%)"
    },
    {
      title: "Applications",
      description: "Manage and review job applications",
      action: () => {
        // Check if user is admin (db10@boolmind.com)
        const user = JSON.parse(localStorage.getItem('recruiterUser') || '{}');
        if (user.email === 'db10@boolmind.com') {
          navigate('/applications-management');
        } else {
          navigate('/recruiter/applications');
        }
      },
      color: "#fd7e14",
      icon: "ðŸ“",
      gradient: "linear-gradient(135deg, #fd7e14 0%, #ff6b35 100%)"
    }
  ];

  return (
    <div className="modern-recruiter-dashboard">
      {/* Animated Header */}
      <div className="recruiter-dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <div className="header-icon">
              <i className="fa-solid fa-building"></i>
            </div>
            <div className="header-text">
              <h1 className="header-title">Boolmind</h1>
              <p className="header-subtitle">Welcome back, {recruiterData?.full_name || 'Recruiter'}!</p>
            </div>
          </div>
          <div className="header-actions">
            {/* Notification Bell */}
            <div className="notification-container">
              <button 
                className="notification-bell" 
                onClick={() => setShowNotifications(!showNotifications)}
                title="Notifications"
              >
                <i className="fa-solid fa-bell"></i>
                {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
              </button>
              
              {showNotifications && (
                <div className="notification-dropdown">
                  <div className="notification-header">
                    <h3>Notifications (Last 7 Days)</h3>
                    <button 
                      className="close-notifications"
                      onClick={() => setShowNotifications(false)}
                    >
                      <i className="fa-solid fa-times"></i>
                    </button>
                  </div>
                  
                  <div className="notification-list">
                    {notifications.length === 0 ? (
                      <div className="no-notifications">
                        <i className="fa-solid fa-bell-slash"></i>
                        <p>No notifications yet</p>
                      </div>
                    ) : (
                      <>
                        {notifications.map(notification => (
                          <div 
                            key={notification.id} 
                            className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
                            onClick={() => !notification.is_read && markNotificationAsRead(notification.id)}
                          >
                            <div className="notification-content">
                              <h4 className="notification-title">{notification.title}</h4>
                              <p className="notification-message">{notification.message}</p>
                              <span className="notification-time">
                                {new Date(notification.created_at).toLocaleDateString()} at{' '}
                                {new Date(notification.created_at).toLocaleTimeString()}
                              </span>
                            </div>
                            {!notification.is_read && <div className="unread-indicator"></div>}
                          </div>
                        ))}
                        
                        {unreadCount > 0 && (
                          <div className="notification-actions">
                            <button 
                              className="mark-all-read"
                              onClick={markAllNotificationsAsRead}
                            >
                              Mark All as Read
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            <button className="btn-profile" onClick={() => alert('Profile settings coming soon!')}>
              <span className="btn-icon"><i className="fa-solid fa-user"></i></span>
              Profile
            </button>
            <button className="btn-logout" onClick={handleLogout}>
              <span className="btn-icon"><i className="fa-solid fa-right-from-bracket"></i></span>
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-section">
        <div className="stats-grid">
          <div className="stat-card" style={{animationDelay: '0.1s'}}>
            <div className="stat-icon"><i className="fa-solid fa-clipboard-list"></i></div>
            <div className="stat-content">
              <h3 className="stat-number">{stats.totalJobs}</h3>
              <p className="stat-label">Total Jobs</p>
            </div>
            <div className="stat-progress">
              <div className="progress-bar" style={{width: '75%'}}></div>
            </div>
          </div>
          
          <div className="stat-card" style={{animationDelay: '0.2s'}}>
            <div className="stat-icon"><i className="fa-solid fa-circle-check"></i></div>
            <div className="stat-content">
              <h3 className="stat-number">{stats.activeJobs}</h3>
              <p className="stat-label">Active Jobs</p>
            </div>
            <div className="stat-progress">
              <div className="progress-bar" style={{width: '60%'}}></div>
            </div>
          </div>
          
          <div className="stat-card" style={{animationDelay: '0.3s'}}>
            <div className="stat-icon"><i className="fa-solid fa-file-lines"></i></div>
            <div className="stat-content">
              <h3 className="stat-number">{stats.totalApplications}</h3>
              <p className="stat-label">Total Applications</p>
            </div>
            <div className="stat-progress">
              <div className="progress-bar" style={{width: '85%'}}></div>
            </div>
          </div>
          
          <div className="stat-card" style={{animationDelay: '0.4s'}}>
            <div className="stat-icon"><i className="fa-solid fa-clock"></i></div>
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
          <span className="title-icon">
            <i className="fa-solid fa-bolt"></i>
          </span>
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
              <div className="action-icon">{action.icon || 'âš™ï¸'}</div>
              <div className="action-content">
                <h3 className="action-title">{action.title}</h3>
                <p className="action-description">{action.description}</p>
              </div>
              <div className="action-arrow"><i className="fa-solid fa-arrow-right"></i></div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="activity-section">
        <h2 className="section-title">
          <span className="title-icon"><i className="fa-solid fa-chart-line"></i></span>
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
                <i className={`fa-solid ${activity.iconClass}`}></i>
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
