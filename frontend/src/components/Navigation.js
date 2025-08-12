import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Navigation.css';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    // Clear all stored data
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('recruiterToken');
    localStorage.removeItem('recruiterUser');
    localStorage.removeItem('candidateToken');
    localStorage.removeItem('candidateUser');
    
    // Navigate to welcome page
    navigate('/');
  };

  const isLoggedIn = () => {
    return localStorage.getItem('token') || 
           localStorage.getItem('recruiterToken') || 
           localStorage.getItem('candidateToken');
  };

  const getUserType = () => {
    if (localStorage.getItem('recruiterToken')) return 'recruiter';
    if (localStorage.getItem('candidateToken')) return 'candidate';
    if (localStorage.getItem('token')) return 'user';
    return null;
  };

  // Don't show navigation on welcome page
  if (location.pathname === '/') {
    return null;
  }

  return (
    <nav className="main-navigation">
      <div className="nav-container">
        <div className="nav-brand">
          <span className="brand-icon">💼</span>
          <span className="brand-text">CV Matcher</span>
        </div>
        
        <div className="nav-links">
          <button 
            className="nav-link"
            onClick={() => navigate('/')}
          >
            🏠 Home
          </button>
          
          {getUserType() === 'recruiter' && (
            <>
              <button 
                className="nav-link"
                onClick={() => navigate('/jobs-dashboard')}
              >
                📋 Jobs
              </button>
              <button 
                className="nav-link"
                onClick={() => navigate('/enhanced-recruiter-recommendations')}
              >
                👥 Find Candidates
              </button>
            </>
          )}
          
          {getUserType() === 'candidate' && (
            <>
              <button 
                className="nav-link"
                onClick={() => navigate('/job-search')}
              >
                🔍 Search Jobs
              </button>
              <button 
                className="nav-link"
                onClick={() => navigate('/enhanced-candidate-recommendations')}
              >
                🎯 My Recommendations
              </button>
            </>
          )}
        </div>
        
        {isLoggedIn() && (
          <div className="nav-actions">
            <span className="user-type">
              {getUserType() === 'recruiter' ? '👔 Recruiter' : 
               getUserType() === 'candidate' ? '👤 Candidate' : '👤 User'}
            </span>
            <button 
              className="logout-btn"
              onClick={handleLogout}
            >
              🚪 Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navigation; 