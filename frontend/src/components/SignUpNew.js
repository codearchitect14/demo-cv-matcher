import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './SignUpNew.css';

const SignUpNew = ({ onSwitchToSignIn }) => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0); // Start with CV upload step
  const [cvUploaded, setCvUploaded] = useState(false);
  const [cvParsing, setCvParsing] = useState(false);
  const [cvFile, setCvFile] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    location: '',
    domain: '',
    expected_salary_min: '',
    expected_salary_max: '',
    summary: '',
    total_experience_years: '',
    skills: [{ name: '', years: '' }]
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

  const handleSkillChange = (index, field, value) => {
    const updatedSkills = [...formData.skills];
    updatedSkills[index][field] = value;
    setFormData({
      ...formData,
      skills: updatedSkills
    });
  };

  const addSkill = () => {
    setFormData({
      ...formData,
      skills: [...formData.skills, { name: '', years: '' }]
    });
  };

  const removeSkill = (index) => {
    if (formData.skills.length > 1) {
      const updatedSkills = formData.skills.filter((_, i) => i !== index);
      setFormData({
        ...formData,
        skills: updatedSkills
      });
    }
  };

  const nextStep = () => {
    if (currentStep < 4) {
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
      // Filter out empty skills
      const skills = formData.skills.filter(skill => skill.name && skill.name.trim() !== '');
      
      const requestBody = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        location: formData.location,
        domain: formData.domain,
        expected_salary_min: parseInt(formData.expected_salary_min),
        expected_salary_max: parseInt(formData.expected_salary_max),
        summary: formData.summary,
        total_experience_years: formData.total_experience_years ? parseInt(formData.total_experience_years) : null,
        skills: skills.length > 0 ? skills.map(skill => ({
          name: skill.name.trim(),
          years: parseInt(skill.years) || 0,
          description: null  // Description is optional for registration
        })) : null
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
        setError(typeof errorData.detail === 'string' ? errorData.detail : 'Registration failed');
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

  const handleCvUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
      setError('Please upload a PDF or Word document');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('File size must be less than 5MB');
      return;
    }

    setCvFile(file);
    setCvParsing(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('cv_file', file);

      const response = await fetch('http://localhost:8000/api/v1/recommendations/cv/parse', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        
        // Auto-fill extractable fields
        const extractedData = data.cv_analysis || {};
        setFormData(prev => ({
          ...prev,
          name: extractedData.name || prev.name,
          email: extractedData.email || prev.email,
          location: extractedData.location || prev.location,
          summary: extractedData.summary || prev.summary,
          total_experience_years: extractedData.total_experience || prev.total_experience_years,
          skills: extractedData.skills && extractedData.skills.length > 0 
            ? extractedData.skills.map(skill => ({ name: skill.skill, years: skill.years }))
            : prev.skills
        }));
        
        setCvUploaded(true);
        setCurrentStep(1); // Move to form step
      } else {
        const errorData = await response.json();
        setError(typeof errorData.detail === 'string' ? errorData.detail : 'Failed to parse CV');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setCvParsing(false);
    }
  };

  const skipCvUpload = () => {
    setCurrentStep(1);
  };

  const renderCvUploadStep = () => (
    <div className="form-step">
      <div className="cv-upload-section">
        <h3 className="cv-upload-title">Quick Registration with CV</h3>
        <p className="cv-upload-description">
          Upload your CV to automatically fill in your details, or skip to fill manually.
        </p>
        
        <div className="cv-upload-area">
          <input
            type="file"
            id="cv-upload"
            accept=".pdf,.doc,.docx"
            onChange={handleCvUpload}
            className="cv-upload-input"
            disabled={cvParsing}
          />
          <label htmlFor="cv-upload" className="cv-upload-label">
            {cvParsing ? (
              <div className="cv-upload-loading">
                <div className="spinner"></div>
                <span>Parsing CV...</span>
              </div>
            ) : (
              <div className="cv-upload-content">
                <div className="cv-upload-icon">📄</div>
                <div className="cv-upload-text">
                  <strong>Upload CV</strong>
                  <span>PDF, DOC, or DOCX (max 5MB)</span>
                </div>
              </div>
            )}
          </label>
        </div>

        {cvFile && (
          <div className="cv-file-info">
            <span>📄 {cvFile.name}</span>
            {cvUploaded && <span className="cv-success">✅ Parsed successfully!</span>}
          </div>
        )}

        <div className="cv-upload-actions">
          <button
            type="button"
            onClick={skipCvUpload}
            className="skip-cv-btn"
            disabled={cvParsing}
          >
            Skip & Fill Manually
          </button>
        </div>
      </div>
    </div>
  );

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
        <label className="form-label">
          Full Name
          {cvUploaded && formData.name && <span className="auto-filled-indicator">(Auto-filled from CV)</span>}
        </label>
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
        <label className="form-label">
          Email Address
          {cvUploaded && formData.email && <span className="auto-filled-indicator">(Auto-filled from CV)</span>}
        </label>
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
        <label className="form-label">
          Location
          {cvUploaded && formData.location && <span className="auto-filled-indicator">(Auto-filled from CV)</span>}
        </label>
      </div>

      <div className="form-group">
        <select
          name="domain"
          value={formData.domain}
          onChange={handleChange}
          className="form-input"
          required
        >
          <option value="">Select Professional Domain</option>
          <option value="IT">IT</option>
          <option value="AI">AI</option>
          <option value="Healthcare">Healthcare</option>
          <option value="Education">Education</option>
          <option value="Retail">Retail</option>
          <option value="Finance">Finance</option>
          <option value="Marketing">Marketing</option>
          <option value="Sales">Sales</option>
          <option value="HR">HR</option>
          <option value="Design">Design</option>
          <option value="Product Management">Product Management</option>
        </select>
        <label className="form-label">Professional Domain</label>
      </div>

      <div className="form-group">
        <input
          type="number"
          name="total_experience_years"
          placeholder=" "
          value={formData.total_experience_years}
          onChange={handleChange}
          className="form-input"
          autoComplete="off"
          required
          min="0"
          max="50"
        />
        <label className="form-label">Total Years of Experience</label>
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
      <h3 style={{ marginBottom: '20px', color: '#333' }}>Add Your Skills</h3>
      {formData.skills.map((skill, index) => (
        <div key={index} style={{ display: 'flex', gap: '10px', marginBottom: '15px', alignItems: 'center' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <input
              type="text"
              placeholder=" "
              value={skill.name}
              onChange={(e) => handleSkillChange(index, 'name', e.target.value)}
              className="form-input"
              required={index === 0}
            />
            <label className="form-label">Skill Name (e.g., Python)</label>
          </div>
          <div className="form-group" style={{ width: '120px' }}>
            <input
              type="number"
              placeholder=" "
              value={skill.years}
              onChange={(e) => handleSkillChange(index, 'years', e.target.value)}
              className="form-input"
              required={index === 0}
              min="0"
              max="20"
            />
            <label className="form-label">Years</label>
          </div>
          {formData.skills.length > 1 && (
            <button
              type="button"
              onClick={() => removeSkill(index)}
              style={{
                background: '#dc3545',
                color: 'white',
                border: 'none',
                padding: '12px 16px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Remove
            </button>
          )}
        </div>
      ))}
      <button
        type="button"
        onClick={addSkill}
        style={{
          background: '#28a745',
          color: 'white',
          border: 'none',
          padding: '12px 20px',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '14px',
          marginTop: '10px'
        }}
      >
        + Add Another Skill
      </button>
    </div>
  );

  const renderStep4 = () => (
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
        <label className="form-label">
          Professional Summary
          {cvUploaded && formData.summary && <span className="auto-filled-indicator">(Auto-filled from CV)</span>}
        </label>
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
          <div className={`progress-step ${currentStep >= 0 ? 'active' : ''}`}>
            <div className="step-number">0</div>
            <div className="step-label">CV Upload</div>
          </div>
          <div className={`progress-step ${currentStep >= 1 ? 'active' : ''}`}>
            <div className="step-number">1</div>
            <div className="step-label">Basic Info</div>
          </div>
          <div className={`progress-step ${currentStep >= 2 ? 'active' : ''}`}>
            <div className="step-number">2</div>
            <div className="step-label">Profile</div>
          </div>
          <div className={`progress-step ${currentStep >= 3 ? 'active' : ''}`}>
            <div className="step-number">3</div>
            <div className="step-label">Skills</div>
          </div>
          <div className={`progress-step ${currentStep >= 4 ? 'active' : ''}`}>
            <div className="step-number">4</div>
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
          {currentStep === 0 && renderCvUploadStep()}
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
          {currentStep === 4 && renderStep4()}

          <div className="form-navigation">
            {currentStep > 1 && (
              <button type="button" className="nav-btn prev-btn" onClick={prevStep}>
                Previous
              </button>
            )}
            
            {currentStep === 0 ? (
              // CV upload step - no navigation buttons (handled within the step)
              null
            ) : currentStep < 4 ? (
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