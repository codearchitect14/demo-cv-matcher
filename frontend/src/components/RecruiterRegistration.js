import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './RecruiterRegistration.css';

const RecruiterRegistration = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phoneNumber: '',
    password: '',
    passwordConfirm: '',
    companyName: '',
    domain: '',
    companySize: '',
    companyDescription: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const domains = [
    'IT', 'Healthcare', 'Finance', 'Education', 'Manufacturing',
    'Retail', 'Consulting', 'Media', 'Real Estate', 'Transportation',
    'Energy', 'Telecommunications', 'Other'
  ];

  const companySizes = [
    '1-10', '11-50', '51-200', '201-500', '501-1000', '1000+'
  ];

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

    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters long';
    }

    if (!formData.passwordConfirm) {
      newErrors.passwordConfirm = 'Please confirm your password';
    } else if (formData.password !== formData.passwordConfirm) {
      newErrors.passwordConfirm = 'Passwords do not match';
    }

    if (!formData.companyName.trim()) {
      newErrors.companyName = 'Company name is required';
    }

    if (!formData.domain) {
      newErrors.domain = 'Please select a domain';
    }

    if (!formData.companySize) {
      newErrors.companySize = 'Please select company size';
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
      const response = await fetch('http://localhost:8000/api/v1/recruiter/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: formData.fullName,
          email: formData.email,
          phone_number: formData.phoneNumber || null,
          password: formData.password,
          password_confirm: formData.passwordConfirm,
          company_name: formData.companyName,
          domain: formData.domain,
          company_size: formData.companySize,
          company_description: formData.companyDescription || null
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert('Registration successful! Please login.');
        navigate('/recruiter/login');
      } else {
        const errorData = await response.json();
        alert(`Registration failed: ${typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail)}`);
      }
    } catch (error) {
      console.error('Registration error:', error);
      alert('Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="recruiter-registration">
      <div className="registration-container">
        <div className="registration-header">
          <h1>Recruiter Registration</h1>
          <p>Create your account to start posting jobs and finding talent</p>
        </div>

        <form onSubmit={handleSubmit} className="registration-form">
          <div className="form-section">
            <h2>Basic Account Info</h2>
            
            <div className="form-group">
              <label htmlFor="fullName">Full Name *</label>
              <input
                type="text"
                id="fullName"
                name="fullName"
                value={formData.fullName}
                onChange={handleInputChange}
                className={errors.fullName ? 'error' : ''}
                placeholder="Enter your full name"
              />
              {errors.fullName && <span className="error-message">{typeof errors.fullName === 'string' ? errors.fullName : JSON.stringify(errors.fullName)}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address:</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
                required
                className={errors.email ? 'error' : ''}
              />
              {errors.email && <span className="error-message">{typeof errors.email === 'string' ? errors.email : JSON.stringify(errors.email)}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="phoneNumber">Phone Number (Optional):</label>
              <input
                type="tel"
                id="phoneNumber"
                name="phoneNumber"
                value={formData.phoneNumber}
                onChange={handleInputChange}
                placeholder="Enter your phone number"
              />
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

            <div className="form-group">
              <label htmlFor="passwordConfirm">Confirm Password:</label>
              <input
                type="password"
                id="passwordConfirm"
                name="passwordConfirm"
                value={formData.passwordConfirm}
                onChange={handleInputChange}
                placeholder="Confirm your password"
                required
                className={errors.passwordConfirm ? 'error' : ''}
              />
              {errors.passwordConfirm && <span className="error-message">{typeof errors.passwordConfirm === 'string' ? errors.passwordConfirm : JSON.stringify(errors.passwordConfirm)}</span>}
            </div>
          </div>

          <div className="form-section">
            <h2>Company Information</h2>
            
            <div className="form-group">
              <label htmlFor="companyName">Company Name:</label>
              <input
                type="text"
                id="companyName"
                name="companyName"
                value={formData.companyName}
                onChange={handleInputChange}
                placeholder="Enter company name"
                required
                className={errors.companyName ? 'error' : ''}
              />
              {errors.companyName && <span className="error-message">{typeof errors.companyName === 'string' ? errors.companyName : JSON.stringify(errors.companyName)}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="domain">Domain:</label>
              <select
                id="domain"
                name="domain"
                value={formData.domain}
                onChange={handleInputChange}
                required
                className={errors.domain ? 'error' : ''}
              >
                <option value="">Select Domain</option>
                <option value="IT">IT</option>
                <option value="Healthcare">Healthcare</option>
                <option value="Finance">Finance</option>
                <option value="Education">Education</option>
                <option value="Manufacturing">Manufacturing</option>
                <option value="Retail">Retail</option>
                <option value="Consulting">Consulting</option>
                <option value="Media">Media</option>
                <option value="Real Estate">Real Estate</option>
                <option value="Transportation">Transportation</option>
                <option value="Energy">Energy</option>
                <option value="Telecommunications">Telecommunications</option>
                <option value="Other">Other</option>
              </select>
              {errors.domain && <span className="error-message">{typeof errors.domain === 'string' ? errors.domain : JSON.stringify(errors.domain)}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="companySize">Company Size:</label>
              <select
                id="companySize"
                name="companySize"
                value={formData.companySize}
                onChange={handleInputChange}
                required
                className={errors.companySize ? 'error' : ''}
              >
                <option value="">Select Company Size</option>
                <option value="1-10">1-10 employees</option>
                <option value="11-50">11-50 employees</option>
                <option value="51-200">51-200 employees</option>
                <option value="201-500">201-500 employees</option>
                <option value="501-1000">501-1000 employees</option>
                <option value="1000+">1000+ employees</option>
              </select>
              {errors.companySize && <span className="error-message">{typeof errors.companySize === 'string' ? errors.companySize : JSON.stringify(errors.companySize)}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="companyDescription">Company Description</label>
              <textarea
                id="companyDescription"
                name="companyDescription"
                value={formData.companyDescription}
                onChange={handleInputChange}
                placeholder="Brief description of your company (optional)"
                rows="4"
              />
            </div>
          </div>

          <div className="form-actions">
            <button 
              type="submit" 
              className="btn-register"
              disabled={isLoading}
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
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

        <div className="login-link">
          <p>Already have an account? <button onClick={() => navigate('/recruiter/login')}>Sign In</button></p>
        </div>
      </div>
    </div>
  );
};

export default RecruiterRegistration; 