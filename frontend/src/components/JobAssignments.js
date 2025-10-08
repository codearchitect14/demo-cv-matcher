import React, { useState, useEffect } from 'react';
import './JobAssignments.css';

const JobAssignments = () => {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAssignments();
  }, []);

  const fetchAssignments = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/v1/jobs-fast/assignments-fast');
      
      if (response.ok) {
        const data = await response.json();
        setAssignments(data.assignments || []);
        setError('');
      } else {
        setError('Failed to fetch job assignments');
      }
    } catch (error) {
      setError(String(error));
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    return status === 'Assigned' ? 'status-assigned' : 'status-unassigned';
  };

  if (loading) {
    return (
      <div className="job-assignments-container">
        <div className="loading">Loading job assignments...</div>
      </div>
    );
  }

  return (
    <div className="job-assignments-container">
      <div className="assignments-header">
        <h1>Job Assignments</h1>
        <button onClick={fetchAssignments} className="btn-refresh">
          Refresh
        </button>
        <button onClick={() => window.location.href = '/jobs-dashboard'} className="btn-back">
          Back to Dashboard
        </button>
        <button onClick={() => window.location.href = '/login'} className="btn-logout">
          Logout
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          Error: {error}
        </div>
      )}

      <div className="assignments-summary">
        <div className="summary-card">
          <h3>Total Jobs</h3>
          <span className="summary-number">{assignments.length}</span>
        </div>
        <div className="summary-card">
          <h3>Assigned Jobs</h3>
          <span className="summary-number assigned">
            {assignments.filter(a => a.status === 'Assigned').length}
          </span>
        </div>
        <div className="summary-card">
          <h3>Unassigned Jobs</h3>
          <span className="summary-number unassigned">
            {assignments.filter(a => a.status === 'Unassigned').length}
          </span>
        </div>
      </div>

      <div className="assignments-table-container">
        <table className="assignments-table">
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Job Title</th>
              <th>Company</th>
              <th>Location</th>
              <th>Recruiter</th>
              <th>Email</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {assignments.map((assignment) => (
              <tr key={assignment.job_id}>
                <td>{assignment.job_id}</td>
                <td>{String(assignment.job_title)}</td>
                <td>{String(assignment.company)}</td>
                <td>{String(assignment.location)}</td>
                <td>{String(assignment.recruiter_name)}</td>
                <td>{String(assignment.recruiter_email)}</td>
                <td>
                  <span className={`status-badge ${getStatusColor(assignment.status)}`}>
                    {assignment.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {assignments.length === 0 && !loading && (
        <div className="no-assignments">
          <p>No job assignments found.</p>
        </div>
      )}
    </div>
  );
};

export default JobAssignments;



