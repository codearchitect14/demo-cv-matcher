import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import EnhancedNavigation from './EnhancedNavigation';
import './EnhancedTestPage.css';

const EnhancedTestPage = () => {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState('overview');

  const features = [
    {
      title: "🔍 Enhanced CV Parsing",
      description: "Advanced CV parsing with NER, skill extraction, and experience duration calculation",
      features: [
        "Named Entity Recognition (NER) for skill extraction",
        "Date parsing for experience duration calculation",
        "Company and role context analysis",
        "Skill-to-role mapping with experience estimation",
        "Multi-format support (PDF, DOCX)"
      ],
      route: "/enhanced-candidate-recommendations"
    },
    {
      title: "🎯 Skill-Specific Matching",
      description: "Precise skill matching with experience validation and semantic similarity",
      features: [
        "Skill taxonomy with aliases and hierarchies",
        "Semantic similarity for skill matching",
        "Experience requirement validation",
        "Skill normalization and matching",
        "Proficiency level assessment"
      ],
      route: "/enhanced-recruiter-recommendations"
    },
    {
      title: "📊 Enhanced Recommendations",
      description: "Detailed recommendations with skill breakdowns and match explanations",
      features: [
        "Skill-specific experience validation",
        "Detailed match explanations",
        "Experience gap analysis",
        "Strength identification",
        "Interactive feedback system"
      ],
      route: "/enhanced-candidate-recommendations"
    },
    {
      title: "🔄 Feedback Loop System",
      description: "Continuous improvement through user feedback and model performance tracking",
      features: [
        "User feedback collection",
        "Model performance metrics",
        "Feedback insights and analytics",
        "Prediction probability estimation",
        "Continuous learning system"
      ],
      route: "/interactions-analytics"
    }
  ];

  const testScenarios = [
    {
      title: "Candidate CV Upload Test",
      description: "Upload a CV and get skill-specific job recommendations",
      steps: [
        "1. Navigate to Enhanced Candidate Recommendations",
        "2. Upload a CV file (PDF/DOCX)",
        "3. View parsed skills and experience",
        "4. Get personalized job recommendations",
        "5. Review skill-specific match details"
      ],
      route: "/enhanced-candidate-recommendations"
    },
    {
      title: "Recruiter Candidate Search Test",
      description: "Find candidates for a job with skill-specific requirements",
      steps: [
        "1. Navigate to Enhanced Recruiter Recommendations",
        "2. Enter a job ID with skill requirements",
        "3. View matching candidates",
        "4. Review skill validation results",
        "5. Analyze experience gaps and strengths"
      ],
      route: "/enhanced-recruiter-recommendations"
    },
    {
      title: "Skill Matching Test",
      description: "Test semantic skill matching and validation",
      steps: [
        "1. Use the skill matching API",
        "2. Test skill normalization",
        "3. Validate experience requirements",
        "4. Review semantic similarity scores",
        "5. Check proficiency level assessment"
      ],
      route: "/enhanced-candidate-recommendations"
    }
  ];

  return (
    <div className="enhanced-test-page">
      <EnhancedNavigation />
      
      <div className="main-content">
        <div className="page-header">
          <h1>🧪 Enhanced Recommendation System Test</h1>
          <p>Test the advanced CV matching and skill-specific recommendation features</p>
        </div>

        <div className="content-tabs">
          <button 
            className={`tab-button ${activeSection === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveSection('overview')}
          >
            📋 Overview
          </button>
          <button 
            className={`tab-button ${activeSection === 'features' ? 'active' : ''}`}
            onClick={() => setActiveSection('features')}
          >
            ⚡ Features
          </button>
          <button 
            className={`tab-button ${activeSection === 'testing' ? 'active' : ''}`}
            onClick={() => setActiveSection('testing')}
          >
            🧪 Testing
          </button>
        </div>

        {activeSection === 'overview' && (
          <div className="overview-section">
            <div className="overview-card">
              <h2>🎯 System Overview</h2>
              <p>The Enhanced Recommendation System provides advanced CV parsing and skill-specific matching capabilities:</p>
              
              <div className="overview-grid">
                <div className="overview-item">
                  <h3>🔍 CV Parsing</h3>
                  <p>Advanced parsing with NER, skill extraction, and experience duration calculation</p>
                </div>
                <div className="overview-item">
                  <h3>🎯 Skill Matching</h3>
                  <p>Semantic similarity and skill taxonomy for precise matching</p>
                </div>
                <div className="overview-item">
                  <h3>📊 Recommendations</h3>
                  <p>Detailed recommendations with skill breakdowns and explanations</p>
                </div>
                <div className="overview-item">
                  <h3>🔄 Feedback Loop</h3>
                  <p>Continuous improvement through user feedback and analytics</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeSection === 'features' && (
          <div className="features-section">
            <div className="features-grid">
              {features.map((feature, index) => (
                <div key={index} className="feature-card">
                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                  <ul>
                    {feature.features.map((item, itemIndex) => (
                      <li key={itemIndex}>{item}</li>
                    ))}
                  </ul>
                  <button 
                    className="btn-test-feature"
                    onClick={() => navigate(feature.route)}
                  >
                    Test This Feature
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeSection === 'testing' && (
          <div className="testing-section">
            <div className="testing-grid">
              {testScenarios.map((scenario, index) => (
                <div key={index} className="test-scenario-card">
                  <h3>{scenario.title}</h3>
                  <p>{scenario.description}</p>
                  <div className="test-steps">
                    {scenario.steps.map((step, stepIndex) => (
                      <div key={stepIndex} className="test-step">
                        {step}
                      </div>
                    ))}
                  </div>
                  <button 
                    className="btn-run-test"
                    onClick={() => navigate(scenario.route)}
                  >
                    Run Test
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="quick-actions">
          <h3>🚀 Quick Actions</h3>
          <div className="action-buttons">
            <button 
              className="action-btn primary"
              onClick={() => navigate('/enhanced-candidate-recommendations')}
            >
              📄 Upload CV & Test
            </button>
            <button 
              className="action-btn secondary"
              onClick={() => navigate('/enhanced-recruiter-recommendations')}
            >
              👥 Find Candidates
            </button>
            <button 
              className="action-btn tertiary"
              onClick={() => navigate('/interactions-analytics')}
            >
              📊 View Analytics
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedTestPage; 