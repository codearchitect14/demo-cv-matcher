import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './WelcomePage.css';

const WelcomePage = () => {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);
  const [selectedRole, setSelectedRole] = useState(null);

  React.useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleRoleSelect = (role) => {
    setSelectedRole(role);
  };

  const handleLogin = () => {
    if (selectedRole === 'candidate') {
      navigate('/login-new');
    } else if (selectedRole === 'recruiter') {
      navigate('/recruiter/login');
    }
  };

  const handleRegister = () => {
    if (selectedRole === 'candidate') {
      navigate('/signup-new');
    } else if (selectedRole === 'recruiter') {
      navigate('/recruiter/register');
    }
  };

  const handleBack = () => {
    setSelectedRole(null);
  };

  return (
    <div className={`welcome-container ${isVisible ? 'visible' : ''}`}>
      {/* Animated Background */}
      <div className="welcome-background">
        <div className="gradient-overlay"></div>
        <div className="floating-shapes">
          <div className="shape shape-1"></div>
          <div className="shape shape-2"></div>
          <div className="shape shape-3"></div>
          <div className="shape shape-4"></div>
          <div className="shape shape-5"></div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="welcome-content-wrapper">
        <div className="welcome-card">
          {/* Header Section */}
          <div className="welcome-header">
            <div className="logo-container">
              <div className="logo-icon">
                <i className="fas fa-bullseye"></i>
              </div>
              <h1 className="logo-text">CV Matcher</h1>
            </div>
            <h2 className="welcome-title">Welcome to the Future of Hiring</h2>
            <p className="welcome-description">
              Connect talented candidates with amazing opportunities through AI-powered matching
            </p>
          </div>

          {/* Role Selection */}
          {!selectedRole ? (
            <div className="role-selection">
              <h3 className="role-selection-title">Choose your role</h3>
              <div className="role-cards">
                <div 
                  className="role-card candidate-card" 
                  onClick={() => handleRoleSelect('candidate')}
                >
                  <div className="role-card-icon">
                    <div className="icon-circle candidate-icon">
                      <i className="fas fa-user"></i>
                    </div>
                  </div>
                  <div className="role-card-content">
                    <h4>I'm a Candidate</h4>
                    <p>Find your dream job with personalized recommendations</p>
                    <div className="role-features">
                      <span><i className="fas fa-robot"></i> AI-Powered Matching</span>
                      <span><i className="fas fa-chart-line"></i> Career Growth</span>
                      <span><i className="fas fa-briefcase"></i> Top Companies</span>
                    </div>
                  </div>
                  <div className="role-card-arrow">→</div>
                </div>
                
                <div 
                  className="role-card recruiter-card" 
                  onClick={() => handleRoleSelect('recruiter')}
                >
                  <div className="role-card-icon">
                    <div className="icon-circle recruiter-icon">
                      <i className="fas fa-building"></i>
                    </div>
                  </div>
                  <div className="role-card-content">
                    <h4>I'm a Recruiter</h4>
                    <p>Post jobs and discover exceptional talent</p>
                    <div className="role-features">
                      <span><i className="fas fa-search"></i> Smart Screening</span>
                      <span><i className="fas fa-chart-bar"></i> Analytics</span>
                      <span><i className="fas fa-bolt"></i> Quick Hiring</span>
                    </div>
                  </div>
                  <div className="role-card-arrow">→</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="role-selection">
              <div className="welcome-actions">
                <button className="welcome-btn welcome-btn-back" onClick={handleBack}>
                  ← Back
                </button>
              </div>
              
              <h3 className="role-selection-title">
                {selectedRole === 'candidate' ? 'Join as a Candidate' : 'Join as a Recruiter'}
              </h3>
              
              <div className="role-cards">
                <div className="role-card">
                  <div className="role-card-icon">
                    <div className="icon-circle candidate-icon">
                      <i className="fas fa-lock"></i>
                    </div>
                  </div>
                  <div className="role-card-content">
                    <h4>Already have an account?</h4>
                    <p>Sign in to access your dashboard</p>
                  </div>
                  <div className="role-card-arrow">→</div>
                </div>
                
                <div className="role-card">
                  <div className="role-card-icon">
                    <div className="icon-circle recruiter-icon">
                      <i className="fas fa-star"></i>
                    </div>
                  </div>
                  <div className="role-card-content">
                    <h4>New to CV Matcher?</h4>
                    <p>Create your account to get started</p>
                  </div>
                  <div className="role-card-arrow">→</div>
                </div>
              </div>
              
              <div className="welcome-actions">
                <button className="welcome-btn welcome-btn-primary" onClick={handleLogin}>
                  Sign In
                </button>
                <button className="welcome-btn welcome-btn-secondary" onClick={handleRegister}>
                  Sign Up
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WelcomePage; 