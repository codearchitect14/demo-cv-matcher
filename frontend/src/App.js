import React, { useState, useEffect } from 'react';
import SignIn from './components/SignIn';
import SignUp from './components/SignUp';
import ExperienceForm from './components/ExperienceForm';
import JobRecommendations from './components/JobRecommendations';
import JobPosting from './components/JobPosting';
import CandidateRecommendations from './components/CandidateRecommendations';
import AdminDashboard from './components/AdminDashboard';
import GDPRManagement from './components/GDPRManagement';
import { apiService } from './api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showAuth, setShowAuth] = useState('signin'); // 'signin' or 'signup'
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
    setShowAuth('signin');
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

  // Show authentication screens if not authenticated
  if (!isAuthenticated) {
    return (
      <div>
        <nav className="nav">
          <div className="nav-brand">
            <h1>Job Recommendation System</h1>
          </div>
        </nav>
        
        <div className="container">
          {showAuth === 'signin' && (
            <SignIn 
              onSignInSuccess={handleSignInSuccess}
              onSwitchToSignUp={() => setShowAuth('signup')}
            />
          )}
          
          {showAuth === 'signup' && (
            <SignUp 
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
          <h1>Job Recommendation System</h1>
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