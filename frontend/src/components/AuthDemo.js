import React, { useState } from 'react';
import SignIn from './SignIn';
import SignUp from './SignUp';

const AuthDemo = () => {
  const [currentView, setCurrentView] = useState('signin');

  const handleSignInSuccess = (response) => {
    console.log('Sign in successful:', response);
    alert('Sign in successful! Check console for details.');
  };

  const handleSignUpSuccess = (response) => {
    console.log('Sign up successful:', response);
    alert('Sign up successful! Check console for details.');
  };

  return (
    <div className="auth-demo">
      <div className="demo-header">
        <h1>🚀 Modern Authentication Demo</h1>
        <p>Experience the beautiful new sign-in and sign-up pages</p>
        
        <div className="demo-controls">
          <button 
            className={`demo-button ${currentView === 'signin' ? 'active' : ''}`}
            onClick={() => setCurrentView('signin')}
          >
            Sign In
          </button>
          <button 
            className={`demo-button ${currentView === 'signup' ? 'active' : ''}`}
            onClick={() => setCurrentView('signup')}
          >
            Sign Up
          </button>
        </div>
      </div>

      <div className="demo-content">
        {currentView === 'signin' ? (
          <SignIn 
            onSignInSuccess={handleSignInSuccess}
            onSwitchToSignUp={() => setCurrentView('signup')}
          />
        ) : (
          <SignUp 
            onSignUpSuccess={handleSignUpSuccess}
            onSwitchToSignIn={() => setCurrentView('signin')}
          />
        )}
      </div>

      <div className="demo-features">
        <h3>✨ Features Included:</h3>
        <ul>
          <li>🎨 Glassmorphism design with backdrop blur</li>
          <li>🌊 Smooth animations and transitions</li>
          <li>🎯 Floating labels with focus states</li>
          <li>👁️ Password visibility toggle</li>
          <li>📱 Fully responsive design</li>
          <li>🎨 Modern gradient backgrounds</li>
          <li>⚡ Loading states with spinners</li>
          <li>🔒 Social authentication buttons</li>
          <li>📊 Multi-step signup process</li>
          <li>🎭 Dark mode support</li>
        </ul>
      </div>
    </div>
  );
};

export default AuthDemo; 