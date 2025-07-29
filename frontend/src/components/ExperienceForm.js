import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import apiService from '../api';

const ExperienceForm = ({ candidateId, onExperienceAdded }) => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  const onSubmit = async (data) => {
    setLoading(true);
    setMessage('');
    
    try {
      const experienceData = {
        skill: data.skill,
        years: parseInt(data.years),
        description: data.description
      };

      const response = await apiService.addExperience(candidateId, experienceData);
      setMessage('Experience added successfully!');
      reset();
      if (onExperienceAdded) {
        onExperienceAdded(response);
      }
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>Add Experience</h3>
      
      {message && (
        <div className={`alert ${message.includes('Error') ? 'alert-error' : 'alert-success'}`}>
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label>Skill *</label>
          <input
            type="text"
            {...register('skill', { required: 'Skill is required' })}
            placeholder="Enter skill name"
          />
          {errors.skill && <span style={{color: 'red'}}>{errors.skill.message}</span>}
        </div>

        <div className="form-group">
          <label>Years of Experience *</label>
          <input
            type="number"
            {...register('years', { 
              required: 'Years of experience is required',
              min: { value: 0, message: 'Years must be 0 or more' },
              max: { value: 50, message: 'Years cannot exceed 50' }
            })}
            placeholder="Enter years of experience"
          />
          {errors.years && <span style={{color: 'red'}}>{errors.years.message}</span>}
        </div>

        <div className="form-group">
          <label>Description</label>
          <textarea
            {...register('description')}
            placeholder="Describe your experience with this skill"
            rows="3"
          />
        </div>

        <button 
          type="submit" 
          className="btn btn-primary" 
          disabled={loading}
        >
          {loading ? 'Adding...' : 'Add Experience'}
        </button>
      </form>
    </div>
  );
};

export default ExperienceForm; 