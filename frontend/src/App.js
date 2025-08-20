import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import WelcomePage from './components/WelcomePage';
import SignUpNew from './components/SignUpNew';
import LoginNew from './components/LoginNew';
import CandidatesDashboard from './components/CandidatesDashboard';
import JobsDashboard from './components/JobsDashboard';
import JobSearch from './components/JobSearch';
import JobRecommendations from './components/JobRecommendations';
import CandidateSearch from './components/CandidateSearch';
import ApplicationsManagement from './components/ApplicationsManagement';
import InteractionsAnalytics from './components/InteractionsAnalytics';
import AdminDashboard from './components/AdminDashboard';
import RecommendationsEngine from './components/RecommendationsEngine';
import GDPRManagement from './components/GDPRManagement';
import RecruiterLogin from './components/RecruiterLogin';
import RecruiterRegistration from './components/RecruiterRegistration';
import RecruiterDashboard from './components/RecruiterDashboard';
import CandidateRecommendations from './components/CandidateRecommendations';
import RecruiterRecommendations from './components/RecruiterRecommendations';
import EnhancedCandidateRecommendations from './components/EnhancedCandidateRecommendations';
import EnhancedRecruiterRecommendations from './components/EnhancedRecruiterRecommendations';
import EnhancedTestPage from './components/EnhancedTestPage';
import Navigation from './components/Navigation';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          {/* Welcome and Auth Routes */}
          <Route path="/" element={<WelcomePage />} />
          <Route path="/signup-new" element={<SignUpNew />} />
          <Route path="/login" element={<LoginNew />} />
          <Route path="/login-new" element={<LoginNew />} />
          
          {/* Enhanced Test Page */}
          <Route path="/enhanced-test" element={<EnhancedTestPage />} />
          
          {/* Candidate Routes */}
          <Route path="/candidates-dashboard" element={<CandidatesDashboard />} />
          <Route path="/job-search" element={<JobSearch />} />
          <Route path="/job-recommendations" element={<JobRecommendations />} />
          <Route path="/candidate-recommendations" element={<CandidateRecommendations />} />
          <Route path="/enhanced-candidate-recommendations" element={<EnhancedCandidateRecommendations />} />
          
          {/* Recruiter Routes */}
          <Route path="/recruiter/login" element={<RecruiterLogin />} />
          <Route path="/recruiter/register" element={<RecruiterRegistration />} />
          <Route path="/recruiter/dashboard" element={<RecruiterDashboard />} />
          <Route path="/recruiter-recommendations" element={<RecruiterRecommendations />} />
          <Route path="/enhanced-recruiter-recommendations" element={<EnhancedRecruiterRecommendations />} />
          
          {/* Admin Routes */}
          <Route path="/jobs-dashboard" element={<JobsDashboard />} />
          <Route path="/candidate-search" element={<CandidateSearch />} />
          <Route path="/applications-management" element={<ApplicationsManagement />} />
          <Route path="/interactions-analytics" element={<InteractionsAnalytics />} />
          <Route path="/admin-dashboard" element={<AdminDashboard />} />
          <Route path="/recommendations-engine" element={<RecommendationsEngine />} />
          <Route path="/gdpr-management" element={<GDPRManagement />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App; 