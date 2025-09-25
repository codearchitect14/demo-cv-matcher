import React, { useState } from 'react';

const MCQTemplatesModal = ({ onApplyTemplate }) => {
  const [showModal, setShowModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('');

  // Pre-built MCQ templates for common roles
  const templates = {
    'software-engineer': {
      name: 'Software Engineer',
      description: 'General programming, algorithms, and software development concepts',
      mcqs: [
        {
          question: 'What is the time complexity of binary search?',
          options: { A: 'O(1)', B: 'O(log n)', C: 'O(n)', D: 'O(n²)' },
          correct: 'B'
        },
        {
          question: 'Which data structure uses LIFO (Last In, First Out) principle?',
          options: { A: 'Queue', B: 'Stack', C: 'Array', D: 'Linked List' },
          correct: 'B'
        },
        {
          question: 'What does REST stand for in RESTful APIs?',
          options: { A: 'Representational State Transfer', B: 'Remote State Transfer', C: 'Representational Software Transfer', D: 'Remote Software Transfer' },
          correct: 'A'
        },
        {
          question: 'Which programming paradigm does JavaScript primarily follow?',
          options: { A: 'Procedural', B: 'Functional', C: 'Object-Oriented', D: 'All of the above' },
          correct: 'D'
        },
        {
          question: 'What is the purpose of version control systems like Git?',
          options: { A: 'To compile code', B: 'To track changes in code over time', C: 'To debug applications', D: 'To deploy applications' },
          correct: 'B'
        }
      ]
    },
    'data-scientist': {
      name: 'Data Scientist',
      description: 'Statistics, machine learning, and data analysis concepts',
      mcqs: [
        {
          question: 'What is the difference between supervised and unsupervised learning?',
          options: { A: 'Supervised uses labeled data, unsupervised uses unlabeled data', B: 'Supervised is faster than unsupervised', C: 'Unsupervised is more accurate', D: 'No difference' },
          correct: 'A'
        },
        {
          question: 'Which metric is used to evaluate classification models?',
          options: { A: 'Mean Absolute Error', B: 'R-squared', C: 'Accuracy', D: 'All of the above' },
          correct: 'C'
        },
        {
          question: 'What is overfitting in machine learning?',
          options: { A: 'Model performs well on training data but poorly on test data', B: 'Model is too simple', C: 'Model has too few parameters', D: 'Model is too fast' },
          correct: 'A'
        },
        {
          question: 'What does SQL stand for?',
          options: { A: 'Structured Query Language', B: 'Simple Query Language', C: 'Standard Query Language', D: 'System Query Language' },
          correct: 'A'
        },
        {
          question: 'Which statistical test is used to compare means of two groups?',
          options: { A: 'Chi-square test', B: 't-test', C: 'ANOVA', D: 'Correlation test' },
          correct: 'B'
        }
      ]
    },
    'product-manager': {
      name: 'Product Manager',
      description: 'Product strategy, user experience, and business concepts',
      mcqs: [
        {
          question: 'What is the primary goal of a Product Manager?',
          options: { A: 'To write code', B: 'To manage engineering teams', C: 'To build products that solve user problems', D: 'To handle customer support' },
          correct: 'C'
        },
        {
          question: 'What does MVP stand for?',
          options: { A: 'Most Valuable Player', B: 'Minimum Viable Product', C: 'Maximum Value Proposition', D: 'Most Valuable Product' },
          correct: 'B'
        },
        {
          question: 'Which framework is commonly used for user story writing?',
          options: { A: 'As a [user], I want [goal] so that [benefit]', B: 'User + Action + Result', C: 'Problem + Solution + Impact', D: 'All of the above' },
          correct: 'A'
        },
        {
          question: 'What is A/B testing used for?',
          options: { A: 'To compare two versions of a feature', B: 'To test server performance', C: 'To debug applications', D: 'To deploy code' },
          correct: 'A'
        },
        {
          question: 'What is the primary purpose of user research?',
          options: { A: 'To validate assumptions about users', B: 'To write better code', C: 'To increase server capacity', D: 'To reduce costs' },
          correct: 'A'
        }
      ]
    },
    'frontend-developer': {
      name: 'Frontend Developer',
      description: 'HTML, CSS, JavaScript, and web development concepts',
      mcqs: [
        {
          question: 'What does CSS stand for?',
          options: { A: 'Computer Style Sheets', B: 'Cascading Style Sheets', C: 'Creative Style Sheets', D: 'Colorful Style Sheets' },
          correct: 'B'
        },
        {
          question: 'Which HTML tag is used to create a hyperlink?',
          options: { A: '<link>', B: '<a>', C: '<href>', D: '<url>' },
          correct: 'B'
        },
        {
          question: 'What is the purpose of JavaScript frameworks like React?',
          options: { A: 'To style web pages', B: 'To build interactive user interfaces', C: 'To create databases', D: 'To manage servers' },
          correct: 'B'
        },
        {
          question: 'What does DOM stand for?',
          options: { A: 'Document Object Model', B: 'Data Object Management', C: 'Dynamic Object Method', D: 'Document Order Management' },
          correct: 'A'
        },
        {
          question: 'Which CSS property is used to change text color?',
          options: { A: 'text-color', B: 'font-color', C: 'color', D: 'text-style' },
          correct: 'C'
        }
      ]
    },
    'devops-engineer': {
      name: 'DevOps Engineer',
      description: 'Infrastructure, deployment, and system administration concepts',
      mcqs: [
        {
          question: 'What does CI/CD stand for?',
          options: { A: 'Continuous Integration/Continuous Deployment', B: 'Code Integration/Code Deployment', C: 'Central Integration/Central Deployment', D: 'Complete Integration/Complete Deployment' },
          correct: 'A'
        },
        {
          question: 'Which tool is commonly used for containerization?',
          options: { A: 'VirtualBox', B: 'Docker', C: 'VMware', D: 'Hyper-V' },
          correct: 'B'
        },
        {
          question: 'What is the purpose of Infrastructure as Code (IaC)?',
          options: { A: 'To write application code', B: 'To manage infrastructure using code', C: 'To debug applications', D: 'To test user interfaces' },
          correct: 'B'
        },
        {
          question: 'Which cloud provider offers AWS?',
          options: { A: 'Microsoft', B: 'Google', C: 'Amazon', D: 'IBM' },
          correct: 'C'
        },
        {
          question: 'What is the primary goal of monitoring in DevOps?',
          options: { A: 'To write better code', B: 'To track system performance and health', C: 'To design user interfaces', D: 'To manage databases' },
          correct: 'B'
        }
      ]
    }
  };

  const handleApplyTemplate = () => {
    if (selectedTemplate && templates[selectedTemplate]) {
      onApplyTemplate(templates[selectedTemplate].mcqs);
      setShowModal(false);
      setSelectedTemplate('');
    }
  };

  return (
    <>
      <button 
        className="btn btn-secondary"
        onClick={() => setShowModal(true)}
        style={{
          background: '#10b981',
          color: 'white',
          padding: '8px 16px',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '0.875rem',
          fontWeight: '500',
          marginRight: '10px'
        }}
      >
        📋 Use Template
      </button>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="templates-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Choose MCQ Template</h3>
              <button 
                className="modal-close"
                onClick={() => setShowModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#6b7280'
                }}
              >
                ×
              </button>
            </div>
            
            <div className="modal-content">
              <p>Select a pre-built template for common roles:</p>
              
              <div className="templates-list">
                {Object.entries(templates).map(([key, template]) => (
                  <div key={key} className="template-card">
                    <label className="template-option">
                      <input
                        type="radio"
                        name="template"
                        value={key}
                        checked={selectedTemplate === key}
                        onChange={(e) => setSelectedTemplate(e.target.value)}
                      />
                      <div className="template-info">
                        <h4>{template.name}</h4>
                        <p>{template.description}</p>
                        <span className="question-count">{template.mcqs.length} questions</span>
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowModal(false)}
                style={{
                  background: '#6b7280',
                  color: 'white',
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  marginRight: '10px'
                }}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleApplyTemplate}
                disabled={!selectedTemplate}
                style={{
                  background: selectedTemplate ? '#3b82f6' : '#9ca3af',
                  color: 'white',
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: selectedTemplate ? 'pointer' : 'not-allowed'
                }}
              >
                Apply Template
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .templates-modal {
          background: white;
          border-radius: 12px;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
          max-width: 600px;
          width: 90%;
          max-height: 80vh;
          overflow: hidden;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .modal-header h3 {
          margin: 0;
          color: #1f2937;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .modal-content {
          padding: 20px;
          max-height: 400px;
          overflow-y: auto;
        }

        .templates-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-top: 15px;
        }

        .template-card {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          overflow: hidden;
          transition: border-color 0.2s;
        }

        .template-card:hover {
          border-color: #3b82f6;
        }

        .template-option {
          display: flex;
          align-items: center;
          padding: 15px;
          cursor: pointer;
          width: 100%;
          margin: 0;
        }

        .template-option input[type="radio"] {
          margin-right: 15px;
          width: 18px;
          height: 18px;
          accent-color: #3b82f6;
        }

        .template-info {
          flex: 1;
        }

        .template-info h4 {
          margin: 0 0 5px 0;
          color: #1f2937;
          font-size: 1rem;
          font-weight: 600;
        }

        .template-info p {
          margin: 0 0 8px 0;
          color: #6b7280;
          font-size: 0.875rem;
          line-height: 1.4;
        }

        .question-count {
          display: inline-block;
          background: #f3f4f6;
          color: #374151;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 500;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          padding: 20px;
          border-top: 1px solid #e5e7eb;
        }
      `}</style>
    </>
  );
};

export default MCQTemplatesModal;
