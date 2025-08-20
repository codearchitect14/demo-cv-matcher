import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './SignUpNew.css';

const SignUpNew = ({ onSwitchToSignIn }) => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
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

  const nextStep = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Validate salary range
    if (parseInt(formData.expected_salary_min) > parseInt(formData.expected_salary_max)) {
      setError('Minimum salary cannot be greater than maximum salary');
      setIsLoading(false);
      return;
    }

    try {
      const requestBody = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        location: formData.location,
        domain: formData.domain,
        expected_salary_min: parseInt(formData.expected_salary_min),
        expected_salary_max: parseInt(formData.expected_salary_max),
        summary: formData.summary
      };

      const response = await fetch('http://localhost:8000/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const data = await response.json();
        // Show success message and automatically navigate to login
        alert('Account created successfully! Please sign in.');
        // Navigate to login page
        navigate('/login-new');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSocialLogin = (provider) => {
    console.log(`${provider} signup clicked`);
  };

  const renderStep1 = () => (
    <div className="form-step">
      <div className="form-group">
        <label className="form-label">Full Name</label>
        <input
          type="text"
          name="name"
          placeholder="Enter your full name"
          value={formData.name}
          onChange={handleChange}
          className="form-input"
          autoComplete="name"
          required
        />
      </div>

      <div className="form-group">
        <label className="form-label">Email Address</label>
        <input
          type="email"
          name="email"
          placeholder="Enter your email address"
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
            autoComplete="new-password"
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
    </div>
  );

  const renderStep2 = () => (
    <div className="form-step">
      <div className="form-group">
        <label className="form-label">Location</label>
        <input
          type="text"
          name="location"
          placeholder="Enter your location (e.g., New York, NY)"
          value={formData.location}
          onChange={handleChange}
          className="form-input"
          autoComplete="off"
          required
        />
      </div>

      <div className="form-group">
        <label className="form-label">Professional Domain</label>
        <input
          type="text"
          name="domain"
          placeholder="Enter your professional domain (e.g., Software Development)"
          value={formData.domain}
          onChange={handleChange}
          className="form-input"
          autoComplete="off"
          required
        />
      </div>

      <div className="salary-range">
        <div className="form-group">
          <label className="form-label">Minimum Salary</label>
          <input
            type="number"
            name="expected_salary_min"
            placeholder="Enter minimum salary"
            value={formData.expected_salary_min}
            onChange={handleChange}
            className="form-input"
            autoComplete="off"
            required
            min="0"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Maximum Salary</label>
          <input
            type="number"
            name="expected_salary_max"
            placeholder="Enter maximum salary"
            value={formData.expected_salary_max}
            onChange={handleChange}
            className="form-input"
            autoComplete="off"
            required
            min="0"
          />
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="form-step">
      <div className="form-group">
        <label className="form-label">Professional Summary</label>
        <textarea
          name="summary"
          placeholder="Tell us about your professional experience, skills, and career goals..."
          value={formData.summary}
          onChange={handleChange}
          className="form-textarea"
          autoComplete="off"
          required
          rows="4"
        />
      </div>
    </div>
  );

  return (
    <div className={`signup-new-container ${isVisible ? 'visible' : ''}`}>
      <div className="signup-new-background">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>
      
      <div className="signup-new-card">
        <div className="signup-new-header">
          <h1 className="signup-new-title">Create your account</h1>
          <p className="signup-new-subtitle">Join thousands of professionals finding their dream jobs</p>
        </div>

        <div className="progress-bar">
          <div className={`progress-step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
            <div className="progress-circle">{currentStep > 1 ? '✓' : '1'}</div>
            <div className="progress-label">Basic Info</div>
          </div>
          <div className={`progress-step ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
            <div className="progress-circle">{currentStep > 2 ? '✓' : '2'}</div>
            <div className="progress-label">Location & Domain</div>
          </div>
          <div className={`progress-step ${currentStep >= 3 ? 'active' : ''}`}>
            <div className="progress-circle">3</div>
            <div className="progress-label">Summary</div>
          </div>
        </div>

        {error && (
          <div className="error-message">
            <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
            <button onClick={() => setError('')}>×</button>
          </div>
        )}

        <form className="signup-new-form" onSubmit={handleSubmit}>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}

          <div className="form-navigation">
            {currentStep > 1 && (
              <button type="button" className="nav-btn nav-btn-secondary" onClick={prevStep}>
                <i className="fas fa-arrow-left"></i> Previous
              </button>
            )}
            
            {currentStep < 3 ? (
              <button type="button" className="nav-btn nav-btn-primary" onClick={nextStep}>
                Next <i className="fas fa-arrow-right"></i>
              </button>
            ) : (
              <button type="submit" className="submit-btn" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <div className="spinner"></div>
                    Creating Account...
                  </>
                ) : (
                  'Create Account'
                )}
              </button>
            )}
          </div>
        </form>

        <div className="social-signup-section">
          <div className="social-signup-title">Or continue with</div>
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

        <div className="signup-new-footer">
          <p>
            Already have an account?{' '}
            <button 
              type="button" 
              className="signin-link" 
              onClick={() => navigate('/login-new')}
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Sign in
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

export default SignUpNew; 