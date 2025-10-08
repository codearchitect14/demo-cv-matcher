import React, { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import apiService from '../api';

const CandidateRegistration = ({ onRegistrationSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { register, handleSubmit, reset, control, formState: { errors } } = useForm({
    defaultValues: {
      skills: [{ name: '', years: 0 }]
    }
  });
  const { fields, append, remove } = useFieldArray({
    control,
    name: "skills"
  });

  const onSubmit = async (data) => {
    setLoading(true);
    setMessage('');
    
    try {
      // Filter out empty skills
      const skills = data.skills.filter(skill => skill.name && skill.name.trim() !== '');
      
      const candidateData = {
        name: data.name,
        email: data.email,
        password: data.password,
        location: data.location,
        domain: data.domain,
        expected_salary_min: parseFloat(data.expected_salary_min),
        expected_salary_max: parseFloat(data.expected_salary_max),
        summary: data.summary,
        consent_given: data.consent_given || false,
        total_experience_years: data.total_experience_years ? parseInt(data.total_experience_years) : null,
        skills: skills.length > 0 ? skills.map(skill => ({
          name: skill.name.trim(),
          years: parseInt(skill.years) || 0
        })) : null
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
          {errors.name && <span style={{color: 'red'}}>{typeof errors.name.message === 'string' ? errors.name.message : JSON.stringify(errors.name.message)}</span>}
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
          {errors.email && <span style={{color: 'red'}}>{typeof errors.email.message === 'string' ? errors.email.message : JSON.stringify(errors.email.message)}</span>}
        </div>

        <div className="form-group">
          <label>Password *</label>
          <input
            type="password"
            {...register('password', { 
              required: 'Password is required',
              minLength: {
                value: 8,
                message: 'Password must be at least 8 characters'
              }
            })}
            placeholder="Enter your password"
          />
          {errors.password && <span style={{color: 'red'}}>{typeof errors.password.message === 'string' ? errors.password.message : JSON.stringify(errors.password.message)}</span>}
        </div>

        <div className="form-group">
          <label>Location *</label>
          <input
            type="text"
            {...register('location', { required: 'Location is required' })}
            placeholder="Enter your location"
          />
          {errors.location && <span style={{color: 'red'}}>{typeof errors.location.message === 'string' ? errors.location.message : JSON.stringify(errors.location.message)}</span>}
        </div>

        <div className="form-group">
          <label>Professional Domain *</label>
          <select {...register('domain', { required: 'Domain is required' })}>
            <option value="">Select domain</option>
            <option value="IT">IT</option>
            <option value="AI">AI</option>
            <option value="Healthcare">Healthcare</option>
            <option value="Education">Education</option>
            <option value="Retail">Retail</option>
            <option value="Finance">Finance</option>
            <option value="Marketing">Marketing</option>
            <option value="Sales">Sales</option>
            <option value="HR">HR</option>
            <option value="Design">Design</option>
            <option value="Product Management">Product Management</option>
          </select>
          {errors.domain && <span style={{color: 'red'}}>{typeof errors.domain.message === 'string' ? errors.domain.message : JSON.stringify(errors.domain.message)}</span>}
        </div>

        <div className="form-group">
          <label>Total Years of Experience *</label>
          <input
            type="number"
            {...register('total_experience_years', { 
              required: 'Total experience is required',
              min: { value: 0, message: 'Experience must be 0 or more' },
              max: { value: 50, message: 'Experience cannot exceed 50 years' }
            })}
            placeholder="Enter total years of professional experience"
          />
          {errors.total_experience_years && <span style={{color: 'red'}}>{typeof errors.total_experience_years.message === 'string' ? errors.total_experience_years.message : JSON.stringify(errors.total_experience_years.message)}</span>}
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
          {errors.expected_salary_min && <span style={{color: 'red'}}>{typeof errors.expected_salary_min.message === 'string' ? errors.expected_salary_min.message : JSON.stringify(errors.expected_salary_min.message)}</span>}
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
          {errors.expected_salary_max && <span style={{color: 'red'}}>{typeof errors.expected_salary_max.message === 'string' ? errors.expected_salary_max.message : JSON.stringify(errors.expected_salary_max.message)}</span>}
        </div>

        <div className="form-group">
          <label>Skills with Years of Experience</label>
          {fields.map((field, index) => (
            <div key={field.id} style={{ display: 'flex', gap: '10px', marginBottom: '10px', alignItems: 'center' }}>
              <input
                type="text"
                placeholder="Skill name (e.g., Python)"
                {...register(`skills.${index}.name`, { required: index === 0 ? 'At least one skill is required' : false })}
                style={{ flex: 1 }}
              />
              <input
                type="number"
                placeholder="Years"
                min="0"
                max="20"
                {...register(`skills.${index}.years`, { 
                  required: index === 0 ? 'Years of experience is required' : false,
                  min: { value: 0, message: 'Must be 0 or more' },
                  max: { value: 20, message: 'Cannot exceed 20 years' }
                })}
                style={{ width: '80px' }}
              />
              {fields.length > 1 && (
                <button
                  type="button"
                  onClick={() => remove(index)}
                  style={{ 
                    background: '#dc3545', 
                    color: 'white', 
                    border: 'none', 
                    padding: '8px 12px', 
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={() => append({ name: '', years: 0 })}
            style={{ 
              background: '#28a745', 
              color: 'white', 
              border: 'none', 
              padding: '8px 16px', 
              borderRadius: '4px',
              cursor: 'pointer',
              marginTop: '10px'
            }}
          >
            Add Another Skill
          </button>
          {errors.skills && <span style={{color: 'red'}}>Please fill in at least one skill</span>}
        </div>

        <div className="form-group">
          <label>Professional Summary</label>
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