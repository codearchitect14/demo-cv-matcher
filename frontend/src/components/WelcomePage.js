import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './WelcomePage.css';

const WelcomePage = () => {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);

  React.useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleLogin = () => {
    navigate('/login-new');
  };

  const handleRegister = () => {
    navigate('/signup-new');
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
          <h1 className="welcome-title">Discover Your Dream Job here</h1>
          <p className="welcome-description">
            Explore all the existing job roles based on your interest and study major
          </p>
          
          <div className="welcome-buttons">
            <button className="btn-primary" onClick={handleLogin}>
              Login
            </button>
            <button className="btn-secondary" onClick={handleRegister}>
              Register
            </button>
          </div>
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