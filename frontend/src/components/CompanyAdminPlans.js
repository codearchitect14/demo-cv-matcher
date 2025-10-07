import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const CompanyAdminPlans = () => {
  const navigate = useNavigate();
  const [availablePlans, setAvailablePlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const token = localStorage.getItem('recruiterToken');

  useEffect(() => {
    if (!token) {
      navigate('/recruiter-login');
      return;
    }
    fetchAvailablePlans();
    fetchCurrentSubscription();
  }, [token, navigate]);

  const fetchAvailablePlans = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/company-admin/subscriptions/available-plans', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setAvailablePlans(data);
      } else if (res.status === 403) {
        setError('Only company admins can view subscription plans');
      }
    } catch (e) {
      console.error('Failed to fetch plans:', e);
      setError('Failed to load plans');
    }
  };

  const fetchCurrentSubscription = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/company-admin/subscriptions/my-subscription', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        if (!data.message) {
          setCurrentSubscription(data);
        }
      }
    } catch (e) {
      console.error('Failed to fetch subscription:', e);
    } finally {
      setLoading(false);
    }
  };

  const requestPlan = async (plan) => {
    if (!window.confirm(`Request ${plan.plan_name} plan ($${plan.price}/month)?\n\nThis will be sent to Super Admin for approval.`)) return;

    try {
      const res = await fetch('http://localhost:8000/api/v1/company-admin/subscriptions/request-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ offer_plan_id: plan.id })
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Request failed');
      }

      const data = await res.json();
      alert(`✅ ${plan.plan_name} request sent to Super Admin!\n\nYou'll receive an email when it's approved.`);
      await fetchCurrentSubscription();
    } catch (e) {
      alert('❌ ' + (e.message || 'Failed to request plan'));
    }
  };

  if (loading) {
    return (
      <div style={{padding: 40, textAlign: 'center'}}>
        <div style={{fontSize: 18}}>Loading subscription plans...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{padding: 40, textAlign: 'center', color: '#ef4444'}}>
        <div style={{fontSize: 18, marginBottom: 16}}>{error}</div>
        <button onClick={() => navigate('/recruiter/dashboard')}>Back to Dashboard</button>
      </div>
    );
  }

  return (
    <div style={{padding: 24, background: '#f8fafc', minHeight: '100vh'}}>
      {/* Header */}
      <div style={{marginBottom: 32}}>
        <button 
          onClick={() => navigate('/recruiter/dashboard')}
          style={{
            background: 'none',
            border: 'none',
            color: '#3b82f6',
            cursor: 'pointer',
            fontSize: 14,
            marginBottom: 16
          }}
        >
          ← Back to Dashboard
        </button>
        <h1 style={{margin: '0 0 8px 0', fontSize: 32, fontWeight: 'bold'}}>Subscription Plans</h1>
        <p style={{margin: 0, color: '#6b7280'}}>Choose the perfect plan for your company</p>
      </div>

      {/* Current Subscription Status */}
      {currentSubscription && (
        <div style={{
          background: currentSubscription.status === 'Active' ? '#d1fae5' : '#fef3c7',
          border: `2px solid ${currentSubscription.status === 'Active' ? '#10b981' : '#f59e0b'}`,
          borderRadius: 12,
          padding: 20,
          marginBottom: 32
        }}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div>
              <h3 style={{margin: '0 0 8px 0', color: '#1f2937'}}>Current Subscription</h3>
              <p style={{margin: 0, fontSize: 18, fontWeight: 'bold', color: currentSubscription.status === 'Active' ? '#059669' : '#d97706'}}>
                {currentSubscription.plan_name} - ${currentSubscription.price}/month
              </p>
              <p style={{margin: '8px 0 0 0', fontSize: 14, color: '#6b7280'}}>
                Status: <strong>{currentSubscription.status}</strong>
                {currentSubscription.status === 'Pending' && ' (Awaiting Super Admin Approval)'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Plan Cards Grid */}
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 24}}>
        {availablePlans.map((plan) => {
          const isCurrentPlan = currentSubscription && currentSubscription.offer_plan_id === plan.id;
          const isPending = currentSubscription && currentSubscription.status === 'Pending';
          
          return (
            <div
              key={plan.id}
              style={{
                border: isCurrentPlan ? '3px solid #8b5cf6' : '2px solid #e5e7eb',
                borderRadius: 16,
                padding: 28,
                background: 'white',
                boxShadow: isCurrentPlan ? '0 8px 24px rgba(139, 92, 246, 0.15)' : '0 2px 8px rgba(0,0,0,0.05)',
                position: 'relative',
                transition: 'all 0.3s'
              }}
            >
              {/* Recommended Badge */}
              {plan.plan_name.toLowerCase().includes('gold') && (
                <div style={{
                  position: 'absolute',
                  top: -12,
                  right: 20,
                  background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                  color: 'white',
                  padding: '6px 16px',
                  borderRadius: 20,
                  fontSize: 12,
                  fontWeight: 600
                }}>
                  RECOMMENDED
                </div>
              )}

              {/* Plan Header */}
              <div style={{marginBottom: 24, textAlign: 'center'}}>
                <div style={{
                  fontSize: 24,
                  fontWeight: 'bold',
                  color: '#1f2937',
                  marginBottom: 8
                }}>
                  {plan.plan_name}
                </div>
                <div style={{fontSize: 48, fontWeight: 'bold', color: '#8b5cf6'}}>
                  ${plan.price}
                  <span style={{fontSize: 18, color: '#6b7280', fontWeight: 400}}>/month</span>
                </div>
              </div>

              {/* Features List */}
              <div style={{marginBottom: 24}}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px 0',
                  borderBottom: '1px solid #f3f4f6'
                }}>
                  <span style={{fontSize: 18, color: '#10b981', marginRight: 12}}>✓</span>
                  <span style={{fontSize: 15, color: '#374151', fontWeight: 500}}>
                    {plan.job_post_limit ? `${plan.job_post_limit} Job Posts` : '∞ Unlimited Job Posts'}
                  </span>
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px 0',
                  borderBottom: '1px solid #f3f4f6'
                }}>
                  <span style={{fontSize: 18, color: '#10b981', marginRight: 12}}>✓</span>
                  <span style={{fontSize: 15, color: '#374151', fontWeight: 500}}>
                    {plan.recruiter_limit} Recruiter{plan.recruiter_limit > 1 ? 's' : ''}
                  </span>
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px 0',
                  borderBottom: '1px solid #f3f4f6'
                }}>
                  <span style={{fontSize: 18, color: '#10b981', marginRight: 12}}>✓</span>
                  <span style={{fontSize: 15, color: '#374151', fontWeight: 500}}>
                    {plan.candidate_views ? `${plan.candidate_views.toLocaleString()} Candidate Views` : '∞ Unlimited Views'}
                  </span>
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px 0',
                  borderBottom: '1px solid #f3f4f6'
                }}>
                  <span style={{fontSize: 18, color: '#10b981', marginRight: 12}}>✓</span>
                  <span style={{fontSize: 15, color: '#374151', fontWeight: 500}}>
                    {plan.analytics_level} Analytics
                  </span>
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px 0'
                }}>
                  <span style={{fontSize: 18, color: '#10b981', marginRight: 12}}>✓</span>
                  <span style={{fontSize: 15, color: '#374151', fontWeight: 500}}>
                    {plan.support_level}
                  </span>
                </div>
              </div>

              {/* Action Button */}
              {isCurrentPlan && currentSubscription.status === 'Active' ? (
                <button
                  disabled
                  style={{
                    width: '100%',
                    background: '#10b981',
                    color: 'white',
                    border: 'none',
                    padding: '14px',
                    borderRadius: 10,
                    fontSize: 15,
                    fontWeight: 600,
                    cursor: 'not-allowed',
                    opacity: 0.8
                  }}
                >
                  ✓ Current Plan
                </button>
              ) : isCurrentPlan && currentSubscription.status === 'Pending' ? (
                <button
                  disabled
                  style={{
                    width: '100%',
                    background: '#f59e0b',
                    color: 'white',
                    border: 'none',
                    padding: '14px',
                    borderRadius: 10,
                    fontSize: 15,
                    fontWeight: 600,
                    cursor: 'not-allowed',
                    opacity: 0.8
                  }}
                >
                  ⏳ Pending Approval
                </button>
              ) : isPending ? (
                <button
                  disabled
                  style={{
                    width: '100%',
                    background: '#6b7280',
                    color: 'white',
                    border: 'none',
                    padding: '14px',
                    borderRadius: 10,
                    fontSize: 15,
                    fontWeight: 600,
                    cursor: 'not-allowed',
                    opacity: 0.6
                  }}
                >
                  Request Pending
                </button>
              ) : (
                <button
                  onClick={() => requestPlan(plan)}
                  style={{
                    width: '100%',
                    background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                    color: 'white',
                    border: 'none',
                    padding: '14px',
                    borderRadius: 10,
                    fontSize: 15,
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'transform 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                  onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                >
                  Request This Plan
                </button>
              )}
            </div>
          );
        })}
      </div>

      {availablePlans.length === 0 && !loading && (
        <div style={{textAlign: 'center', padding: 60, color: '#6b7280'}}>
          <p style={{fontSize: 18}}>No subscription plans available at the moment.</p>
          <p style={{fontSize: 14}}>Please contact support for more information.</p>
        </div>
      )}

      {/* Info Box */}
      <div style={{
        marginTop: 40,
        background: 'white',
        borderRadius: 12,
        padding: 24,
        border: '1px solid #e5e7eb'
      }}>
        <h3 style={{margin: '0 0 16px 0', color: '#1f2937'}}>How It Works</h3>
        <ol style={{margin: 0, paddingLeft: 20, color: '#6b7280'}}>
          <li style={{marginBottom: 8}}>Select a subscription plan that fits your needs</li>
          <li style={{marginBottom: 8}}>Click "Request This Plan" - your request will be sent to Super Admin</li>
          <li style={{marginBottom: 8}}>Wait for Super Admin approval (you'll receive an email notification)</li>
          <li>Once approved, you'll have full access to all plan features!</li>
        </ol>
      </div>
    </div>
  );
};

export default CompanyAdminPlans;

