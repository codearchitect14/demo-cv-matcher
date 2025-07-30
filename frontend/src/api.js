import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Service for all backend interactions
export const apiService = {
  // Authentication APIs
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.log('Logout request failed:', error);
    }
    // Clear local storage regardless of server response
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    api.defaults.headers.common['Authorization'] = null;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Token management
  setAuthToken: (token) => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  },

  getAuthToken: () => {
    return localStorage.getItem('access_token');
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },

  // Initialize auth token from localStorage
  initializeAuth: () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  },

  // Candidate APIs
  createCandidate: async (candidateData) => {
    const response = await api.post('/candidates', candidateData);
    return response.data;
  },

  getCandidate: async (candidateId) => {
    const response = await api.get(`/candidates/${candidateId}`);
    return response.data;
  },

  updateCandidate: async (candidateId, candidateData) => {
    const response = await api.put(`/candidates/${candidateId}`, candidateData);
    return response.data;
  },

  deleteCandidate: async (candidateId) => {
    const response = await api.delete(`/candidates/${candidateId}`);
    return response.data;
  },

  addExperience: async (candidateId, experienceData) => {
    const response = await api.post(`/candidates/${candidateId}/experience`, experienceData);
    return response.data;
  },

  updateExperience: async (candidateId, experienceId, experienceData) => {
    const response = await api.put(`/candidates/${candidateId}/experience/${experienceId}`, experienceData);
    return response.data;
  },

  deleteExperience: async (candidateId, experienceId) => {
    const response = await api.delete(`/candidates/${candidateId}/experience/${experienceId}`);
    return response.data;
  },

  getCandidateApplications: async (candidateId) => {
    const response = await api.get(`/candidates/${candidateId}/applications`);
    return response.data;
  },

  getCandidateInteractions: async (candidateId) => {
    const response = await api.get(`/candidates/${candidateId}/interactions`);
    return response.data;
  },

  // Job APIs
  createJob: async (jobData) => {
    const response = await api.post('/jobs', jobData);
    return response.data;
  },

  getJob: async (jobId) => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },

  updateJob: async (jobId, jobData) => {
    const response = await api.put(`/jobs/${jobId}`, jobData);
    return response.data;
  },

  deleteJob: async (jobId) => {
    const response = await api.delete(`/jobs/${jobId}`);
    return response.data;
  },

  getJobs: async (filters = {}) => {
    const response = await api.get('/jobs', { params: filters });
    return response.data;
  },

  addMandatorySkill: async (jobId, skillData) => {
    const response = await api.post(`/jobs/${jobId}/mandatory-skills`, skillData);
    return response.data;
  },

  getJobApplications: async (jobId) => {
    const response = await api.get(`/jobs/${jobId}/applications`);
    return response.data;
  },

  // Application APIs
  applyForJob: async (applicationData) => {
    const response = await api.post('/applications', applicationData);
    return response.data;
  },

  getApplication: async (applicationId) => {
    const response = await api.get(`/applications/${applicationId}`);
    return response.data;
  },

  updateApplicationStatus: async (applicationId, status) => {
    const response = await api.put(`/applications/${applicationId}/status`, { status });
    return response.data;
  },

  // Recommendation APIs
  getJobRecommendations: async (candidateId, useMlRanking = true) => {
    const response = await api.get(`/candidates/${candidateId}/job-recommendations`, {
      params: { use_ml_ranking: useMlRanking }
    });
    return response.data;
  },

  getCandidateRecommendations: async (jobId, useMlRanking = true) => {
    const response = await api.get(`/jobs/${jobId}/candidate-recommendations`, {
      params: { use_ml_ranking: useMlRanking }
    });
    return response.data;
  },

  searchJobs: async (searchData) => {
    const response = await api.post('/search/jobs', searchData);
    return response.data;
  },

  searchCandidates: async (searchData) => {
    const response = await api.post('/search/candidates', searchData);
    return response.data;
  },

  // Interaction APIs
  logInteraction: async (interactionData) => {
    const response = await api.post('/interactions/log-interaction', interactionData);
    return response.data;
  },

  getBehaviorPatterns: async (candidateId) => {
    const response = await api.get(`/interactions/candidates/${candidateId}/behavior-patterns`);
    return response.data;
  },

  getSimilarUsers: async (candidateId) => {
    const response = await api.get(`/interactions/candidates/${candidateId}/similar-users`);
    return response.data;
  },

  // Analytics APIs
  getJobsWithoutApplicants: async () => {
    const response = await api.get('/analytics/jobs-without-applicants');
    return response.data;
  },

  getCandidatesZeroVisibility: async () => {
    const response = await api.get('/analytics/candidates-zero-visibility');
    return response.data;
  },

  getSkillGapAnalysis: async () => {
    const response = await api.get('/analytics/skill-gap-analysis');
    return response.data;
  },

  getApplicationStats: async () => {
    const response = await api.get('/analytics/application-stats');
    return response.data;
  },

  getJobPerformance: async () => {
    const response = await api.get('/analytics/job-performance');
    return response.data;
  },

  // System APIs
  generateEmbeddings: async () => {
    const response = await api.post('/system/embeddings/generate');
    return response.data;
  },

  retrainModels: async () => {
    const response = await api.post('/system/models/retrain');
    return response.data;
  },

  getSystemHealth: async () => {
    const response = await api.get('/system/health');
    return response.data;
  },

  getSystemStats: async () => {
    const response = await api.get('/system/stats');
    return response.data;
  },

  // GDPR APIs
  updateConsent: async (candidateId, consentData) => {
    const response = await api.put(`/gdpr/update_consent/${candidateId}`, consentData);
    return response.data;
  },

  deleteUserData: async (candidateId, deletionData) => {
    const response = await api.delete(`/gdpr/delete_user_data/${candidateId}`, {
      data: deletionData
    });
    return response.data;
  },

  getAuditLogs: async (candidateId) => {
    const response = await api.get(`/gdpr/audit_logs/${candidateId}`);
    return response.data;
  },

  exportUserData: async (candidateId) => {
    const response = await api.get(`/gdpr/export_user_data/${candidateId}`);
    return response.data;
  },

  getConsentStatus: async (candidateId) => {
    const response = await api.get(`/gdpr/consent_status/${candidateId}`);
    return response.data;
  }
};

export default apiService; 