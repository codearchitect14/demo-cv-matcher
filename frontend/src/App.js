import React, { useState } from 'react';
import CandidateRegistration from './components/CandidateRegistration';
import ExperienceForm from './components/ExperienceForm';
import JobRecommendations from './components/JobRecommendations';
import JobPosting from './components/JobPosting';
import CandidateRecommendations from './components/CandidateRecommendations';
import AdminDashboard from './components/AdminDashboard';
import GDPRManagement from './components/GDPRManagement';

function App() {
  const [activeTab, setActiveTab] = useState('candidate');
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');

  const renderContent = () => {
    switch (activeTab) {
      case 'candidate':
        return (
          <div>
            <h2>Candidate Functions</h2>
            <div className="grid">
              <CandidateRegistration 
                onRegistrationSuccess={(candidate) => {
                  setSelectedCandidateId(candidate.id);
                  alert(`Candidate registered with ID: ${candidate.id}`);
                }}
              />
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

  return (
    <div>
      <nav className="nav">
        <a href="#" onClick={() => setActiveTab('candidate')}>Candidate</a>
        <a href="#" onClick={() => setActiveTab('employer')}>Employer</a>
        <a href="#" onClick={() => setActiveTab('admin')}>Admin Dashboard</a>
        <a href="#" onClick={() => setActiveTab('gdpr')}>GDPR Management</a>
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