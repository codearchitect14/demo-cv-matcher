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
          {errors.skill && <span style={{color: 'red'}}>{typeof errors.skill.message === 'string' ? errors.skill.message : JSON.stringify(errors.skill.message)}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="years">Years of Experience:</label>
          <input
            type="number"
            id="years"
            name="years"
            value={formData.years}
            onChange={handleInputChange}
            placeholder="Enter years of experience"
            min="0"
            max="50"
            required
          />
          {errors.years && <span style={{color: 'red'}}>{typeof errors.years.message === 'string' ? errors.years.message : JSON.stringify(errors.years.message)}</span>}
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