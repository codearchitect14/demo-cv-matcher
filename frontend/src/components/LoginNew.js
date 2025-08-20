import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../api';
import './LoginNew.css';

const LoginNew = ({ onSwitchToSignUp, onSignInSuccess }) => {
  const navigate = useNavigate();
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
        console.log('=== LOGIN SUCCESS ===');
        console.log('Login response:', data);
        
        // Use apiService to set token
        apiService.setToken(data.access_token);
        console.log('Token set in localStorage:', localStorage.getItem('access_token'));
        
        // Call success callback if provided
        if (onSignInSuccess) {
          console.log('Calling onSignInSuccess callback');
          onSignInSuccess(data);
        } else {
          // Navigate to candidates dashboard after successful login
          console.log('Navigating to /candidates-dashboard');
          try {
            navigate('/candidates-dashboard');
            console.log('Navigation successful');
          } catch (navError) {
            console.error('Navigation failed:', navError);
            // Fallback: try to redirect manually
            window.location.href = '/candidates-dashboard';
          }
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
            <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
            <button onClick={() => setError('')}>×</button>
          </div>
        )}

        <form className="login-new-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              className="form-input"
              autoComplete="email"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div className="password-input-container">
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
                className="form-input"
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <i className="fas fa-eye-slash"></i> : <i className="fas fa-eye"></i>}
              </button>
            </div>
          </div>

          <button type="submit" className="login-submit-btn" disabled={isLoading}>
            {isLoading ? (
              <>
                <div className="spinner"></div>
                Signing in...
              </>
            ) : (
              'Sign in'
            )}
          </button>
        </form>

        <div className="social-login-section">
          <div className="social-login-title">Or continue with</div>
          <div className="social-buttons">
            <button
              className="social-btn google"
              onClick={() => handleSocialLogin('Google')}
            >
              <i className="fab fa-google"></i>
              Google
            </button>
            <button
              className="social-btn linkedin"
              onClick={() => handleSocialLogin('LinkedIn')}
            >
              <i className="fab fa-linkedin"></i>
              LinkedIn
            </button>
          </div>
        </div>

        <div className="login-new-footer">
          <p>
            Don't have an account?{' '}
            <button 
              type="button" 
              className="signup-link" 
              onClick={() => navigate('/signup-new')}
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Sign up
            </button>
          </p>
          <a href="/" className="back-link">
            <i className="fas fa-arrow-left"></i> Back to home
          </a>
        </div>
      </div>
    </div>
  );
};

export default LoginNew; 