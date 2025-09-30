import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { apiService } from './api';
import WelcomePage from './components/WelcomePage';
import SignUpNew from './components/SignUpNew';
import LoginNew from './components/LoginNew';
import CandidatesDashboard from './components/CandidatesDashboard';
import JobsDashboard from './components/JobsDashboard';
import JobSearch from './components/JobSearch';
import MyApplications from './components/MyApplications';
import JobRecommendations from './components/JobRecommendations';
import CandidateSearch from './components/CandidateSearch';
import ApplicationsManagement from './components/ApplicationsManagement';
import RecruiterApplications from './components/RecruiterApplications';
import InteractionsAnalytics from './components/InteractionsAnalytics';
import AdminDashboard from './components/AdminDashboard';
import RecommendationsEngine from './components/RecommendationsEngine';
import GDPRManagement from './components/GDPRManagement';
import RecruiterLogin from './components/RecruiterLogin';
import AdminLogin from './components/AdminLogin';
import RecruiterRegistration from './components/RecruiterRegistration';
import RecruiterDashboard from './components/RecruiterDashboard';
import CandidateRecommendations from './components/CandidateRecommendations';
import RecruiterRecommendations from './components/RecruiterRecommendations';
import EnhancedCandidateRecommendations from './components/EnhancedCandidateRecommendations';
import EnhancedRecruiterRecommendations from './components/EnhancedRecruiterRecommendations';
import EnhancedTestPage from './components/EnhancedTestPage';
import CompanyAdminDashboard from './components/CompanyAdminDashboard';
import CompanyManagement from './components/CompanyManagement';
import RecruiterAdmin from './components/RecruiterAdmin';
import JobAssignments from './components/JobAssignments';
import CandidateAssessment from './components/CandidateAssessment';
import AssessmentAnalytics from './components/AssessmentAnalytics';
import SubRecruiterDashboard from './components/SubRecruiterDashboard';
import SuperAdminLogin from './components/SuperAdminLogin';
import SuperAdminDashboard from './components/SuperAdminDashboard';
import Unauthorized from './components/Unauthorized';
// import Navigation from './components/Navigation';
import './App.css';

function App() {
  // Initialize authentication on app load
  useEffect(() => {
    apiService.initializeAuth();
  }, []);

  return (
    <Router>
      <div className="app">
        {/* <Navigation /> */}
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
          <Route path="/my-applications" element={<MyApplications />} />
          <Route path="/job-search" element={<JobSearch />} />
          <Route path="/assessment/:applicationId" element={<CandidateAssessment />} />
          <Route path="/job-recommendations" element={<JobRecommendations />} />
          <Route path="/candidate-recommendations" element={<CandidateRecommendations />} />
          <Route path="/enhanced-candidate-recommendations" element={<EnhancedCandidateRecommendations />} />
          
          {/* Recruiter Routes */}
          <Route path="/recruiter/login" element={<RecruiterLogin />} />
          <Route path="/recruiter/register" element={<RecruiterRegistration />} />
          <Route path="/recruiter/dashboard" element={<RecruiterDashboard />} />
          <Route path="/recruiter/applications" element={<RecruiterApplications />} />
          <Route path="/recruiter-recommendations" element={<RecruiterRecommendations />} />
          <Route path="/enhanced-recruiter-recommendations" element={<EnhancedRecruiterRecommendations />} />
          
          {/* Admin Routes */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/jobs-dashboard" element={<JobsDashboard />} />
          <Route path="/candidate-search" element={<CandidateSearch />} />
          <Route path="/applications-management" element={<ApplicationsManagement />} />
          <Route path="/interactions-analytics" element={<InteractionsAnalytics />} />
          <Route path="/admin-dashboard" element={<AdminDashboard />} />
          <Route path="/recommendations-engine" element={<RecommendationsEngine />} />
          <Route path="/gdpr-management" element={<GDPRManagement />} />
          
          {/* Company Management Routes */}
            <Route path="/company-admin" element={<CompanyAdminDashboard />} />
            <Route path="/company-management" element={<CompanyManagement />} />
            <Route path="/recruiter-admin" element={<RecruiterAdmin />} />
            <Route path="/job-assignments" element={<JobAssignments />} />
            <Route path="/assessment-analytics" element={<AssessmentAnalytics />} />
            <Route path="/sub-recruiter/dashboard" element={<SubRecruiterDashboard />} />
        <Route path="/super-admin-login" element={<SuperAdminLogin />} />
        <Route path="/super-admin-dashboard" element={<SuperAdminDashboard />} />
            <Route path="/unauthorized" element={<Unauthorized />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App; 