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
        <input
          type="text"
          name="name"
          placeholder=" "
          value={formData.name}
          onChange={handleChange}
          className="form-input"
          autoComplete="name"
          required
        />
        <label className="form-label">Full Name</label>
      </div>

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
          autoComplete="new-password"
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
    </div>
  );

  const renderStep2 = () => (
    <div className="form-step">
      <div className="form-group">
        <input
          type="text"
          name="location"
          placeholder=" "
          value={formData.location}
          onChange={handleChange}
          className="form-input"
          autoComplete="off"
          required
        />
        <label className="form-label">Location</label>
      </div>

      <div className="form-group">
        <input
          type="text"
          name="domain"
          placeholder=" "
          value={formData.domain}
          onChange={handleChange}
          className="form-input"
          autoComplete="off"
          required
        />
        <label className="form-label">Professional Domain</label>
      </div>

      <div className="salary-group">
        <div className="form-group salary-input">
          <input
            type="number"
            name="expected_salary_min"
            placeholder=" "
            value={formData.expected_salary_min}
            onChange={handleChange}
            className="form-input"
            autoComplete="off"
            required
            min="0"
          />
          <label className="form-label">Minimum Salary</label>
        </div>

        <div className="form-group salary-input">
          <input
            type="number"
            name="expected_salary_max"
            placeholder=" "
            value={formData.expected_salary_max}
            onChange={handleChange}
            className="form-input"
            autoComplete="off"
            required
            min="0"
          />
          <label className="form-label">Maximum Salary</label>
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="form-step">
      <div className="form-group">
        <textarea
          name="summary"
          placeholder=" "
          value={formData.summary}
          onChange={handleChange}
          className="form-input form-textarea"
          autoComplete="off"
          required
          rows="4"
        />
        <label className="form-label">Professional Summary</label>
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
          <h1 className="signup-new-title">Create your account and start your journey</h1>
        </div>

        <div className="progress-indicator">
          <div className={`progress-step ${currentStep >= 1 ? 'active' : ''}`}>
            <div className="step-number">1</div>
            <div className="step-label">Basic Info</div>
          </div>
          <div className={`progress-step ${currentStep >= 2 ? 'active' : ''}`}>
            <div className="step-number">2</div>
            <div className="step-label">Location & Domain</div>
          </div>
          <div className={`progress-step ${currentStep >= 3 ? 'active' : ''}`}>
            <div className="step-number">3</div>
            <div className="step-label">Summary</div>
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
              <button type="button" className="nav-btn prev-btn" onClick={prevStep}>
                Previous
              </button>
            )}
            
            {currentStep < 3 ? (
              <button type="button" className="nav-btn next-btn" onClick={nextStep}>
                Next
              </button>
            ) : (
              <button type="submit" className="nav-btn submit-btn" disabled={isLoading}>
                {isLoading ? 'Creating Account...' : 'Create Account'}
              </button>
            )}
          </div>
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

        <div className="signup-new-footer">
          <p className="footer-text">
            Already have an account?{' '}
            <button 
              type="button" 
              className="footer-link" 
              onClick={() => navigate('/login-new')}
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignUpNew; 