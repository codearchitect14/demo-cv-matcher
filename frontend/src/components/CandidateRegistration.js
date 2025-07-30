import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import apiService from '../api';

const CandidateRegistration = ({ onRegistrationSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  const onSubmit = async (data) => {
    setLoading(true);
    setMessage('');
    
    try {
      const candidateData = {
        name: data.name,
        email: data.email,
        location: data.location,
        domain: data.domain,
        expected_salary_min: parseFloat(data.expected_salary_min),
        expected_salary_max: parseFloat(data.expected_salary_max),
        summary: data.summary,
        consent_given: data.consent_given || false
      };

      const response = await apiService.createCandidate(candidateData);
      setMessage(`Candidate registered successfully! ID: ${response.id}`);
      reset();
      if (onRegistrationSuccess) {
        onRegistrationSuccess(response);
      }
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>Candidate Registration</h3>
      
      {message && (
        <div className={`alert ${message.includes('Error') ? 'alert-error' : 'alert-success'}`}>
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label>Name *</label>
          <input
            type="text"
            {...register('name', { required: 'Name is required' })}
            placeholder="Enter your full name"
          />
          {errors.name && <span style={{color: 'red'}}>{errors.name.message}</span>}
        </div>

        <div className="form-group">
          <label>Email *</label>
          <input
            type="email"
            {...register('email', { 
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address'
              }
            })}
            placeholder="Enter your email address"
          />
          {errors.email && <span style={{color: 'red'}}>{errors.email.message}</span>}
        </div>

        <div className="form-group">
          <label>Location *</label>
          <input
            type="text"
            {...register('location', { required: 'Location is required' })}
            placeholder="Enter your location"
          />
          {errors.location && <span style={{color: 'red'}}>{errors.location.message}</span>}
        </div>

        <div className="form-group">
          <label>Domain *</label>
          <select {...register('domain', { required: 'Domain is required' })}>
            <option value="">Select domain</option>
            <option value="Software Development">Software Development</option>
            <option value="Data Science">Data Science</option>
            <option value="Marketing">Marketing</option>
            <option value="Sales">Sales</option>
            <option value="Finance">Finance</option>
            <option value="HR">HR</option>
            <option value="Design">Design</option>
            <option value="Product Management">Product Management</option>
          </select>
          {errors.domain && <span style={{color: 'red'}}>{errors.domain.message}</span>}
        </div>

        <div className="form-group">
          <label>Expected Salary Min *</label>
          <input
            type="number"
            {...register('expected_salary_min', { 
              required: 'Minimum salary is required',
              min: { value: 0, message: 'Salary must be positive' }
            })}
            placeholder="Enter minimum expected salary"
          />
          {errors.expected_salary_min && <span style={{color: 'red'}}>{errors.expected_salary_min.message}</span>}
        </div>

        <div className="form-group">
          <label>Expected Salary Max *</label>
          <input
            type="number"
            {...register('expected_salary_max', { 
              required: 'Maximum salary is required',
              min: { value: 0, message: 'Salary must be positive' }
            })}
            placeholder="Enter maximum expected salary"
          />
          {errors.expected_salary_max && <span style={{color: 'red'}}>{errors.expected_salary_max.message}</span>}
        </div>

        <div className="form-group">
          <label>Summary</label>
          <textarea
            {...register('summary')}
            placeholder="Enter your professional summary"
            rows="4"
          />
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              {...register('consent_given')}
            />
            I consent to data processing (GDPR compliance)
          </label>
        </div>

        <button 
          type="submit" 
          className="btn btn-primary" 
          disabled={loading}
        >
          {loading ? 'Registering...' : 'Register Candidate'}
        </button>
      </form>
    </div>
  );
};

export default CandidateRegistration; 