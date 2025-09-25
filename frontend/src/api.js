import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Export the api instance
export default api;

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
    const response = await api.get('/candidates/me');
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
    const token = localStorage.getItem('access_token');
    console.log('Checking authentication, token exists:', !!token);
    return !!token;
  },

  // Initialize auth token from localStorage
  initializeAuth: () => {
    const token = localStorage.getItem('access_token');
    console.log('Initializing auth with token:', token ? 'Token exists' : 'No token');
    console.log('Token value:', token);
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      console.log('Authorization header set to:', api.defaults.headers.common['Authorization']);
    }
  },

  // Validate token by making a request to /me endpoint
  validateToken: async () => {
    try {
      console.log('Validating token...');
      console.log('Current Authorization header:', api.defaults.headers.common['Authorization']);
      const response = await api.get('/candidates/me');
      console.log('Token validation successful:', response.data);
      return response.data;
    } catch (error) {
      console.log('Token validation failed:', error);
      console.log('Error response:', error.response?.data);
      console.log('Error status:', error.response?.status);
      return null;
    }
  },

  // Set token and update axios headers
  setToken: (token) => {
    if (token) {
      localStorage.setItem('access_token', token);
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      localStorage.removeItem('access_token');
      delete api.defaults.headers.common['Authorization'];
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

  logJobView: async (candidateId, jobId) => {
    const response = await api.get(`/jobs/${jobId}`, {
      params: { candidate_id: candidateId }
    });
    return response.data;
  },

  // Application APIs
  createApplication: async (applicationData) => {
    try {
      console.log('API Service - Application data before sending:', JSON.stringify(applicationData, null, 2));
      
      // Create explicit data object with uppercase status
      const explicitData = {
        job_id: applicationData.job_id,
        candidate_id: applicationData.candidate_id,
        status: 'APPLIED'  // Explicitly set to uppercase
      };
      
      console.log('API Service - Explicit data being sent:', JSON.stringify(explicitData, null, 2));
      
      // Use public endpoint that doesn't require authentication
      const response = await api.post('/applications/public', explicitData);
      return response.data;
    } catch (error) {
      console.error('Error creating application:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw error;
    }
  },

  getApplications: async (filters = {}) => {
    // Auto-add recruiter filter ONLY if logged in as regular recruiter (not admin)
    const recruiterUser = localStorage.getItem('recruiterUser');
    if (recruiterUser) {
      const recruiterData = JSON.parse(recruiterUser);
      // Only filter if user is a regular recruiter (not admin)
      if (recruiterData.role === 'recruiter') {
        filters.recruiter_id = recruiterData.id;
      }
    }
    
    const response = await api.get('/applications-public/public-fast', { params: filters });
    return response.data;
  },

  getApplication: async (applicationId) => {
    const response = await api.get(`/applications/${applicationId}`);
    return response.data;
  },

  updateApplication: async (applicationId, updateData) => {
    const response = await api.put(`/applications/${applicationId}`, updateData);
    return response.data;
  },

  deleteApplication: async (applicationId) => {
    const response = await api.delete(`/applications/${applicationId}`);
    return response.data;
  },

  updateApplicationStatus: async (applicationId, status) => {
    const response = await api.put(`/applications/${applicationId}/status`, { status });
    return response.data;
  },

  // Recommendation APIs
  getJobRecommendations: async (limit = 10) => {
    try {
      const response = await api.get('/recommendations/jobs', {
        params: { limit },
        timeout: 35000 // 35 second timeout (longer than backend 30s limit)
      });
      return response.data;
    } catch (error) {
      console.error('Error getting job recommendations:', error);
      
      // Handle specific error cases
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        console.log('Request timed out, returning empty recommendations');
        return [];
      }
      
      if (error.response?.status === 504) {
        console.log('Gateway timeout (504), returning empty recommendations');
        return [];
      }
      
      if (error.response?.status === 500) {
        console.log('Server error (500), returning empty recommendations');
        return [];
      }
      
      // For other errors, re-throw to be handled by the component
      throw error;
    }
  },

  getCandidateRecommendations: async (jobId, useMlRanking = true) => {
    const response = await api.get(`/jobs/${jobId}/candidate-recommendations`, {
      params: { use_ml_ranking: useMlRanking }
    });
    return response.data;
  },

  // New Advanced Recommendation APIs
  getCandidateJobRecommendations: async (data) => {
    const response = await api.post('/recommendations/candidate/jobs', data);
    return response.data;
  },

  getRecruiterCandidateRecommendations: async (data) => {
    const response = await api.post('/recommendations/recruiter/candidates', data);
    return response.data;
  },

  uploadCvAndGetRecommendations: async (formData) => {
    const response = await api.post('/recommendations/cv/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  submitFeedback: async (data) => {
    const response = await api.post('/recommendations/feedback', data);
    return response.data;
  },

  getFeedbackInsights: async (params = {}) => {
    const response = await api.get('/recommendations/feedback/insights', { params });
    return response.data;
  },

  getModelPerformance: async () => {
    const response = await api.get('/recommendations/model/performance');
    return response.data;
  },

  predictFeedbackProbability: async (data) => {
    const response = await api.post('/recommendations/predict/feedback', data);
    return response.data;
  },

  quickCandidateMatch: async (data) => {
    const response = await api.post('/recommendations/candidate/quick-match', data);
    return response.data;
  },

  quickRecruiterMatch: async (data) => {
    const response = await api.post('/recommendations/recruiter/quick-match', data);
    return response.data;
  },

  searchJobs: async (searchData) => {
    // Use candidate unified recommendations with filtering and unified scoring
    try {
      let params = {};
      if (typeof searchData === 'string') {
        params = { title: searchData, limit: 10 };
      } else if (searchData && typeof searchData === 'object') {
        const { query, location, limit } = searchData;
        params = {
          title: query,
          location: location,
          limit: limit || 10
        };
        Object.keys(params).forEach(key => params[key] === undefined && delete params[key]);
      }
      const response = await api.get('/recommendations/candidate/jobs', { params, timeout: 35000 });
      const jobs = response.data || [];
      return jobs.map(j => ({
        job_id: j.job_id || j.id,
        title: j.title || 'Untitled Position',
        company: j.company || 'Unknown Company',
        location: j.location || 'Remote',
        salary_min: j.salary_min,
        salary_max: j.salary_max,
        domain: j.domain || 'General',
        match_score: typeof j.match_score === 'number' ? j.match_score : 0,
        explanation: j.explanation || {},
        is_valid: true,
        validation_reasons: []
      }));
    } catch (error) {
      console.error('Unified job search failed:', error);
      return [];
    }
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
  },

  // Enhanced Recommendation APIs
  async getEnhancedCandidateJobRecommendations(request) {
    try {
      const response = await fetch(`${this.baseURL}/recommendations/candidate/jobs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getToken()}`
        },
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting enhanced candidate recommendations:', error);
      throw error;
    }
  },

  async getEnhancedRecruiterCandidateRecommendations(request) {
    try {
      const response = await fetch(`${this.baseURL}/recommendations/recruiter/candidates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getToken()}`
        },
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting enhanced recruiter recommendations:', error);
      throw error;
    }
  },

  async uploadCvAndGetEnhancedRecommendations(candidateId, cvFile) {
    try {
      const formData = new FormData();
      formData.append('cv_file', cvFile);
      formData.append('candidate_id', candidateId);

      const response = await fetch(`${this.baseURL}/recommendations/cv/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.getToken()}`
        },
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error uploading CV and getting recommendations:', error);
      throw error;
    }
  },

  async createJobWithSkillRequirements(jobData, skillRequirements) {
    try {
      const response = await fetch(`${this.baseURL}/recommendations/job/create-with-skills`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getToken()}`
        },
        body: JSON.stringify({
          job_data: jobData,
          skill_requirements: skillRequirements
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating job with skill requirements:', error);
      throw error;
    }
  },

  // Enhanced Skill Matching APIs
  async getSkillMatches(query, threshold = 0.3) {
    try {
      const response = await fetch(`${this.baseURL}/skills/matches?query=${encodeURIComponent(query)}&threshold=${threshold}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getToken()}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting skill matches:', error);
      throw error;
    }
  },

  async validateSkillRequirements(jobSkills, candidateSkills) {
    try {
      const response = await fetch(`${this.baseURL}/skills/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getToken()}`
        },
        body: JSON.stringify({
          job_skills: jobSkills,
          candidate_skills: candidateSkills
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error validating skill requirements:', error);
      throw error;
    }
  },

  // Enhanced Feedback APIs
  async submitEnhancedFeedback(feedbackData) {
    try {
      const response = await fetch(`${this.baseURL}/recommendations/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getToken()}`
        },
        body: JSON.stringify(feedbackData)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error submitting enhanced feedback:', error);
      throw error;
    }
  },

  async getEnhancedFeedbackInsights(userId = null, userType = null, days = 30) {
    try {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      if (userType) params.append('user_type', userType);
      params.append('days', days);

      const response = await fetch(`${this.baseURL}/recommendations/feedback/insights?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getToken()}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting enhanced feedback insights:', error);
      throw error;
    }
  },

  async getEnhancedModelPerformance() {
    try {
      const response = await fetch(`${this.baseURL}/recommendations/model/performance`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getToken()}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting enhanced model performance:', error);
      throw error;
    }
  }
}; 