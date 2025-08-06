import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './RecruiterLogin.css';

const RecruiterLogin = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/recruiter/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        }),
      });

      if (response.ok) {
        const data = await response.json();
        // Store token and user info
        localStorage.setItem('recruiterToken', data.access_token);
        localStorage.setItem('recruiterUser', JSON.stringify(data.user));
        alert('Login successful!');
        navigate('/recruiter/dashboard');
      } else {
        const errorData = await response.json();
        alert(`Login failed: ${typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail)}`);
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="recruiter-login">
      <div className="login-container">
        <div className="login-header">
          <h1>Recruiter Login</h1>
          <p>Welcome back! Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className={errors.email ? 'error' : ''}
              placeholder="Enter your email address"
            />
            {errors.email && <span className="error-message">{typeof errors.email === 'string' ? errors.email : JSON.stringify(errors.email)}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password:</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="Enter your password"
              required
              className={errors.password ? 'error' : ''}
            />
            {errors.password && <span className="error-message">{typeof errors.password === 'string' ? errors.password : JSON.stringify(errors.password)}</span>}
          </div>

          <div className="form-actions">
            <button 
              type="submit" 
              className="btn-login"
              disabled={isLoading}
            >
              {isLoading ? 'Signing In...' : 'Sign In'}
            </button>
            
            <button 
              type="button" 
              className="btn-back"
              onClick={() => navigate('/')}
            >
              ← Back to Welcome
            </button>
          </div>
        </form>

        <div className="register-link">
          <p>Don't have an account? <button onClick={() => navigate('/recruiter/register')}>Register</button></p>
        </div>
      </div>
    </div>
  );
};

export default RecruiterLogin; 