import React, { useState, useEffect } from 'react';
import './RecommendationsEngine.css';

const RecommendationsEngine = () => {
  const [jobRecommendations, setJobRecommendations] = useState([]);
  const [candidateRecommendations, setCandidateRecommendations] = useState([]);
  const [jobSearchResults, setJobSearchResults] = useState([]);
  const [candidateSearchResults, setCandidateSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('job-recommendations');
  
  // Job recommendations state
  const [jobRecParams, setJobRecParams] = useState({
    candidate_id: '',
    limit: 10,
    apply_filters: true,
    strict_mode: false,
    use_ml_ranking: true
  });

  // Candidate recommendations state
  const [candidateRecParams, setCandidateRecParams] = useState({
    job_id: '',
    limit: 10,
    apply_filters: true,
    strict_mode: false,
    use_ml_ranking: true
  });

  // Search state
  const [jobSearchQuery, setJobSearchQuery] = useState({
    query: '',
    limit: 10,
    apply_filters: true,
    strict_mode: false,
    use_ml_ranking: true
  });

  const [candidateSearchQuery, setCandidateSearchQuery] = useState({
    query: '',
    limit: 10,
    apply_filters: true,
    strict_mode: false,
    use_ml_ranking: true
  });

  const fetchJobRecommendations = async () => {
    if (!jobRecParams.candidate_id) {
      setError('Please enter a candidate ID');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const queryParams = new URLSearchParams({
        limit: jobRecParams.limit,
        apply_filters: jobRecParams.apply_filters,
        strict_mode: jobRecParams.strict_mode,
        use_ml_ranking: jobRecParams.use_ml_ranking
      });

      const response = await fetch(`http://localhost:8000/api/v1/recommendations/candidates/${jobRecParams.candidate_id}/job-recommendations?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setJobRecommendations(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch job recommendations: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const fetchCandidateRecommendations = async () => {
    if (!candidateRecParams.job_id) {
      setError('Please enter a job ID');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const queryParams = new URLSearchParams({
        limit: candidateRecParams.limit,
        apply_filters: candidateRecParams.apply_filters,
        strict_mode: candidateRecParams.strict_mode,
        use_ml_ranking: candidateRecParams.use_ml_ranking
      });

      const response = await fetch(`http://localhost:8000/api/v1/recommendations/jobs/${candidateRecParams.job_id}/candidate-recommendations?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCandidateRecommendations(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to fetch candidate recommendations: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const searchJobs = async () => {
    if (!jobSearchQuery.query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/recommendations/search/jobs', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(jobSearchQuery)
      });
      
      if (response.ok) {
        const data = await response.json();
        setJobSearchResults(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to search jobs: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const searchCandidates = async () => {
    if (!candidateSearchQuery.query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/recommendations/search/candidates', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(candidateSearchQuery)
      });
      
      if (response.ok) {
        const data = await response.json();
        setCandidateSearchResults(data);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        setError(`Failed to search candidates: ${errorMessage}`);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="recommendations-engine">
      <div className="dashboard-header">
        <h1>Recommendations Engine</h1>
      </div>

      {error && (
        <div className="error-message">
          <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'job-recommendations' ? 'active' : ''}`}
          onClick={() => setActiveTab('job-recommendations')}
        >
          Job Recommendations
        </button>
        <button 
          className={`tab ${activeTab === 'candidate-recommendations' ? 'active' : ''}`}
          onClick={() => setActiveTab('candidate-recommendations')}
        >
          Candidate Recommendations
        </button>
        <button 
          className={`tab ${activeTab === 'job-search' ? 'active' : ''}`}
          onClick={() => setActiveTab('job-search')}
        >
          Job Search
        </button>
        <button 
          className={`tab ${activeTab === 'candidate-search' ? 'active' : ''}`}
          onClick={() => setActiveTab('candidate-search')}
        >
          Candidate Search
        </button>
      </div>

      <div className="content-area">
        {activeTab === 'job-recommendations' && (
          <div className="recommendations-section">
            <h2>Job Recommendations for Candidate</h2>
            <div className="params-section">
              <div className="param-group">
                <label>Candidate ID:</label>
                <input
                  type="number"
                  value={jobRecParams.candidate_id}
                  onChange={(e) => setJobRecParams({...jobRecParams, candidate_id: e.target.value})}
                  placeholder="Enter candidate ID"
                />
              </div>
              <div className="param-group">
                <label>Limit:</label>
                <select
                  value={jobRecParams.limit}
                  onChange={(e) => setJobRecParams({...jobRecParams, limit: parseInt(e.target.value)})}
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>
              <div className="param-group">
                <label>
                  <input
                    type="checkbox"
                    checked={jobRecParams.apply_filters}
                    onChange={(e) => setJobRecParams({...jobRecParams, apply_filters: e.target.checked})}
                  />
                  Apply Filters
                </label>
              </div>
              <div className="param-group">
                <label>
                  <input
                    type="checkbox"
                    checked={jobRecParams.strict_mode}
                    onChange={(e) => setJobRecParams({...jobRecParams, strict_mode: e.target.checked})}
                  />
                  Strict Mode
                </label>
              </div>
              <div className="param-group">
                <label>
                  <input
                    type="checkbox"
                    checked={jobRecParams.use_ml_ranking}
                    onChange={(e) => setJobRecParams({...jobRecParams, use_ml_ranking: e.target.checked})}
                  />
                  Use ML Ranking
                </label>
              </div>
              <button 
                className="btn-primary"
                onClick={fetchJobRecommendations}
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Get Job Recommendations'}
              </button>
            </div>

            <div className="results-section">
              <h3>Results ({jobRecommendations.length})</h3>
              {jobRecommendations.length > 0 ? (
                <div className="recommendations-grid">
                  {jobRecommendations.map((recommendation, index) => (
                    <div key={recommendation.job_id || index} className="recommendation-card">
                      <div className="recommendation-header">
                        <h4>{recommendation.job?.title || 'N/A'}</h4>
                        <span className="score">Score: {recommendation.final_score?.toFixed(3) || 'N/A'}</span>
                      </div>
                      <p><strong>Company:</strong> {recommendation.job?.company || 'N/A'}</p>
                      <p><strong>Location:</strong> {recommendation.job?.location || 'N/A'}</p>
                      <p><strong>Domain:</strong> {recommendation.job?.domain || 'N/A'}</p>
                      <p><strong>Salary:</strong> ${recommendation.job?.salary_min || 0} - ${recommendation.job?.salary_max || 0}</p>
                      <p><strong>Experience:</strong> {recommendation.job?.total_years_required || 0} years</p>
                      <p><strong>Similarity:</strong> {(recommendation.similarity_score * 100).toFixed(1)}%</p>
                      {recommendation.personalization_reasons && recommendation.personalization_reasons.length > 0 && (
                        <div className="personalization-reasons">
                          <strong>Personalization:</strong>
                          <ul>
                            {recommendation.personalization_reasons.map((reason, idx) => (
                              <li key={idx}>{reason}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-results">No job recommendations found</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'candidate-recommendations' && (
          <div className="recommendations-section">
            <h2>Candidate Recommendations for Job</h2>
            <div className="params-section">
              <div className="param-group">
                <label>Job ID:</label>
                <input
                  type="number"
                  value={candidateRecParams.job_id}
                  onChange={(e) => setCandidateRecParams({...candidateRecParams, job_id: e.target.value})}
                  placeholder="Enter job ID"
                />
              </div>
              <div className="param-group">
                <label>Limit:</label>
                <select
                  value={candidateRecParams.limit}
                  onChange={(e) => setCandidateRecParams({...candidateRecParams, limit: parseInt(e.target.value)})}
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>
              <div className="param-group">
                <label>
                  <input
                    type="checkbox"
                    checked={candidateRecParams.apply_filters}
                    onChange={(e) => setCandidateRecParams({...candidateRecParams, apply_filters: e.target.checked})}
                  />
                  Apply Filters
                </label>
              </div>
              <div className="param-group">
                <label>
                  <input
                    type="checkbox"
                    checked={candidateRecParams.strict_mode}
                    onChange={(e) => setCandidateRecParams({...candidateRecParams, strict_mode: e.target.checked})}
                  />
                  Strict Mode
                </label>
              </div>
              <div className="param-group">
                <label>
                  <input
                    type="checkbox"
                    checked={candidateRecParams.use_ml_ranking}
                    onChange={(e) => setCandidateRecParams({...candidateRecParams, use_ml_ranking: e.target.checked})}
                  />
                  Use ML Ranking
                </label>
              </div>
              <button 
                className="btn-primary"
                onClick={fetchCandidateRecommendations}
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Get Candidate Recommendations'}
              </button>
            </div>

            <div className="results-section">
              <h3>Results ({candidateRecommendations.length})</h3>
              {candidateRecommendations.length > 0 ? (
                <div className="recommendations-grid">
                  {candidateRecommendations.map((recommendation, index) => (
                    <div key={recommendation.candidate_id || index} className="recommendation-card">
                      <div className="recommendation-header">
                        <h4>{recommendation.candidate?.name || 'N/A'}</h4>
                        <span className="score">Score: {recommendation.final_score?.toFixed(3) || 'N/A'}</span>
                      </div>
                      <p><strong>Email:</strong> {recommendation.candidate?.email || 'N/A'}</p>
                      <p><strong>Location:</strong> {recommendation.candidate?.location || 'N/A'}</p>
                      <p><strong>Domain:</strong> {recommendation.candidate?.domain || 'N/A'}</p>
                      <p><strong>Expected Salary:</strong> ${recommendation.candidate?.expected_salary_min || 0} - ${recommendation.candidate?.expected_salary_max || 0}</p>
                      <p><strong>Summary:</strong> {recommendation.candidate?.summary?.substring(0, 100) || 'N/A'}...</p>
                      <p><strong>Similarity:</strong> {(recommendation.similarity_score * 100).toFixed(1)}%</p>
                      {recommendation.personalization_reasons && recommendation.personalization_reasons.length > 0 && (
                        <div className="personalization-reasons">
                          <strong>Personalization:</strong>
                          <ul>
                            {recommendation.personalization_reasons.map((reason, idx) => (
                              <li key={idx}>{reason}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-results">No candidate recommendations found</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'job-search' && (
          <div className="search-section">
            <h2>Semantic Job Search</h2>
            <div className="search-form">
              <div className="search-input-group">
                <label>Search Query:</label>
                <input
                  type="text"
                  value={jobSearchQuery.query}
                  onChange={(e) => setJobSearchQuery({...jobSearchQuery, query: e.target.value})}
                  placeholder="Enter job search query (e.g., 'Python developer remote')"
                />
              </div>
              <div className="search-params">
                <div className="param-group">
                  <label>Limit:</label>
                  <select
                    value={jobSearchQuery.limit}
                    onChange={(e) => setJobSearchQuery({...jobSearchQuery, limit: parseInt(e.target.value)})}
                  >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                </div>
                <div className="param-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={jobSearchQuery.apply_filters}
                      onChange={(e) => setJobSearchQuery({...jobSearchQuery, apply_filters: e.target.checked})}
                    />
                    Apply Filters
                  </label>
                </div>
                <div className="param-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={jobSearchQuery.strict_mode}
                      onChange={(e) => setJobSearchQuery({...jobSearchQuery, strict_mode: e.target.checked})}
                    />
                    Strict Mode
                  </label>
                </div>
                <div className="param-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={jobSearchQuery.use_ml_ranking}
                      onChange={(e) => setJobSearchQuery({...jobSearchQuery, use_ml_ranking: e.target.checked})}
                    />
                    Use ML Ranking
                  </label>
                </div>
              </div>
              <button 
                className="btn-primary"
                onClick={searchJobs}
                disabled={loading}
              >
                {loading ? 'Searching...' : 'Search Jobs'}
              </button>
            </div>

            <div className="results-section">
              <h3>Search Results ({jobSearchResults.length})</h3>
              {jobSearchResults.length > 0 ? (
                <div className="recommendations-grid">
                  {jobSearchResults.map((job, index) => (
                    <div key={job.id || index} className="recommendation-card">
                      <div className="recommendation-header">
                        <h4>{job.title}</h4>
                        <span className="score">Score: {(job.similarity_score * 100).toFixed(1)}%</span>
                      </div>
                      <p><strong>Company:</strong> {job.company}</p>
                      <p><strong>Location:</strong> {job.location}</p>
                      <p><strong>Domain:</strong> {job.domain}</p>
                      <p><strong>Salary:</strong> ${job.salary_min} - ${job.salary_max}</p>
                      <p><strong>Experience:</strong> {job.total_years_required} years</p>
                      <p><strong>Similarity:</strong> {(job.similarity_score * 100).toFixed(1)}%</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-results">No jobs found</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'candidate-search' && (
          <div className="search-section">
            <h2>Semantic Candidate Search</h2>
            <div className="search-form">
              <div className="search-input-group">
                <label>Search Query:</label>
                <input
                  type="text"
                  value={candidateSearchQuery.query}
                  onChange={(e) => setCandidateSearchQuery({...candidateSearchQuery, query: e.target.value})}
                  placeholder="Enter candidate search query (e.g., 'senior Python developer')"
                />
              </div>
              <div className="search-params">
                <div className="param-group">
                  <label>Limit:</label>
                  <select
                    value={candidateSearchQuery.limit}
                    onChange={(e) => setCandidateSearchQuery({...candidateSearchQuery, limit: parseInt(e.target.value)})}
                  >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                </div>
                <div className="param-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={candidateSearchQuery.apply_filters}
                      onChange={(e) => setCandidateSearchQuery({...candidateSearchQuery, apply_filters: e.target.checked})}
                    />
                    Apply Filters
                  </label>
                </div>
                <div className="param-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={candidateSearchQuery.strict_mode}
                      onChange={(e) => setCandidateSearchQuery({...candidateSearchQuery, strict_mode: e.target.checked})}
                    />
                    Strict Mode
                  </label>
                </div>
                <div className="param-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={candidateSearchQuery.use_ml_ranking}
                      onChange={(e) => setCandidateSearchQuery({...candidateSearchQuery, use_ml_ranking: e.target.checked})}
                    />
                    Use ML Ranking
                  </label>
                </div>
              </div>
              <button 
                className="btn-primary"
                onClick={searchCandidates}
                disabled={loading}
              >
                {loading ? 'Searching...' : 'Search Candidates'}
              </button>
            </div>

            <div className="results-section">
              <h3>Search Results ({candidateSearchResults.length})</h3>
              {candidateSearchResults.length > 0 ? (
                <div className="recommendations-grid">
                  {candidateSearchResults.map((candidate, index) => (
                    <div key={candidate.candidate_id || index} className="recommendation-card">
                      <div className="recommendation-header">
                        <h4>{candidate.name}</h4>
                        <span className="score">Score: {(candidate.similarity_score * 100).toFixed(1)}%</span>
                      </div>
                      <p><strong>Location:</strong> {candidate.location}</p>
                      <p><strong>Domain:</strong> {candidate.domain}</p>
                      <p><strong>Expected Salary:</strong> ${candidate.expected_salary_min} - ${candidate.expected_salary_max}</p>
                      <p><strong>Similarity:</strong> {(candidate.similarity_score * 100).toFixed(1)}%</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-results">No candidates found</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RecommendationsEngine; 