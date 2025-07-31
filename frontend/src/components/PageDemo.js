import React from 'react';
import { Link } from 'react-router-dom';
import './PageDemo.css';

const PageDemo = () => {
  return (
    <div className="demo-container">
      <div className="demo-header">
        <h1>🎨 Frontend Pages Demo</h1>
        <p>Choose a page to view the different authentication designs</p>
      </div>
      
      <div className="demo-grid">
        <div className="demo-card">
          <h3>🌟 New Modern Pages</h3>
          <div className="demo-links">
            <Link to="/welcome" className="demo-link">
              🏠 Welcome Page
            </Link>
            <Link to="/login-new" className="demo-link">
              🔐 Modern Login
            </Link>
            <Link to="/signup-new" className="demo-link">
              ✨ Modern Signup
            </Link>
          </div>
          <p className="demo-description">
            Beautiful modern design with animations, floating labels, and social login
          </p>
        </div>
        
        <div className="demo-card">
          <h3>📱 Original Pages (Backup)</h3>
          <div className="demo-links">
            <Link to="/login-old" className="demo-link">
              🔐 Original Login
            </Link>
            <Link to="/signup-old" className="demo-link">
              ✨ Original Signup
            </Link>
          </div>
          <p className="demo-description">
            Your existing authentication pages with glassmorphism design
          </p>
        </div>
        
        <div className="demo-card">
          <h3>🚀 Features</h3>
          <div className="demo-features">
            <div className="feature">
              <span className="feature-icon">🎨</span>
              <span>Modern UI/UX Design</span>
            </div>
            <div className="feature">
              <span className="feature-icon">✨</span>
              <span>Smooth Animations</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🔐</span>
              <span>Social Login Options</span>
            </div>
            <div className="feature">
              <span className="feature-icon">📱</span>
              <span>Responsive Design</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🎯</span>
              <span>Floating Labels</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🔒</span>
              <span>Password Toggle</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="demo-footer">
        <p>Both sets of pages are fully functional and ready to use!</p>
        <Link to="/welcome" className="demo-cta">
          🚀 Start with Welcome Page
        </Link>
      </div>
    </div>
  );
};

export default PageDemo; 