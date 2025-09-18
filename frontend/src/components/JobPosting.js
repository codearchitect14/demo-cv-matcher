import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import apiService from '../api';

const JobPosting = ({ onJobPosted }) => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [mandatorySkills, setMandatorySkills] = useState([]);
  const [newSkill, setNewSkill] = useState({ skill: '', min_experience: '' });
  const [recruiters, setRecruiters] = useState([]);
  const [loadingRecruiters, setLoadingRecruiters] = useState(false);
  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  // Fetch recruiters on component mount
  useEffect(() => {
    const fetchRecruiters = async () => {
      setLoadingRecruiters(true);
      try {
        const response = await fetch('http://localhost:8000/api/v1/jobs-fast/recruiters-fast');
        if (response.ok) {
          const data = await response.json();
          setRecruiters(data);
        }
      } catch (error) {
        console.error('Error fetching recruiters:', error);
      } finally {
        setLoadingRecruiters(false);
      }
    };

    fetchRecruiters();
  }, []);

  const onSubmit = async (data) => {
    setLoading(true);
    setMessage('');
    
    try {
      const jobData = {
        title: data.title,
        company: data.company,
        location: data.location,
        domain: data.domain,
        salary_min: parseFloat(data.salary_min),
        salary_max: parseFloat(data.salary_max),
        total_years_required: parseInt(data.total_years_required),
        job_description: data.description,
        recruiter_id: data.recruiter_id ? parseInt(data.recruiter_id) : null
      };

      const response = await apiService.createJob(jobData);
      setMessage(`Job posted successfully! ID: ${response.id}`);
      
      // Add mandatory skills if any
      if (mandatorySkills.length > 0) {
        for (const skill of mandatorySkills) {
          await apiService.addMandatorySkill(response.id, skill);
        }
      }
      
      reset();
      setMandatorySkills([]);
      if (onJobPosted) {
        onJobPosted(response);
      }
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const addMandatorySkill = () => {
    if (newSkill.skill && newSkill.min_experience) {
      setMandatorySkills([...mandatorySkills, {
        skill: newSkill.skill,
        min_experience: parseInt(newSkill.min_experience)
      }]);
      setNewSkill({ skill: '', min_experience: '' });
    }
  };

  const removeMandatorySkill = (index) => {
    setMandatorySkills(mandatorySkills.filter((_, i) => i !== index));
  };

  return (
    <div className="card">
      <h3>Post New Job</h3>
      
      {message && (
        <div className={`alert ${message.includes('Error') ? 'alert-error' : 'alert-success'}`}>
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label>Job Title *</label>
          <input
            type="text"
            {...register('title', { required: 'Job title is required' })}
            placeholder="Enter job title"
          />
          {errors.title && <span style={{color: 'red'}}>{typeof errors.title.message === 'string' ? errors.title.message : JSON.stringify(errors.title.message)}</span>}
        </div>

        <div className="form-group">
          <label>Company *</label>
          <input
            type="text"
            {...register('company', { required: 'Company name is required' })}
            placeholder="Enter company name"
          />
          {errors.company && <span style={{color: 'red'}}>{typeof errors.company.message === 'string' ? errors.company.message : JSON.stringify(errors.company.message)}</span>}
        </div>

        <div className="form-group">
          <label>Location *</label>
          <input
            type="text"
            {...register('location', { required: 'Location is required' })}
            placeholder="Enter job location"
          />
          {errors.location && <span style={{color: 'red'}}>{typeof errors.location.message === 'string' ? errors.location.message : JSON.stringify(errors.location.message)}</span>}
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
          {errors.domain && <span style={{color: 'red'}}>{typeof errors.domain.message === 'string' ? errors.domain.message : JSON.stringify(errors.domain.message)}</span>}
        </div>

        <div className="form-group">
          <label>Assigned Recruiter</label>
          <select {...register('recruiter_id')}>
            <option value="">Select recruiter (optional)</option>
            {loadingRecruiters ? (
              <option disabled>Loading recruiters...</option>
            ) : (
              recruiters.map(recruiter => (
                <option key={recruiter.id} value={recruiter.id}>
                  {recruiter.name} ({recruiter.email})
                </option>
              ))
            )}
          </select>
          <small style={{color: '#666', fontSize: '12px'}}>
            Leave empty to assign later or for admin assignment
          </small>
        </div>

        <div className="form-group">
          <label>Salary Min *</label>
          <input
            type="number"
            {...register('salary_min', { 
              required: 'Minimum salary is required',
              min: { value: 0, message: 'Salary must be positive' }
            })}
            placeholder="Enter minimum salary"
          />
          {errors.salary_min && <span style={{color: 'red'}}>{typeof errors.salary_min.message === 'string' ? errors.salary_min.message : JSON.stringify(errors.salary_min.message)}</span>}
        </div>

        <div className="form-group">
          <label>Salary Max *</label>
          <input
            type="number"
            {...register('salary_max', { 
              required: 'Maximum salary is required',
              min: { value: 0, message: 'Salary must be positive' }
            })}
            placeholder="Enter maximum salary"
          />
          {errors.salary_max && <span style={{color: 'red'}}>{typeof errors.salary_max.message === 'string' ? errors.salary_max.message : JSON.stringify(errors.salary_max.message)}</span>}
        </div>

        <div className="form-group">
          <label>Total Years Required *</label>
          <input
            type="number"
            {...register('total_years_required', { 
              required: 'Total years required is required',
              min: { value: 0, message: 'Years must be 0 or more' }
            })}
            placeholder="Enter total years of experience required"
          />
          {errors.total_years_required && <span style={{color: 'red'}}>{typeof errors.total_years_required.message === 'string' ? errors.total_years_required.message : JSON.stringify(errors.total_years_required.message)}</span>}
        </div>

        <div className="form-group">
          <label>Job Description *</label>
          <textarea
            {...register('description', { required: 'Job description is required' })}
            placeholder="Enter detailed job description"
            rows="4"
          />
          {errors.description && <span style={{color: 'red'}}>{typeof errors.description.message === 'string' ? errors.description.message : JSON.stringify(errors.description.message)}</span>}
        </div>

        <div className="form-group">
          <label>Mandatory Skills</label>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
            <input
              type="text"
              value={newSkill.skill}
              onChange={(e) => setNewSkill({...newSkill, skill: e.target.value})}
              placeholder="Skill name"
              style={{ flex: 1 }}
            />
            <input
              type="number"
              value={newSkill.min_experience}
              onChange={(e) => setNewSkill({...newSkill, min_experience: e.target.value})}
              placeholder="Min years"
              style={{ width: '100px' }}
            />
            <button 
              type="button" 
              className="btn btn-primary" 
              onClick={addMandatorySkill}
            >
              Add
            </button>
          </div>
          
          {mandatorySkills.length > 0 && (
            <div>
              <strong>Added Skills:</strong>
              <ul>
                {mandatorySkills.map((skill, index) => (
                  <li key={index}>
                    {skill.skill} ({skill.min_experience} years)
                    <button 
                      type="button" 
                      className="btn btn-danger" 
                      onClick={() => removeMandatorySkill(index)}
                      style={{ marginLeft: '10px', padding: '2px 8px' }}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <button 
          type="submit" 
          className="btn btn-primary" 
          disabled={loading}
        >
          {loading ? 'Posting...' : 'Post Job'}
        </button>
      </form>
    </div>
  );
};

export default JobPosting; 