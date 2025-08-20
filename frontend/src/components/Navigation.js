import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Navigation.css';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

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

  // Don't show navigation on welcome and auth pages
  const hiddenNavPaths = [
    '/',
    '/login',
    '/login-new',
    '/signup',
    '/signup-new',
    '/recruiter/login',
    '/recruiter/register'
  ];
  if (hiddenNavPaths.includes(location.pathname)) {
    return null;
  }

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  return (
    <nav className="main-navigation">
      <div className="nav-container">
        <div className="nav-brand" onClick={() => navigate('/')}>
          <span className="brand-icon">
            <i className="fas fa-bullseye"></i>
          </span>
          <span className="brand-text">CV Matcher</span>
        </div>
        
        <button 
          className={`mobile-menu-toggle ${isMobileMenuOpen ? 'active' : ''}`}
          onClick={toggleMobileMenu}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
        
        <div className={`nav-links ${isMobileMenuOpen ? 'active' : ''}`}>
                      <button 
              className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
              onClick={() => {
                navigate('/');
                closeMobileMenu();
              }}
            >
              <i className="fas fa-home"></i> Home
            </button>
          
          {getUserType() === 'recruiter' && (
            <>
              <button 
                className={`nav-link ${location.pathname === '/jobs-dashboard' ? 'active' : ''}`}
                onClick={() => {
                  navigate('/jobs-dashboard');
                  closeMobileMenu();
                }}
              >
                <i className="fas fa-clipboard-list"></i> Jobs
              </button>
              <button 
                className={`nav-link ${location.pathname === '/enhanced-recruiter-recommendations' ? 'active' : ''}`}
                onClick={() => {
                  navigate('/enhanced-recruiter-recommendations');
                  closeMobileMenu();
                }}
              >
                <i className="fas fa-users"></i> Find Candidates
              </button>
            </>
          )}
          
          {getUserType() === 'candidate' && (
            <>
              <button 
                className={`nav-link ${location.pathname === '/job-search' ? 'active' : ''}`}
                onClick={() => {
                  navigate('/job-search');
                  closeMobileMenu();
                }}
              >
                <i className="fas fa-search"></i> Search Jobs
              </button>
              <button 
                className={`nav-link ${location.pathname === '/enhanced-candidate-recommendations' ? 'active' : ''}`}
                onClick={() => {
                  navigate('/enhanced-candidate-recommendations');
                  closeMobileMenu();
                }}
              >
                <i className="fas fa-bullseye"></i> My Recommendations
              </button>
            </>
          )}
        </div>
        
        {isLoggedIn() && (
          <div className="nav-actions">
            <span className="user-type">
              {getUserType() === 'recruiter' ? <><i className="fas fa-user-tie"></i> Recruiter</> : 
               getUserType() === 'candidate' ? <><i className="fas fa-user"></i> Candidate</> : <><i className="fas fa-user"></i> User</>}
            </span>
            <button 
              className="logout-btn"
              onClick={() => {
                handleLogout();
                closeMobileMenu();
              }}
            >
              <i className="fas fa-sign-out-alt"></i> Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navigation; 