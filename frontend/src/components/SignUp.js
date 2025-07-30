import React, { useState } from 'react';
import { apiService } from '../api';

const SignUp = ({ onSignUpSuccess, onSwitchToSignIn }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    location: '',
    domain: '',
    expected_salary_min: '',
    expected_salary_max: '',
    summary: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validate form data
      if (!formData.name || !formData.email || !formData.password) {
        throw new Error('Please fill in all required fields');
      }

      if (formData.expected_salary_min && formData.expected_salary_max) {
        if (parseInt(formData.expected_salary_min) > parseInt(formData.expected_salary_max)) {
          throw new Error('Minimum salary cannot be greater than maximum salary');
        }
      }

      const response = await apiService.register(formData);
      
      // Show success message and redirect to sign in
      alert('Registration successful! Please sign in with your credentials.');
      onSwitchToSignIn();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Sign Up</h2>
        <p className="auth-subtitle">Create your account to get started</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="name">Full Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder="Enter your full name"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter your email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password *</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
              minLength="6"
            />
          </div>

          <div className="form-group">
            <label htmlFor="location">Location *</label>
            <input
              type="text"
              id="location"
              name="location"
              value={formData.location}
              onChange={handleChange}
              required
              placeholder="Enter your location"
            />
          </div>

          <div className="form-group">
            <label htmlFor="domain">Domain *</label>
            <input
              type="text"
              id="domain"
              name="domain"
              value={formData.domain}
              onChange={handleChange}
              required
              placeholder="e.g., Data Science, Software Engineering"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="expected_salary_min">Min Salary</label>
              <input
                type="number"
                id="expected_salary_min"
                name="expected_salary_min"
                value={formData.expected_salary_min}
                onChange={handleChange}
                placeholder="Min salary"
                min="0"
              />
            </div>

            <div className="form-group">
              <label htmlFor="expected_salary_max">Max Salary</label>
              <input
                type="number"
                id="expected_salary_max"
                name="expected_salary_max"
                value={formData.expected_salary_max}
                onChange={handleChange}
                placeholder="Max salary"
                min="0"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="summary">Professional Summary *</label>
            <textarea
              id="summary"
              name="summary"
              value={formData.summary}
              onChange={handleChange}
              required
              placeholder="Brief description of your experience and skills"
              rows="4"
            />
          </div>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <button 
              type="button" 
              className="link-button"
              onClick={onSwitchToSignIn}
            >
              Sign In
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignUp; 