import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './EnhancedNavigation.css';

const EnhancedNavigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="enhanced-navigation">
      <div className="nav-container">
        <div className="nav-brand">
          <h2>🎯 Enhanced CV Matcher</h2>
        </div>
        
        <div className="nav-links">
          <div className="nav-section">
            <h4>👤 Candidate Features</h4>
            <button 
              className={`nav-link ${isActive('/enhanced-candidate-recommendations') ? 'active' : ''}`}
              onClick={() => navigate('/enhanced-candidate-recommendations')}
            >
              📄 CV Upload & Analysis
            </button>
            <button 
              className={`nav-link ${isActive('/candidate-recommendations') ? 'active' : ''}`}
              onClick={() => navigate('/candidate-recommendations')}
            >
              🎯 Profile Recommendations
            </button>
          </div>
          
          <div className="nav-section">
            <h4>🏢 Recruiter Features</h4>
            <button 
              className={`nav-link ${isActive('/enhanced-recruiter-recommendations') ? 'active' : ''}`}
              onClick={() => navigate('/enhanced-recruiter-recommendations')}
            >
              👥 Enhanced Candidate Search
            </button>
            <button 
              className={`nav-link ${isActive('/recruiter-recommendations') ? 'active' : ''}`}
              onClick={() => navigate('/recruiter-recommendations')}
            >
              🎯 Skill-Based Matching
            </button>
          </div>
          
          <div className="nav-section">
            <h4>📊 Analytics</h4>
            <button 
              className={`nav-link ${isActive('/interactions-analytics') ? 'active' : ''}`}
              onClick={() => navigate('/interactions-analytics')}
            >
              📈 Performance Analytics
            </button>
            <button 
              className={`nav-link ${isActive('/recommendations-engine') ? 'active' : ''}`}
              onClick={() => navigate('/recommendations-engine')}
            >
              ⚙️ Engine Settings
            </button>
          </div>
          
          <div className="nav-section">
            <h4>🔧 System</h4>
            <button 
              className={`nav-link ${isActive('/admin-dashboard') ? 'active' : ''}`}
              onClick={() => navigate('/admin-dashboard')}
            >
              🛠️ Admin Dashboard
            </button>
            <button 
              className={`nav-link ${isActive('/gdpr-management') ? 'active' : ''}`}
              onClick={() => navigate('/gdpr-management')}
            >
              🔒 GDPR Management
            </button>
          </div>
        </div>
        
        <div className="nav-footer">
          <button 
            className="nav-link"
            onClick={() => navigate('/')}
          >
            🏠 Back to Welcome
          </button>
        </div>
      </div>
    </nav>
  );
};

export default EnhancedNavigation; 