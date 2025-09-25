import React, { useEffect, useState } from 'react';
import './AssessmentAnalytics.css';

const AssessmentAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [timeRange, setTimeRange] = useState('7d'); // 7d, 30d, 90d

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Mock analytics data - replace with real API call
      const mockData = {
        totalAssessments: 156,
        completedAssessments: 142,
        averageScore: 68.5,
        passRate: 73.2,
        cheatingAttempts: 8,
        timeRange: timeRange,
        scoreDistribution: [
          { range: '0-20%', count: 12, percentage: 8.5 },
          { range: '21-40%', count: 18, percentage: 12.7 },
          { range: '41-60%', count: 24, percentage: 16.9 },
          { range: '61-80%', count: 45, percentage: 31.7 },
          { range: '81-100%', count: 43, percentage: 30.3 }
        ],
        topPerformingJobs: [
          { jobTitle: 'Software Engineer', company: 'TechCorp', avgScore: 78.5, totalAssessments: 23 },
          { jobTitle: 'Data Scientist', company: 'DataInc', avgScore: 82.1, totalAssessments: 18 },
          { jobTitle: 'Product Manager', company: 'StartupXYZ', avgScore: 75.3, totalAssessments: 15 }
        ],
        cheatingTrends: [
          { date: '2024-01-15', attempts: 2 },
          { date: '2024-01-16', attempts: 1 },
          { date: '2024-01-17', attempts: 0 },
          { date: '2024-01-18', attempts: 3 },
          { date: '2024-01-19', attempts: 1 },
          { date: '2024-01-20', attempts: 1 },
          { date: '2024-01-21', attempts: 0 }
        ],
        completionRates: {
          onTime: 89.4,
          late: 8.1,
          incomplete: 2.5
        }
      };
      
      setAnalytics(mockData);
    } catch (err) {
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="assessment-analytics">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading assessment analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="assessment-analytics">
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button onClick={fetchAnalytics} className="retry-btn">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="assessment-analytics">
      <div className="analytics-header">
        <h1>Assessment Analytics</h1>
        <div className="time-range-selector">
          <label>Time Range:</label>
          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon">📊</div>
          <div className="metric-content">
            <h3>{analytics.totalAssessments}</h3>
            <p>Total Assessments</p>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">✅</div>
          <div className="metric-content">
            <h3>{analytics.completedAssessments}</h3>
            <p>Completed</p>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">📈</div>
          <div className="metric-content">
            <h3>{analytics.averageScore}%</h3>
            <p>Average Score</p>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">🎯</div>
          <div className="metric-content">
            <h3>{analytics.passRate}%</h3>
            <p>Pass Rate</p>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">🚫</div>
          <div className="metric-content">
            <h3>{analytics.cheatingAttempts}</h3>
            <p>Cheating Attempts</p>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-section">
        <div className="chart-container">
          <h3>Score Distribution</h3>
          <div className="score-distribution">
            {analytics.scoreDistribution.map((item, index) => (
              <div key={index} className="score-bar">
                <div className="bar-label">{item.range}</div>
                <div className="bar-container">
                  <div 
                    className="bar-fill" 
                    style={{ width: `${item.percentage}%` }}
                  ></div>
                </div>
                <div className="bar-value">{item.count} ({item.percentage}%)</div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-container">
          <h3>Top Performing Jobs</h3>
          <div className="top-jobs-list">
            {analytics.topPerformingJobs.map((job, index) => (
              <div key={index} className="job-performance-item">
                <div className="job-info">
                  <h4>{job.jobTitle}</h4>
                  <p>{job.company}</p>
                </div>
                <div className="job-stats">
                  <div className="stat">
                    <span className="stat-value">{job.avgScore}%</span>
                    <span className="stat-label">Avg Score</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{job.totalAssessments}</span>
                    <span className="stat-label">Assessments</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Completion Rates */}
      <div className="completion-section">
        <h3>Assessment Completion Rates</h3>
        <div className="completion-grid">
          <div className="completion-item">
            <div className="completion-icon">⏰</div>
            <div className="completion-content">
              <h4>{analytics.completionRates.onTime}%</h4>
              <p>Completed on Time</p>
            </div>
          </div>
          
          <div className="completion-item">
            <div className="completion-icon">⏳</div>
            <div className="completion-content">
              <h4>{analytics.completionRates.late}%</h4>
              <p>Completed Late</p>
            </div>
          </div>
          
          <div className="completion-item">
            <div className="completion-icon">❌</div>
            <div className="completion-content">
              <h4>{analytics.completionRates.incomplete}%</h4>
              <p>Incomplete</p>
            </div>
          </div>
        </div>
      </div>

      {/* Cheating Trends */}
      <div className="cheating-trends">
        <h3>Cheating Attempts Trend</h3>
        <div className="trend-chart">
          {analytics.cheatingTrends.map((trend, index) => (
            <div key={index} className="trend-day">
              <div className="trend-bar" style={{ height: `${(trend.attempts / 3) * 100}%` }}></div>
              <div className="trend-label">{new Date(trend.date).toLocaleDateString()}</div>
              <div className="trend-value">{trend.attempts}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AssessmentAnalytics;
