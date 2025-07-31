import React, { useState, useEffect } from 'react';
import LoginNew from './components/LoginNew';
import SignUpNew from './components/SignUpNew';
import ExperienceForm from './components/ExperienceForm';
import JobRecommendations from './components/JobRecommendations';
import JobPosting from './components/JobPosting';
import CandidateRecommendations from './components/CandidateRecommendations';
import AdminDashboard from './components/AdminDashboard';
import GDPRManagement from './components/GDPRManagement';
import { apiService } from './api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showAuth, setShowAuth] = useState('welcome'); // 'welcome', 'signin' or 'signup'
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('candidate');
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');

  // Initialize authentication on app load
  useEffect(() => {
    apiService.initializeAuth();
    const token = apiService.getAuthToken();
    if (token) {
      setIsAuthenticated(true);
      // Try to get current user info
      apiService.getCurrentUser()
        .then(user => setCurrentUser(user))
        .catch(() => {
          // Token might be invalid, clear it
          apiService.logout();
          setIsAuthenticated(false);
        });
    }
  }, []);

  const handleSignInSuccess = (response) => {
    setIsAuthenticated(true);
    setShowAuth(null);
    // Get user info
    apiService.getCurrentUser()
      .then(user => setCurrentUser(user))
      .catch(console.error);
  };

  const handleLogout = async () => {
    await apiService.logout();
    setIsAuthenticated(false);
    setCurrentUser(null);
    setShowAuth('welcome');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'candidate':
        return (
          <div>
            <h2>Candidate Functions</h2>
            <div className="grid">
              <ExperienceForm 
                candidateId={selectedCandidateId}
                onExperienceAdded={() => alert('Experience added successfully!')}
              />
            </div>
            <JobRecommendations candidateId={selectedCandidateId} />
          </div>
        );
      
      case 'employer':
        return (
          <div>
            <h2>Employer Functions</h2>
            <div className="grid">
              <JobPosting 
                onJobPosted={(job) => {
                  setSelectedJobId(job.id);
                  alert(`Job posted with ID: ${job.id}`);
                }}
              />
              <CandidateRecommendations jobId={selectedJobId} />
            </div>
          </div>
        );
      
      case 'admin':
        return <AdminDashboard />;
      
      case 'gdpr':
        return <GDPRManagement />;
      
      default:
        return <div>Select a tab to get started</div>;
    }
  };

  // Show welcome page if not authenticated
  if (!isAuthenticated && showAuth === 'welcome') {
    return (
      <div className="welcome-container">
        <div className="welcome-background">
          <div className="shape shape-1"></div>
          <div className="shape shape-2"></div>
          <div className="shape shape-3"></div>
        </div>
        
        <div className="welcome-card">
          <div className="logo-container">
            <div className="logo">
              <div className="welcome-logo">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 14V2h12l5.59 5.59a2 2 0 0 1 0 2.82z"/>
                  <line x1="7" y1="7" x2="7.01" y2="7"/>
                </svg>
              </div>
              <h1 className="brand-name">JobMatcher</h1>
            </div>
          </div>
          
          <div className="welcome-content">
            <h2 className="welcome-title">Welcome to JobMatcher</h2>
            <p className="welcome-description">
              Find your dream job or discover the perfect candidate. 
              Start your journey with us today.
            </p>
            
            <div className="welcome-buttons">
              <button 
                className="btn-primary" 
                onClick={() => setShowAuth('signin')}
              >
                Sign In
              </button>
              <button 
                className="btn-secondary" 
                onClick={() => setShowAuth('signup')}
              >
                Create Account
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show authentication screens if not authenticated
  if (!isAuthenticated) {
    return (
      <div>
        <nav className="nav">
          <div className="nav-brand">
            <h1>JobMatcher</h1>
          </div>
        </nav>
        
        <div className="container">
          {showAuth === 'signin' && (
            <LoginNew 
              onSignInSuccess={handleSignInSuccess}
              onSwitchToSignUp={() => setShowAuth('signup')}
            />
          )}
          
          {showAuth === 'signup' && (
            <SignUpNew 
              onSwitchToSignIn={() => setShowAuth('signin')}
            />
          )}
        </div>
      </div>
    );
  }

  // Show main app if authenticated
  return (
    <div>
      <nav className="nav">
        <div className="nav-brand">
          <h1>JobMatcher</h1>
        </div>
        
        <div className="nav-links">
          <a href="#" onClick={() => setActiveTab('candidate')}>Candidate</a>
          <a href="#" onClick={() => setActiveTab('employer')}>Employer</a>
          <a href="#" onClick={() => setActiveTab('admin')}>Admin Dashboard</a>
          <a href="#" onClick={() => setActiveTab('gdpr')}>GDPR Management</a>
        </div>
        
        <div className="nav-user">
          {currentUser && (
            <span className="user-info">
              Welcome, {currentUser.name}!
            </span>
          )}
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </nav>

      <div className="container">
        {activeTab === 'candidate' && (
          <div style={{ marginBottom: '20px' }}>
            <div className="form-group">
              <label>Selected Candidate ID:</label>
              <input
                type="number"
                value={selectedCandidateId}
                onChange={(e) => setSelectedCandidateId(e.target.value)}
                placeholder="Enter candidate ID for testing"
                style={{ width: '200px' }}
              />
            </div>
          </div>
        )}

        {activeTab === 'employer' && (
          <div style={{ marginBottom: '20px' }}>
            <div className="form-group">
              <label>Selected Job ID:</label>
              <input
                type="number"
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
                placeholder="Enter job ID for testing"
                style={{ width: '200px' }}
              />
            </div>
          </div>
        )}

        {renderContent()}
      </div>
    </div>
  );
}

export default App; 