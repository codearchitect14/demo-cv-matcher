import React from 'react';
import { useNavigate } from 'react-router-dom';

const Unauthorized = () => {
  const navigate = useNavigate();

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif'
    }}>
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        borderRadius: '16px',
        padding: '40px',
        textAlign: 'center',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        maxWidth: '500px',
        width: '90%'
      }}>
        <div style={{
          fontSize: '64px',
          marginBottom: '20px'
        }}>
          🚫
        </div>
        <h1 style={{
          margin: '0 0 16px 0',
          fontSize: '28px',
          fontWeight: '700',
          color: '#1f2937'
        }}>
          Access Denied
        </h1>
        <p style={{
          margin: '0 0 24px 0',
          color: '#6b7280',
          fontSize: '16px',
          lineHeight: '1.5'
        }}>
          You don't have permission to access this page. This area is restricted to authorized sub-recruiters only.
        </p>
        <button
          onClick={() => navigate('/')}
          style={{
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            padding: '12px 24px',
            fontSize: '16px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = '#2563eb';
            e.target.style.transform = 'translateY(-1px)';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = '#3b82f6';
            e.target.style.transform = 'translateY(0)';
          }}
        >
          Go to Home
        </button>
      </div>
    </div>
  );
};

export default Unauthorized;
