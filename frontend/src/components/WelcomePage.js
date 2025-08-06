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
      <div className="welcome-background">
        {/* Decorative shapes */}
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>
      
      <div className="welcome-card">
        {/* Illustration */}
        <div className="illustration-container">
          <div className="illustration">
            <div className="person">
              <div className="head"></div>
              <div className="body"></div>
              <div className="arm"></div>
              <div className="cup"></div>
            </div>
            <div className="laptop"></div>
            <div className="plant">
              <div className="pot"></div>
              <div className="leaves">
                <div className="leaf leaf-1"></div>
                <div className="leaf leaf-2"></div>
                <div className="leaf leaf-3"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="welcome-content">
          <h1 className="welcome-title">Welcome to CV Matcher</h1>
          <p className="welcome-description">
            Connect talented candidates with amazing opportunities
          </p>
          
          {!selectedRole ? (
            <div className="role-selection">
              <h2>Choose your role:</h2>
              <div className="role-buttons">
                <button 
                  className="role-btn candidate-btn" 
                  onClick={() => handleRoleSelect('candidate')}
                >
                  <div className="role-icon">👤</div>
                  <div className="role-text">
                    <h3>I'm a Candidate</h3>
                    <p>Find your dream job</p>
                  </div>
                </button>
                <button 
                  className="role-btn recruiter-btn" 
                  onClick={() => handleRoleSelect('recruiter')}
                >
                  <div className="role-icon">🏢</div>
                  <div className="role-text">
                    <h3>I'm a Recruiter</h3>
                    <p>Post jobs and find talent</p>
                  </div>
                </button>
              </div>
            </div>
          ) : (
            <div className="auth-options">
              <h2>Welcome, {selectedRole === 'candidate' ? 'Candidate' : 'Recruiter'}!</h2>
              <div className="welcome-buttons">
                <button className="btn-primary" onClick={handleLogin}>
                  Login
                </button>
                <button className="btn-secondary" onClick={handleRegister}>
                  Register
                </button>
                <button className="btn-back" onClick={handleBack}>
                  ← Back
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Decorative magnifying glass */}
        <div className="magnifying-glass">
          <div className="glass-circle"></div>
          <div className="glass-handle"></div>
        </div>
      </div>
    </div>
  );
};

export default WelcomePage; 