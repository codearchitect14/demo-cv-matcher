import React, { useState, useEffect } from 'react';
import { apiService } from '../api';
import './LoginNew.css';

const LoginNew = ({ onSwitchToSignUp, onSignInSuccess }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
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
        // Use apiService to set token
        apiService.setToken(data.access_token);
        // Call success callback if provided
        if (onSignInSuccess) {
          onSignInSuccess(data);
        } else {
          alert('Login successful!');
        }
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSocialLogin = (provider) => {
    console.log(`${provider} login clicked`);
  };

  return (
    <div className={`login-new-container ${isVisible ? 'visible' : ''}`}>
      <div className="login-new-background">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>
      
      <div className="login-new-card">
        <div className="login-new-header">
          <h1 className="login-new-title">Login here</h1>
          <p className="login-new-subtitle">Welcome back you've been missed!</p>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <form className="login-new-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <input
              type="email"
              name="email"
              placeholder=" "
              value={formData.email}
              onChange={handleChange}
              className="form-input"
              autoComplete="email"
              required
            />
            <label className="form-label">Email Address</label>
          </div>

          <div className="form-group">
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              placeholder=" "
              value={formData.password}
              onChange={handleChange}
              className="form-input"
              autoComplete="current-password"
              required
            />
            <label className="form-label">Password</label>
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? "Show" : "Hide"}
            </button>
          </div>

          <div className="forgot-password">
            <button 
              type="button" 
              className="forgot-link"
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Forgot your password?
            </button>
          </div>

          <button type="submit" className="login-new-btn" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <div className="divider">
          <span className="divider-text">Or continue with</span>
        </div>

        <div className="social-login">
          <button
            className="social-btn google"
            onClick={() => handleSocialLogin('Google')}
          >
            <span className="social-icon">G</span>
          </button>
          <button
            className="social-btn facebook"
            onClick={() => handleSocialLogin('Facebook')}
          >
            <span className="social-icon">f</span>
          </button>
          <button
            className="social-btn apple"
            onClick={() => handleSocialLogin('Apple')}
          >
            <span className="social-icon">A</span>
          </button>
        </div>

        <div className="login-new-footer">
          <p className="footer-text">
            Don't have an account?{' '}
            <button 
              type="button" 
              className="footer-link" 
              onClick={onSwitchToSignUp}
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginNew; 