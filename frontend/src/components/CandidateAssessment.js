import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './CandidateAssessment.css';

const CandidateAssessment = ({ onSubmitted }) => {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const [assessment, setAssessment] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [timeLeft, setTimeLeft] = useState(20 * 60); // 20 minutes default
  const [cheatAttempts, setCheatAttempts] = useState(0);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    const load = async () => {
      try {
        // First check if assessment exists
        let res = await fetch(`http://localhost:8000/api/v1/assessments-fast/assigned?application_id=${applicationId}`);
        
        if (!res.ok) {
          // Assessment doesn't exist, try to assign it first
          console.log('Assessment not found, attempting to assign...');
          
          // Get application details to find job_id and candidate_id
          const appRes = await fetch(`http://localhost:8000/api/v1/applications/public?application_id=${applicationId}`);
          if (appRes.ok) {
            const appData = await appRes.json();
            const application = Array.isArray(appData) ? appData[0] : appData;
            
            if (application) {
              // Assign assessment
              const assignRes = await fetch(`http://localhost:8000/api/v1/assessments-fast/assign?application_id=${applicationId}&candidate_id=${application.candidate_id}&job_id=${application.job_id}&validity_hours=24`, { method: 'POST' });
              
              if (assignRes.ok) {
                console.log('Assessment assigned successfully');
                // Now try to get the assigned assessment
                res = await fetch(`http://localhost:8000/api/v1/assessments-fast/assigned?application_id=${applicationId}`);
              } else {
                throw new Error('Failed to assign assessment');
              }
            } else {
              throw new Error('Application not found');
            }
          } else {
            throw new Error('Failed to get application details');
          }
        }

        if (res.ok) {
          const data = await res.json();
          
          // Check if MCQs exist
          if (!data.mcqs || data.mcqs.length === 0) {
            throw new Error('No assessment questions are configured for this job. Please contact the recruiter.');
          }
          
          setAssessment(data);
          setAnswers(Array.from({ length: (data.mcqs || []).length }, () => ''));
          
          // Check if already submitted
          if (data.status === 'completed') {
            setIsSubmitted(true);
            setIsSubmitting(true);
          } else {
            // Now start the assessment
            const startRes = await fetch(`http://localhost:8000/api/v1/assessments-fast/start?application_id=${applicationId}`, { method: 'POST' });
            if (!startRes.ok) {
              console.warn('Failed to start assessment:', await startRes.text());
            }
          }
        } else {
          const errorData = await res.json().catch(() => ({ detail: 'Assessment not found' }));
          throw new Error(errorData.detail || 'Assessment not found');
        }
      } catch (e) {
        console.error('Assessment load error:', e);
        setError(`Failed to load assessment: ${e.message}`);
      }
    };
    if (applicationId) load();
  }, [applicationId]);

  // Timer
  useEffect(() => {
    if (!assessment || isSubmitted) return;
    timerRef.current = setInterval(() => setTimeLeft(prev => prev > 0 ? prev - 1 : 0), 1000);
    return () => clearInterval(timerRef.current);
  }, [assessment, isSubmitted]);

  useEffect(() => {
    const handleBlur = () => {
      setCheatAttempts((v) => v + 1);
      handleSubmit(true); // auto-submit and fail on cheating
    };
    window.addEventListener('blur', handleBlur);
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) handleBlur();
    });
    return () => {
      window.removeEventListener('blur', handleBlur);
      document.removeEventListener('visibilitychange', handleBlur);
    };
  }, []);

  useEffect(() => {
    if (timeLeft === 0 && assessment && !isSubmitted && !isSubmitting) {
      console.log('Timer expired, auto-submitting...');
      handleSubmit(true);
    }
  }, [timeLeft, assessment, isSubmitted, isSubmitting]);

  const setAnswer = (idx, val) => {
    setAnswers(prev => prev.map((a, i) => i === idx ? val : a));
  };

  const handleSubmit = async (auto = false) => {
    if (isSubmitting || isSubmitted) {
      console.log('Assessment already submitted, ignoring submission');
      return;
    }
    
    try {
      setIsSubmitting(true);
      const submitData = {
        application_id: parseInt(applicationId),
        answers: answers,
        cheat_attempts: auto ? Math.max(1, cheatAttempts) : cheatAttempts
      };
      
      console.log('Submitting assessment:', submitData);
      
      const res = await fetch('http://localhost:8000/api/v1/assessments-fast/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submitData)
      });
      if (res.ok) {
        const data = await res.json();
        setIsSubmitted(true);
        
        if (onSubmitted) {
          onSubmitted(data);
        } else {
          // Show completion message and navigate back
          alert(`Assessment completed! Score: ${data.score}%`);
          navigate('/my-applications');
        }
      } else {
        const err = await res.json().catch(()=>({detail:'Submit failed'}));
        setError(err.detail || 'Submit failed');
        setIsSubmitting(false);
      }
    } catch (e) {
      setError('Submit failed');
      setIsSubmitting(false);
    }
  };

  if (!assessment) return <div className="assessment-page">Loading assessment...</div>;

  if (isSubmitted && assessment.status === 'completed') {
    return (
      <div className="assessment-page">
        <div className="assessment-header">
          <h1>Assessment Completed</h1>
          <div className="score-display">
            <h2>Your Score: {assessment.score}%</h2>
            <p>Completed on: {new Date(assessment.completion_time).toLocaleString()}</p>
            <button onClick={() => navigate('/my-applications')} className="btn-primary">
              Back to Applications
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="assessment-page">
      <div className="assessment-header">
        <h2>Assessment</h2>
        <div className="timer">Time left: {Math.floor(timeLeft/60)}:{String(timeLeft%60).padStart(2,'0')}</div>
      </div>
      {error && <div className="error-message">{error}</div>}
      <div className="mcq-list">
        {assessment.mcqs && assessment.mcqs.map((q, idx) => (
          <div key={idx} className="mcq-item">
            <div className="question">Q{idx+1}. {q.question}</div>
            <div className="options">
              {['A','B','C','D'].map(k => (
                <label key={k} className={`option ${answers[idx]===k?'selected':''}`}>
                  <input type="radio" name={`q${idx}`} value={k} checked={answers[idx]===k} onChange={()=>setAnswer(idx,k)} />
                  <span className="option-key">{k}.</span> {q.options[k]}
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="actions">
        <button 
          className="btn btn-primary" 
          onClick={()=>handleSubmit(false)}
          disabled={isSubmitting || isSubmitted}
        >
          {isSubmitting ? 'Submitting...' : isSubmitted ? 'Submitted' : 'Submit'}
        </button>
      </div>
    </div>
  );
};

export default CandidateAssessment;


