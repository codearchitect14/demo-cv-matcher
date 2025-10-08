import React, { useEffect, useState } from 'react';
import CopyMCQsModal from './CopyMCQsModal';
import MCQTemplatesModal from './MCQTemplatesModal';

const emptyMCQ = () => ({ question: '', options: { A: '', B: '', C: '', D: '' }, correct: 'A' });

const RecruiterMCQEditor = ({ jobId, onSaved }) => {
  const [mcqs, setMcqs] = useState(Array.from({ length: 20 }, () => emptyMCQ()));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/assessments-fast/mcqs/${jobId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.mcqs && data.mcqs.length > 0) {
            setMcqs(prevMcqs => {
              const filled = [...prevMcqs];
              data.mcqs.slice(0, 20).forEach((q, i) => filled[i] = q);
              return filled;
            });
          }
        }
      } catch (e) {
        // ignore
      }
    };
    if (jobId) load();
  }, [jobId]);

  const updateMCQ = (idx, field, value, optionKey) => {
    setMcqs(prev => prev.map((q, i) => {
      if (i !== idx) return q;
      if (field === 'question') return { ...q, question: value };
      if (field === 'option') return { ...q, options: { ...q.options, [optionKey]: value } };
      if (field === 'correct') return { ...q, correct: value };
      return q;
    }));
  };

  const save = async () => {
    setLoading(true); setError(''); setMessage('');
    try {
      const payload = mcqs.filter(q => q.question.trim());
      const res = await fetch(`http://localhost:8000/api/v1/assessments-fast/mcqs/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const err = await res.json().catch(()=>({detail:'Failed'}));
        throw new Error(err.detail || 'Failed to save MCQs');
      }
      setMessage('MCQs saved');
      if (onSaved) onSaved();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const copyFromJob = async (sourceJobId) => {
    if (!sourceJobId) return;
    
    setLoading(true); setError(''); setMessage('');
    try {
      const res = await fetch(`http://localhost:8000/api/v1/assessments-fast/mcqs/${sourceJobId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.mcqs && data.mcqs.length > 0) {
          const filled = [...mcqs];
          data.mcqs.slice(0, 20).forEach((q, i) => filled[i] = q);
          setMcqs(filled);
          setMessage(`Copied ${data.mcqs.length} MCQs from job ${sourceJobId}`);
        } else {
          setError('No MCQs found in source job');
        }
      } else {
        throw new Error('Failed to fetch MCQs from source job');
      }
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const applyTemplate = (templateMCQs) => {
    if (!templateMCQs || templateMCQs.length === 0) return;
    
    const filled = [...mcqs];
    templateMCQs.slice(0, 20).forEach((q, i) => filled[i] = q);
    setMcqs(filled);
    setMessage(`Applied template with ${templateMCQs.length} MCQs`);
  };

  return (
    <div className="mcq-editor">
      <div className="mcq-header">
        <h3>Assessment Questions (max 20)</h3>
        <div className="header-actions">
          <MCQTemplatesModal onApplyTemplate={applyTemplate} />
          <CopyMCQsModal onCopy={copyFromJob} />
          <button className="btn btn-primary" onClick={save} disabled={loading}>
            {loading ? 'Saving...' : 'Save MCQs'}
          </button>
        </div>
      </div>
      {error && <div className="error-message">{error}</div>}
      {message && <div className="success-message">{message}</div>}
      <div className="mcq-grid">
        {mcqs.map((q, idx) => (
          <div key={idx} className="mcq-item">
            <div className="form-group"><label>Q{idx+1}</label>
              <textarea value={q.question} onChange={e=>updateMCQ(idx,'question',e.target.value)} rows={2} placeholder="Enter question text..." />
            </div>
            {['A','B','C','D'].map(k => (
              <div className="form-group" key={k}>
                <label>Option {k}</label>
                <input type="text" value={q.options[k]} onChange={e=>updateMCQ(idx,'option',e.target.value,k)} />
              </div>
            ))}
            <div className="form-group"><label>Correct</label>
              <select value={q.correct} onChange={e=>updateMCQ(idx,'correct',e.target.value)}>
                {['A','B','C','D'].map(k=> <option key={k} value={k}>{k}</option>)}
              </select>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecruiterMCQEditor;


