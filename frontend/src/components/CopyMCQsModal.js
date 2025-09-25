import React, { useState, useEffect } from 'react';

const CopyMCQsModal = ({ onCopy }) => {
  const [showModal, setShowModal] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (showModal) {
      fetchJobs();
    }
  }, [showModal]);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      // Mock jobs data - replace with real API call
      const mockJobs = [
        { id: 1, title: 'Software Engineer', company: 'TechCorp' },
        { id: 2, title: 'Data Scientist', company: 'DataInc' },
        { id: 3, title: 'Product Manager', company: 'StartupXYZ' },
        { id: 4, title: 'Frontend Developer', company: 'WebCo' },
        { id: 5, title: 'Backend Developer', company: 'ServerPro' }
      ];
      setJobs(mockJobs);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (selectedJobId) {
      onCopy(selectedJobId);
      setShowModal(false);
      setSelectedJobId('');
    }
  };

  return (
    <>
      <button 
        className="btn btn-secondary"
        onClick={() => setShowModal(true)}
        style={{
          background: '#6b7280',
          color: 'white',
          padding: '8px 16px',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '0.875rem',
          fontWeight: '500',
          marginRight: '10px'
        }}
      >
        📋 Copy from Job
      </button>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="copy-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Copy MCQs from Another Job</h3>
              <button 
                className="modal-close"
                onClick={() => setShowModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#6b7280'
                }}
              >
                ×
              </button>
            </div>
            
            <div className="modal-content">
              <p>Select a job to copy MCQs from:</p>
              
              {loading ? (
                <div className="loading-state">
                  <div className="loading-spinner"></div>
                  <p>Loading jobs...</p>
                </div>
              ) : (
                <div className="jobs-list">
                  {jobs.length === 0 ? (
                    <p className="no-jobs">No jobs available</p>
                  ) : (
                    <div className="job-options">
                      {jobs.map((job) => (
                        <label key={job.id} className="job-option">
                          <input
                            type="radio"
                            name="sourceJob"
                            value={job.id}
                            checked={selectedJobId === job.id.toString()}
                            onChange={(e) => setSelectedJobId(e.target.value)}
                          />
                          <div className="job-info">
                            <span className="job-title">{job.title}</span>
                            <span className="job-company">{job.company}</span>
                          </div>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="modal-footer">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowModal(false)}
                style={{
                  background: '#6b7280',
                  color: 'white',
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  marginRight: '10px'
                }}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleCopy}
                disabled={!selectedJobId || loading}
                style={{
                  background: selectedJobId ? '#3b82f6' : '#9ca3af',
                  color: 'white',
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: selectedJobId ? 'pointer' : 'not-allowed'
                }}
              >
                Copy MCQs
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .copy-modal {
          background: white;
          border-radius: 12px;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
          max-width: 500px;
          width: 90%;
          max-height: 80vh;
          overflow: hidden;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .modal-header h3 {
          margin: 0;
          color: #1f2937;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .modal-content {
          padding: 20px;
          max-height: 400px;
          overflow-y: auto;
        }

        .loading-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 40px;
        }

        .loading-spinner {
          width: 32px;
          height: 32px;
          border: 3px solid #f3f4f6;
          border-top: 3px solid #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 10px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .jobs-list {
          margin-top: 15px;
        }

        .no-jobs {
          text-align: center;
          color: #6b7280;
          padding: 20px;
        }

        .job-options {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .job-option {
          display: flex;
          align-items: center;
          padding: 12px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .job-option:hover {
          background: #f9fafb;
        }

        .job-option input[type="radio"] {
          margin-right: 12px;
          width: 16px;
          height: 16px;
          accent-color: #3b82f6;
        }

        .job-info {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .job-title {
          font-weight: 500;
          color: #1f2937;
          font-size: 0.875rem;
        }

        .job-company {
          color: #6b7280;
          font-size: 0.75rem;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          padding: 20px;
          border-top: 1px solid #e5e7eb;
        }
      `}</style>
    </>
  );
};

export default CopyMCQsModal;
