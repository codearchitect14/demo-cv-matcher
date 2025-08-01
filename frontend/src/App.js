import React, { useState, useEffect } from 'react';
import LoginNew from './components/LoginNew';
import SignUpNew from './components/SignUpNew';
import CandidatesDashboard from './components/CandidatesDashboard';
import JobsDashboard from './components/JobsDashboard';
import ApplicationsManagement from './components/ApplicationsManagement';
import RecommendationsEngine from './components/RecommendationsEngine';
import InteractionsAnalytics from './components/InteractionsAnalytics';
import { apiService } from './api';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showAuth, setShowAuth] = useState('welcome'); // 'welcome', 'signin' or 'signup'
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState(() => {
    // Get the active tab from localStorage or default to 'candidates'
    return localStorage.getItem('activeTab') || 'candidates';
  });

  // Save active tab to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('activeTab', activeTab);
  }, [activeTab]);

  // Initialize authentication on app load
  useEffect(() => {
    const initializeAuth = async () => {
      console.log('Initializing authentication...');
      apiService.initializeAuth();
      const token = apiService.getAuthToken();
      console.log('Token found:', !!token);
      
      if (token) {
        // Try to validate the token
        const user = await apiService.validateToken();
        console.log('Token validation result:', !!user);
        if (user) {
          setCurrentUser(user);
          setIsAuthenticated(true);
          console.log('User authenticated successfully');
        } else {
          // Token is invalid, clear it
          apiService.setToken(null);
          setIsAuthenticated(false);
          console.log('Token invalid, cleared');
        }
      } else {
        console.log('No token found');
      }
    };

    initializeAuth();
  }, []);

  const handleSignInSuccess = (response) => {
    // Set the token using the new function
    apiService.setToken(response.access_token);
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
    // Reset active tab to default
    setActiveTab('candidates');
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'candidates':
        return <CandidatesDashboard />;
      
      case 'jobs':
        return <JobsDashboard />;
      
      case 'applications':
        return <ApplicationsManagement />;
      
      case 'recommendations':
        return <RecommendationsEngine />;
      
      case 'interactions':
        return <InteractionsAnalytics />;
      
      default:
        return <CandidatesDashboard />;
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="app">
        {showAuth === 'welcome' && (
          <div className="welcome-container">
            <div className="welcome-content">
              <div className="welcome-header">
                <h1 className="welcome-title">JobMatcher</h1>
                <p className="welcome-subtitle">AI-Powered Job Matching Platform</p>
              </div>
              <div className="welcome-features">
                <div className="feature-item">
                  <div className="feature-icon">🎯</div>
                  <h3>Smart Matching</h3>
                  <p>AI-powered job-candidate matching</p>
                </div>
                <div className="feature-item">
                  <div className="feature-icon">📊</div>
                  <h3>Analytics</h3>
                  <p>Behavior patterns and insights</p>
                </div>
                <div className="feature-item">
                  <div className="feature-icon">⚡</div>
                  <h3>Fast & Efficient</h3>
                  <p>Quick recommendations and searches</p>
                </div>
              </div>
              <div className="welcome-actions">
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
        )}
        
        {showAuth === 'signin' && (
          <LoginNew 
            onSwitchToSignUp={() => setShowAuth('signup')}
            onSignInSuccess={handleSignInSuccess}
          />
        )}
        
        {showAuth === 'signup' && (
          <SignUpNew 
            onSwitchToSignIn={() => setShowAuth('signin')}
            onSignUpSuccess={() => setShowAuth('signin')}
          />
        )}
      </div>
    );
  }

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>JobMatcher</h1>
        </div>
        
        <div className="nav-links">
          <a 
            href="#" 
            className={activeTab === 'candidates' ? 'active' : ''}
            onClick={() => handleTabChange('candidates')}
          >
            Candidates
          </a>
          <a 
            href="#" 
            className={activeTab === 'jobs' ? 'active' : ''}
            onClick={() => handleTabChange('jobs')}
          >
            Jobs
          </a>
          <a 
            href="#" 
            className={activeTab === 'applications' ? 'active' : ''}
            onClick={() => handleTabChange('applications')}
          >
            Applications
          </a>
          <a 
            href="#" 
            className={activeTab === 'recommendations' ? 'active' : ''}
            onClick={() => handleTabChange('recommendations')}
          >
            Recommendations
          </a>
          <a 
            href="#" 
            className={activeTab === 'interactions' ? 'active' : ''}
            onClick={() => handleTabChange('interactions')}
          >
            Interactions
          </a>
        </div>
        
        <div className="nav-user">
          <span className="user-welcome">Welcome, {currentUser?.name || 'User'}!</span>
          <button className="btn-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>
      
      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
}

export default App; 