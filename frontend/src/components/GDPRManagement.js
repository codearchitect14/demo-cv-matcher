import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import apiService from '../api';

const GDPRManagement = () => {
  const [candidateId, setCandidateId] = useState('');
  const [consentStatus, setConsentStatus] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [exportedData, setExportedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  const handleConsentUpdate = async (data) => {
    setLoading(true);
    setMessage('');
    
    try {
      await apiService.updateConsent(data.candidate_id, {
        candidate_id: parseInt(data.candidate_id),
        consent_given: data.consent_given,
        admin_id: 1
      });
      setMessage('Consent updated successfully!');
      reset();
      fetchConsentStatus(data.candidate_id);
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDataDeletion = async (data) => {
    if (!window.confirm('Are you sure you want to delete all data for this candidate? This action cannot be undone.')) {
      return;
    }
    
    setLoading(true);
    setMessage('');
    
    try {
      await apiService.deleteUserData(data.candidate_id, {
        candidate_id: parseInt(data.candidate_id),
        reason: data.reason,
        admin_id: 1
      });
      setMessage('User data deleted successfully!');
      reset();
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchConsentStatus = async (id) => {
    try {
      const status = await apiService.getConsentStatus(id);
      setConsentStatus(status);
    } catch (error) {
      console.error('Error fetching consent status:', error);
    }
  };

  const fetchAuditLogs = async (id) => {
    try {
      const logs = await apiService.getAuditLogs(id);
      setAuditLogs(logs.audit_logs || []);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    }
  };

  const handleExportData = async (id) => {
    try {
      const data = await apiService.exportUserData(id);
      setExportedData(data);
      setMessage('Data exported successfully!');
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleCandidateIdChange = (id) => {
    setCandidateId(id);
    if (id) {
      fetchConsentStatus(id);
      fetchAuditLogs(id);
    } else {
      setConsentStatus(null);
      setAuditLogs([]);
    }
  };

  return (
    <div className="container">
      <h2>GDPR Management</h2>
      
      {message && (
        <div className={`alert ${message.includes('Error') ? 'alert-error' : 'alert-success'}`}>
          {message}
        </div>
      )}

      <div className="card">
        <h3>Candidate ID</h3>
        <div className="form-group">
          <input
            type="number"
            value={candidateId}
            onChange={(e) => handleCandidateIdChange(e.target.value)}
            placeholder="Enter candidate ID"
          />
        </div>
      </div>

      {candidateId && (
        <>
          <div className="grid">
            <div className="card">
              <h3>Consent Management</h3>
              <form onSubmit={handleSubmit(handleConsentUpdate)}>
                <input type="hidden" {...register('candidate_id')} value={candidateId} />
                
                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      {...register('consent_given')}
                    />
                    Consent Given
                  </label>
                </div>

                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  disabled={loading}
                >
                  {loading ? 'Updating...' : 'Update Consent'}
                </button>
              </form>

              {consentStatus && (
                <div style={{ marginTop: '15px' }}>
                  <h4>Current Status:</h4>
                  <p><strong>Consent Given:</strong> {consentStatus.data?.consent_given ? 'Yes' : 'No'}</p>
                  <p><strong>Last Updated:</strong> {consentStatus.data?.last_updated}</p>
                </div>
              )}
            </div>

            <div className="card">
              <h3>Data Export</h3>
              <button 
                className="btn btn-primary" 
                onClick={() => handleExportData(candidateId)}
                disabled={loading}
              >
                Export User Data
              </button>

              {exportedData && (
                <div style={{ marginTop: '15px' }}>
                  <h4>Exported Data:</h4>
                  <pre style={{ 
                    background: '#f5f5f5', 
                    padding: '10px', 
                    borderRadius: '4px',
                    fontSize: '12px',
                    maxHeight: '200px',
                    overflow: 'auto'
                  }}>
                    {JSON.stringify(exportedData, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <h3>Data Deletion (Right to be Forgotten)</h3>
            <form onSubmit={handleSubmit(handleDataDeletion)}>
              <input type="hidden" {...register('candidate_id')} value={candidateId} />
              
              <div className="form-group">
                <label>Reason for Deletion</label>
                <textarea
                  {...register('reason', { required: 'Reason is required' })}
                  placeholder="Enter reason for data deletion"
                  rows="3"
                />
                {errors.reason && <span style={{color: 'red'}}>{typeof errors.reason.message === 'string' ? errors.reason.message : JSON.stringify(errors.reason.message)}</span>}
              </div>

              <button 
                type="submit" 
                className="btn btn-danger" 
                disabled={loading}
              >
                {loading ? 'Deleting...' : 'Delete All User Data'}
              </button>
            </form>
          </div>

          <div className="card">
            <h3>Audit Logs</h3>
            {auditLogs.length > 0 ? (
              <div>
                <h4>Recent Activity:</h4>
                <ul>
                  {auditLogs.map((log, index) => (
                    <li key={index}>
                      <strong>{log.action_type}</strong> - {log.created_at}
                      {log.details && (
                        <div style={{ marginLeft: '20px', fontSize: '12px', color: '#666' }}>
                          {typeof log.details === 'string' ? log.details : JSON.stringify(log.details)}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p>No audit logs found for this candidate.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default GDPRManagement; 