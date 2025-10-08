import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Card = ({ title, value }) => (
  <div style={{flex: 1, background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.05)'}}>
    <div style={{fontSize: 12, color: '#6b7280'}}>{title}</div>
    <div style={{fontSize: 24, fontWeight: 700}}>{value}</div>
  </div>
);

const Section = ({ title, children }) => (
  <div style={{marginTop: 24}}>
    <div style={{fontSize: 16, fontWeight: 600, marginBottom: 12}}>{title}</div>
    <div style={{background: '#fff', border: '1px solid #eee', borderRadius: 8}}>
      {children}
    </div>
  </div>
);

const SuperAdminDashboard = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('superAdminToken');
  const user = JSON.parse(localStorage.getItem('superAdminUser') || '{}');
  const [overview, setOverview] = useState({ companies: 0, recruiters: 0, candidates: 0, jobs: 0, applications: 0 });
  const [companies, setCompanies] = useState([]);
  const [companySearch, setCompanySearch] = useState('');
  const [showCompanyModal, setShowCompanyModal] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);
  const [companyForm, setCompanyForm] = useState({ name: '', domain: '', description: '', subscription_plan: 'basic', is_active: true });
  const [activeStatusFilter, setActiveStatusFilter] = useState('ALL');
  const [showCompanyDetails, setShowCompanyDetails] = useState(false);
  const [selectedCompanyDetails, setSelectedCompanyDetails] = useState(null);
  const [admins, setAdmins] = useState([]);
  const [error, setError] = useState('');
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [editingAdmin, setEditingAdmin] = useState(null);
  const [adminForm, setAdminForm] = useState({ full_name: '', email: '', phone_number: '', password: '', role: 'admin' });
  const [companyAdmins, setCompanyAdmins] = useState([]);
  const [showCompanyAdmins, setShowCompanyAdmins] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [offerPlans, setOfferPlans] = useState([]);
  const [showOfferPlanModal, setShowOfferPlanModal] = useState(false);
  const [editingOfferPlan, setEditingOfferPlan] = useState(null);
  const [offerPlanForm, setOfferPlanForm] = useState({
    plan_name: '',
    price: 0,
    job_post_limit: '',
    recruiter_limit: 1,
    candidate_views: '',
    analytics_level: 'Basic',
    support_level: '',
    status: 'Active'
  });
  const [activeTab, setActiveTab] = useState('companies');
  const [subscriptions, setSubscriptions] = useState([]);
  const [subscriptionLoading, setSubscriptionLoading] = useState(false);
  const [showPlanSelectionModal, setShowPlanSelectionModal] = useState(false);
  const [companyForPlanAssignment, setCompanyForPlanAssignment] = useState(null);

  // Define fetch functions outside useEffect so they can be called from anywhere
  const fetchOverview = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/super-admin/overview', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setOverview(await res.json());
      }
    } catch (e) {
      console.error('Failed to fetch overview:', e);
    }
  };

  const fetchCompanies = async (statusFilter = 'ALL') => {
    try {
      const url = statusFilter === 'ALL' 
        ? 'http://localhost:8000/api/v1/super-admin/companies?limit=50'
        : `http://localhost:8000/api/v1/super-admin/companies?limit=50&status=${statusFilter}`;
      
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCompanies(data.items || []);
      }
    } catch (e) {
      console.error('Failed to fetch companies:', e);
    }
  };

  const fetchAdmins = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/super-admin/admins?limit=10', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setAdmins(data.items || []);
      }
    } catch (e) {
      console.error('Failed to fetch admins:', e);
    }
  };

  const fetchOfferPlans = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/super-admin/offer-plans', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setOfferPlans(data || []);
      }
    } catch (e) {
      console.error('Failed to fetch offer plans:', e);
    }
  };

  const fetchSubscriptions = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/super-admin/company-subscriptions', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSubscriptions(data || []);
      }
    } catch (e) {
      console.error('Failed to fetch subscriptions:', e);
    }
  };

  useEffect(() => {
    if (!token) {
      navigate('/super-admin-login');
      return;
    }
    
    fetchOverview();
    fetchCompanies(activeStatusFilter);
    fetchAdmins();
    fetchOfferPlans();
    fetchSubscriptions();
  }, [token, navigate]);

  const handleLogout = () => {
    localStorage.removeItem('superAdminToken');
    localStorage.removeItem('superAdminUser');
    navigate('/super-admin-login');
  };

  const openCreateCompany = () => {
    setEditingCompany(null);
    setCompanyForm({ name: '', domain: '', description: '', subscription_plan: 'basic', is_active: true });
    setShowCompanyModal(true);
  };

  const openEditCompany = (c) => {
    setEditingCompany(c);
    setCompanyForm({
      name: c.name || '',
      domain: c.domain || '',
      description: c.description || '',
      subscription_plan: c.subscription_plan || 'basic',
      is_active: !!c.is_active,
    });
    setShowCompanyModal(true);
  };

  const saveCompany = async () => {
    try {
      const method = editingCompany ? 'PUT' : 'POST';
      const url = editingCompany
        ? `http://localhost:8000/api/v1/super-admin/companies/${editingCompany.id}`
        : 'http://localhost:8000/api/v1/super-admin/companies';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(companyForm),
      });
      if (!res.ok) throw new Error('Save failed');
      setShowCompanyModal(false);
      // Refresh
      const list = await fetch('http://localhost:8000/api/v1/super-admin/companies?limit=50', { headers: { Authorization: `Bearer ${token}` } });
      const data = await list.json();
      setCompanies(data.items || []);
    } catch (e) {
      alert('Save failed');
    }
  };

  const deleteCompany = async (c) => {
    if (!window.confirm(`Delete company "${c.name}"? This cannot be undone.`)) return;
    try {
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${c.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error();
      // Refresh
      const list = await fetch('http://localhost:8000/api/v1/super-admin/companies?limit=50', { headers: { Authorization: `Bearer ${token}` } });
      const data = await list.json();
      setCompanies(data.items || []);
    } catch (e) {
      alert('Delete failed');
    }
  };

  const openManageAdmins = async (company) => {
    setSelectedCompany(company);
    setShowCompanyAdmins(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${company.id}/admins`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCompanyAdmins(data.items || []);
      }
    } catch (e) {
      alert('Failed to load admins');
    }
  };

  const openCreateAdmin = () => {
    setEditingAdmin(null);
    setAdminForm({ full_name: '', email: '', phone_number: '', password: '', role: 'admin' });
    setShowAdminModal(true);
  };

  const openEditAdmin = (admin) => {
    setEditingAdmin(admin);
    setAdminForm({
      full_name: admin.full_name || '',
      email: admin.email || '',
      phone_number: admin.phone_number || '',
      password: '',
      role: admin.role || 'admin',
    });
    setShowAdminModal(true);
  };

  const saveAdmin = async () => {
    try {
      const method = editingAdmin ? 'PUT' : 'POST';
      const url = editingAdmin
        ? `http://localhost:8000/api/v1/super-admin/companies/${selectedCompany.id}/admins/${editingAdmin.id}`
        : `http://localhost:8000/api/v1/super-admin/companies/${selectedCompany.id}/admins`;
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(adminForm),
      });
      if (!res.ok) throw new Error('Save failed');
      setShowAdminModal(false);
      // Refresh admins
      const list = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${selectedCompany.id}/admins`, { headers: { Authorization: `Bearer ${token}` } });
      const data = await list.json();
      setCompanyAdmins(data.items || []);
    } catch (e) {
      alert('Save failed');
    }
  };

  const deleteAdmin = async (admin) => {
    if (!window.confirm(`Delete admin "${admin.full_name}"? This cannot be undone.`)) return;
    try {
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${selectedCompany.id}/admins/${admin.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Delete failed');
      }
      alert('Admin deleted successfully');
      // Refresh admins
      const list = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${selectedCompany.id}/admins`, { headers: { Authorization: `Bearer ${token}` } });
      const data = await list.json();
      setCompanyAdmins(data.items || []);
    } catch (e) {
      alert(e.message || 'Delete failed');
    }
  };

  const toggleAdminStatus = async (admin) => {
    const newStatus = !admin.is_active;
    const action = newStatus ? 'activate' : 'deactivate';
    
    if (!window.confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} admin "${admin.full_name}"?`)) return;
    
    try {
      console.log('Toggling admin status:', {adminId: admin.id, oldStatus: admin.is_active, newStatus});
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${selectedCompany.id}/admins/${admin.id}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ is_active: newStatus === true })  // Ensure boolean
      });
      
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Status update failed');
      }
      
      alert(`Admin ${action}d successfully. Email notification sent.`);
      
      // Refresh admins
      const list = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${selectedCompany.id}/admins`, { 
        headers: { Authorization: `Bearer ${token}` } 
      });
      const data = await list.json();
      setCompanyAdmins(data.items || []);
    } catch (e) {
      alert(e.message || `Failed to ${action} admin`);
    }
  };

  const approveCompany = async (company) => {
    if (!window.confirm(`Approve company "${company.name}"? Email notification will be sent to the admin.`)) return;
    try {
      console.log('Approving company:', company.id);
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${company.id}/approve`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log('Approve response status:', res.status);
      
      if (!res.ok) {
        const error = await res.json();
        console.error('Approve error:', error);
        throw new Error(error.detail || 'Approval failed');
      }
      const data = await res.json();
      console.log('Approve success:', data);
      alert('✅ Company approved successfully! Email sent to admin.');
      await fetchOverview();
      await fetchCompanies(activeStatusFilter);
    } catch (e) {
      console.error('Approve failed:', e);
      alert('❌ ' + (e.message || 'Approval failed'));
    }
  };

  const rejectCompany = async (company) => {
    if (!window.confirm(`Reject company "${company.name}"? Email notification will be sent to the admin.`)) return;
    try {
      console.log('Rejecting company:', company.id);
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${company.id}/reject`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log('Reject response:', res.status);
      
      if (!res.ok) {
        const error = await res.json();
        console.error('Reject error:', error);
        throw new Error(error.detail || 'Rejection failed');
      }
      alert('✅ Company rejected. Email sent to admin.');
      await fetchOverview();
      await fetchCompanies(activeStatusFilter);
    } catch (e) {
      console.error('Reject failed:', e);
      alert('❌ ' + (e.message || 'Rejection failed'));
    }
  };

  const suspendCompany = async (company) => {
    if (!window.confirm(`Suspend company "${company.name}"? Email notification will be sent to the admin.`)) return;
    try {
      console.log('Suspending company:', company.id);
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${company.id}/suspend`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log('Suspend response:', res.status);
      
      if (!res.ok) {
        const error = await res.json();
        console.error('Suspend error:', error);
        throw new Error(error.detail || 'Suspension failed');
      }
      alert('✅ Company suspended. Email sent to admin.');
      await fetchOverview();
      await fetchCompanies(activeStatusFilter);
    } catch (e) {
      console.error('Suspend failed:', e);
      alert('❌ ' + (e.message || 'Suspension failed'));
    }
  };

  const activateCompany = async (company) => {
    if (!window.confirm(`Activate company "${company.name}"? Email notification will be sent to the admin.`)) return;
    try {
      console.log('Activating company:', company.id);
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${company.id}/activate`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log('Activate response:', res.status);
      
      if (!res.ok) {
        const error = await res.json();
        console.error('Activate error:', error);
        throw new Error(error.detail || 'Activation failed');
      }
      alert('✅ Company activated. Email sent to admin.');
      await fetchOverview();
      await fetchCompanies(activeStatusFilter);
    } catch (e) {
      console.error('Activate failed:', e);
      alert('❌ ' + (e.message || 'Activation failed'));
    }
  };

  const viewCompanyDetails = async (company) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/companies/${company.id}/details`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedCompanyDetails(data);
        setShowCompanyDetails(true);
      }
    } catch (e) {
      alert('Failed to load company details');
    }
  };

  const handleStatusFilter = (status) => {
    setActiveStatusFilter(status);
    fetchCompanies(status);
  };

  // Offer Plans Management Functions
  const openCreateOfferPlan = () => {
    setEditingOfferPlan(null);
    setOfferPlanForm({
      plan_name: '',
      price: 0,
      job_post_limit: '',
      recruiter_limit: 1,
      candidate_views: '',
      analytics_level: 'Basic',
      support_level: '',
      status: 'Active'
    });
    setShowOfferPlanModal(true);
  };

  const openEditOfferPlan = (plan) => {
    setEditingOfferPlan(plan);
    setOfferPlanForm({
      plan_name: plan.plan_name,
      price: plan.price,
      job_post_limit: plan.job_post_limit || '',
      recruiter_limit: plan.recruiter_limit,
      candidate_views: plan.candidate_views || '',
      analytics_level: plan.analytics_level,
      support_level: plan.support_level,
      status: plan.status
    });
    setShowOfferPlanModal(true);
  };

  const saveOfferPlan = async () => {
    try {
      const formData = {
        ...offerPlanForm,
        price: parseFloat(offerPlanForm.price),
        job_post_limit: offerPlanForm.job_post_limit ? parseInt(offerPlanForm.job_post_limit) : null,
        candidate_views: offerPlanForm.candidate_views ? parseInt(offerPlanForm.candidate_views) : null,
        recruiter_limit: parseInt(offerPlanForm.recruiter_limit)
      };

      const method = editingOfferPlan ? 'PUT' : 'POST';
      const url = editingOfferPlan
        ? `http://localhost:8000/api/v1/super-admin/offer-plans/${editingOfferPlan.id}`
        : 'http://localhost:8000/api/v1/super-admin/offer-plans';
      
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(formData),
      });
      
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Save failed');
      }
      
      setShowOfferPlanModal(false);
      fetchOfferPlans();
      alert(editingOfferPlan ? 'Plan updated successfully' : 'Plan created successfully');
    } catch (e) {
      alert(e.message || 'Save failed');
    }
  };

  const deleteOfferPlan = async (plan) => {
    if (!window.confirm(`Delete plan "${plan.plan_name}"? This cannot be undone.`)) return;
    try {
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/offer-plans/${plan.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Delete failed');
      alert('Plan deleted successfully');
      fetchOfferPlans();
    } catch (e) {
      alert('Delete failed');
    }
  };

  const togglePlanStatus = async (plan) => {
    try {
      console.log('Toggling plan status:', plan.id);
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/offer-plans/${plan.id}/toggle-status`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log('Toggle status response:', res.status);
      
      if (!res.ok) {
        const error = await res.json();
        console.error('Toggle error:', error);
        throw new Error(error.detail || 'Status update failed');
      }
      const data = await res.json();
      alert(data.message || '✅ Plan status updated');
      await fetchOfferPlans();
    } catch (e) {
      console.error('Toggle failed:', e);
      alert('❌ ' + (e.message || 'Status update failed'));
    }
  };

  const openPlanSelectionModal = (company) => {
    setCompanyForPlanAssignment(company);
    setShowPlanSelectionModal(true);
  };

  const assignPlanToCompany = async (plan) => {
    if (!companyForPlanAssignment) return;
    
    if (!window.confirm(`Assign ${plan.plan_name} ($${plan.price}/month) to ${companyForPlanAssignment.name}?`)) return;
    
    try {
      console.log('Assigning subscription:', {companyId: companyForPlanAssignment.id, planId: plan.id});
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/company-subscriptions`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({
          company_id: parseInt(companyForPlanAssignment.id),
          offer_plan_id: plan.id,
          status: 'Active'
        })
      });
      console.log('Assign subscription response:', res.status);
      
      if (!res.ok) {
        const error = await res.json();
        console.error('Assign error:', error);
        throw new Error(error.detail || 'Failed to assign subscription');
      }
      
      const data = await res.json();
      alert(`✅ ${plan.plan_name} assigned to ${companyForPlanAssignment.name}! Emails sent to company admin and super admin.`);
      setShowPlanSelectionModal(false);
      setCompanyForPlanAssignment(null);
      await fetchSubscriptions();
      await fetchCompanies(activeStatusFilter);
    } catch (e) {
      console.error('Assign subscription failed:', e);
      alert('❌ ' + (e.message || 'Failed to assign subscription'));
    }
  };

  const approveSubscription = async (subscriptionId) => {
    if (!window.confirm('Approve this subscription request? Company admin will be notified via email.')) return;
    
    try {
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/company-subscriptions/${subscriptionId}/approve`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Approval failed');
      }
      
      const data = await res.json();
      alert(`✅ ${data.plan || 'Subscription'} approved! Email sent to company admin.`);
      await fetchSubscriptions();
    } catch (e) {
      alert('❌ ' + (e.message || 'Failed to approve subscription'));
    }
  };

  const rejectSubscription = async (subscriptionId) => {
    const reason = prompt('Reason for rejection (optional):');
    if (reason === null) return; // User cancelled
    
    try {
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/company-subscriptions/${subscriptionId}/reject`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ reason: reason || '' })
      });
      
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Rejection failed');
      }
      
      const data = await res.json();
      alert(`✅ Subscription request rejected. Email sent to company admin.`);
      await fetchSubscriptions();
    } catch (e) {
      alert('❌ ' + (e.message || 'Failed to reject subscription'));
    }
  };

  const cancelSubscription = async (subscriptionId) => {
    if (!window.confirm('Cancel this active subscription?')) return;
    
    try {
      const res = await fetch(`http://localhost:8000/api/v1/super-admin/company-subscriptions/${subscriptionId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Cancellation failed');
      }
      
      const data = await res.json();
      alert(`✅ ${data.message || 'Subscription cancelled'}`);
      await fetchSubscriptions();
    } catch (e) {
      alert('❌ ' + (e.message || 'Failed to cancel subscription'));
    }
  };

  return (
    <div style={{padding: 24, background: '#f8fafc', minHeight: '100vh'}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16}}>
        <div>
          <div style={{fontSize: 12, color: '#6b7280'}}>Super Admin</div>
          <div style={{fontSize: 24, fontWeight: 700}}>Boolmind — Global Control</div>
        </div>
        <div>
          <span style={{marginRight: 16, color: '#374151'}}>{user?.email}</span>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{marginBottom: 24}}>
        <div style={{display: 'flex', gap: 0, borderBottom: '2px solid #e5e7eb'}}>
          {[
            { id: 'companies', label: 'Company Management' },
            { id: 'offer-plans', label: 'Offer Plans' },
            { id: 'subscriptions', label: 'Company Subscriptions' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '12px 24px',
                border: 'none',
                backgroundColor: activeTab === tab.id ? 'white' : 'transparent',
                color: activeTab === tab.id ? '#3b82f6' : '#6b7280',
                borderBottom: activeTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
                cursor: 'pointer',
                fontWeight: activeTab === tab.id ? '600' : '400'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Pending Companies Card - Only show on companies tab */}
      {activeTab === 'companies' && (
        <div style={{background: 'white', padding: 20, borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: 24, borderLeft: '4px solid #f59e0b'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div>
              <h3 style={{margin: 0, color: '#1f2937'}}>Pending Company Approvals</h3>
              <div style={{fontSize: 32, fontWeight: 'bold', color: '#f59e0b', marginTop: 8}}>{overview.companies}</div>
              <div style={{color: '#6b7280', fontSize: 14}}>Companies waiting for approval</div>
            </div>
            <button 
              onClick={() => handleStatusFilter('PENDING')}
              style={{backgroundColor: '#f59e0b', color: 'white', border: 'none', padding: '8px 16px', borderRadius: 6, cursor: 'pointer'}}
            >
              Review Pending
            </button>
          </div>
        </div>
      )}

      {/* Company Management Tab */}
      {activeTab === 'companies' && (
        <Section title="Company Management">
        <div style={{padding: 12}}>
          {/* Status Filter Tabs */}
          <div style={{marginBottom: 16}}>
            <div style={{display: 'flex', gap: 8, marginBottom: 12}}>
              {['ALL', 'PENDING', 'ACTIVE', 'REJECTED', 'SUSPENDED'].map(status => (
                <button
                  key={status}
                  onClick={() => handleStatusFilter(status)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 4,
                    border: '1px solid #d1d5db',
                    backgroundColor: activeStatusFilter === status ? '#3b82f6' : 'white',
                    color: activeStatusFilter === status ? 'white' : '#374151',
                    cursor: 'pointer',
                    fontSize: 14
                  }}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>
          
          <div style={{display:'flex', justifyContent:'space-between', marginBottom:12}}>
            <input
              placeholder="Search companies by name/domain"
              value={companySearch}
              onChange={(e)=>setCompanySearch(e.target.value)}
              style={{flex:1, marginRight: 8}}
            />
            <button onClick={openCreateCompany}>+ New Company</button>
          </div>
          <table style={{width: '100%', borderCollapse: 'collapse'}}>
            <thead>
              <tr>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Name</th>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Domain</th>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Status</th>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Subscription</th>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Jobs</th>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Applications</th>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Created</th>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {companies
                .filter(c => !companySearch || (c.name||'').toLowerCase().includes(companySearch.toLowerCase()) || (c.domain||'').toLowerCase().includes(companySearch.toLowerCase()))
                .map((c) => (
                <tr key={c.id}>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                    <button 
                      onClick={() => viewCompanyDetails(c)}
                      style={{background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', textDecoration: 'underline'}}
                    >
                      {c.name}
                    </button>
                  </td>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{c.domain}</td>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: 12,
                      fontSize: 12,
                      backgroundColor: c.status === 'PENDING' ? '#fef3c7' : 
                                     c.status === 'ACTIVE' ? '#d1fae5' : 
                                     c.status === 'REJECTED' ? '#fee2e2' : '#f3f4f6',
                      color: c.status === 'PENDING' ? '#92400e' : 
                             c.status === 'ACTIVE' ? '#065f46' : 
                             c.status === 'REJECTED' ? '#991b1b' : '#374151'
                    }}>
                      {c.status || 'UNKNOWN'}
                    </span>
                  </td>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                    {c.subscribed_plan_name ? (
                      <div>
                        <div style={{fontWeight: 'bold', fontSize: '12px'}}>{c.subscribed_plan_name}</div>
                        <div style={{fontSize: '11px', color: '#666'}}>${c.subscribed_plan_price}</div>
                        <span style={{
                          padding: '2px 6px',
                          borderRadius: '3px',
                          fontSize: '10px',
                          backgroundColor: c.subscription_status === 'Active' ? '#d1fae5' : '#fee2e2',
                          color: c.subscription_status === 'Active' ? '#065f46' : '#991b1b'
                        }}>
                          {c.subscription_status || 'N/A'}
                        </span>
                      </div>
                    ) : (
                      <span style={{color: '#999', fontSize: '12px'}}>No Plan</span>
                    )}
                  </td>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{c.jobs_count || 0}</td>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{c.applications_count || 0}</td>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{new Date(c.created_at).toLocaleDateString()}</td>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                    <div style={{display: 'flex', flexWrap: 'wrap', gap: 4}}>
                      {c.status === 'PENDING' && (
                        <>
                          <button onClick={()=>approveCompany(c)} style={{backgroundColor:'#10b981', color:'white', border:'none', padding:'4px 8px', borderRadius:4, fontSize:12}}>Approve</button>
                          <button onClick={()=>rejectCompany(c)} style={{backgroundColor:'#ef4444', color:'white', border:'none', padding:'4px 8px', borderRadius:4, fontSize:12}}>Reject</button>
                        </>
                      )}
                      {c.status === 'ACTIVE' && (
                        <>
                          <button onClick={()=>suspendCompany(c)} style={{backgroundColor:'#f59e0b', color:'white', border:'none', padding:'4px 8px', borderRadius:4, fontSize:12}}>Suspend</button>
                          <button onClick={()=>openPlanSelectionModal(c)} style={{backgroundColor:'#8b5cf6', color:'white', border:'none', padding:'4px 8px', borderRadius:4, fontSize:12}}>Assign Plan</button>
                        </>
                      )}
                      {c.status === 'SUSPENDED' && (
                        <button onClick={()=>activateCompany(c)} style={{backgroundColor:'#10b981', color:'white', border:'none', padding:'4px 8px', borderRadius:4, fontSize:12}}>Activate</button>
                      )}
                      {c.status === 'REJECTED' && (
                        <span style={{fontSize:12, color:'#6b7280'}}>Rejected</span>
                      )}
                      <button onClick={()=>openManageAdmins(c)} style={{backgroundColor:'#3b82f6', color:'white', border:'none', padding:'4px 8px', borderRadius:4, fontSize:12}}>Admins</button>
                      <button onClick={()=>deleteCompany(c)} style={{color:'#b91c1c', border:'none', background:'none', fontSize:12}}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
              {!companies.length && (
                <tr><td colSpan={3} style={{padding: 8, color: '#6b7280'}}>No companies found</td></tr>
              )}
            </tbody>
          </table>
        </div>
        </Section>
      )}

      {/* Offer Plans Tab */}
      {activeTab === 'offer-plans' && (
        <Section title="Offer Plans Management">
          <div style={{padding: 12}}>
            <div style={{display:'flex', justifyContent:'space-between', marginBottom:16}}>
              <h3 style={{margin: 0}}>Subscription Plans</h3>
              <button 
                onClick={openCreateOfferPlan}
                style={{backgroundColor:'#3b82f6', color:'white', border:'none', padding:'8px 16px', borderRadius:4}}
              >
                + New Plan
              </button>
            </div>
            
            <table style={{width: '100%', borderCollapse: 'collapse'}}>
              <thead>
                <tr>
                  <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Plan Name</th>
                  <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Price</th>
                  <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Job Limit</th>
                  <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Recruiters</th>
                  <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Views</th>
                  <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Analytics</th>
                  <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Support</th>
                  <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Status</th>
                  <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {offerPlans.map((plan) => (
                  <tr key={plan.id}>
                    <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{plan.plan_name}</td>
                    <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>${plan.price}</td>
                    <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                      {plan.job_post_limit ? plan.job_post_limit : 'Unlimited'}
                    </td>
                    <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{plan.recruiter_limit}</td>
                    <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                      {plan.candidate_views ? plan.candidate_views.toLocaleString() : 'Unlimited'}
                    </td>
                    <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{plan.analytics_level}</td>
                    <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{plan.support_level}</td>
                    <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: 12,
                        fontSize: 12,
                        backgroundColor: plan.status === 'Active' ? '#d1fae5' : '#fee2e2',
                        color: plan.status === 'Active' ? '#065f46' : '#991b1b'
                      }}>
                        {plan.status}
                      </span>
                    </td>
                    <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                      <button 
                        onClick={() => openEditOfferPlan(plan)} 
                        style={{marginRight:4, backgroundColor:'#10b981', color:'white', border:'none', padding:'4px 8px', borderRadius:4}}
                      >
                        Edit
                      </button>
                      <button 
                        onClick={() => togglePlanStatus(plan)} 
                        style={{marginRight:4, backgroundColor:plan.status === 'Active' ? '#f59e0b' : '#10b981', color:'white', border:'none', padding:'4px 8px', borderRadius:4}}
                      >
                        {plan.status === 'Active' ? 'Deactivate' : 'Activate'}
                      </button>
                      <button 
                        onClick={() => deleteOfferPlan(plan)} 
                        style={{color:'#b91c1c', border:'none', background:'none'}}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {!offerPlans.length && (
                  <tr><td colSpan={9} style={{padding: 16, textAlign:'center', color: '#6b7280'}}>No offer plans found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Company Subscriptions Tab */}
      {activeTab === 'subscriptions' && (
        <Section title="Company Subscriptions">
          <div style={{padding: 12}}>
            <div style={{marginBottom: 16}}>
              <h3 style={{margin: 0}}>Company Subscription Overview</h3>
              <p style={{color: '#6b7280', margin: '8px 0'}}>View and manage company subscription plans</p>
            </div>
            
            {subscriptionLoading ? (
              <div style={{textAlign: 'center', padding: 40}}>Loading subscriptions...</div>
            ) : (
              <table style={{width: '100%', borderCollapse: 'collapse'}}>
                <thead>
                  <tr>
                    <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Company</th>
                    <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Plan</th>
                    <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Price</th>
                    <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Status</th>
                    <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Subscribed</th>
                    <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Expires</th>
                    <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {subscriptions.map((sub) => (
                    <tr key={sub.id}>
                      <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                        <div style={{fontWeight: 'bold'}}>{sub.company_name}</div>
                      </td>
                      <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                        <div style={{fontWeight: 'bold', color: '#3b82f6'}}>{sub.plan_name}</div>
                      </td>
                      <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                        <div style={{fontWeight: 'bold'}}>${sub.plan_price}</div>
                      </td>
                      <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: 12,
                          fontSize: 12,
                          backgroundColor: sub.status === 'Active' ? '#d1fae5' : 
                                         sub.status === 'Inactive' ? '#fee2e2' :
                                         sub.status === 'Expired' ? '#fef3c7' : '#f3f4f6',
                          color: sub.status === 'Active' ? '#065f46' : 
                                 sub.status === 'Inactive' ? '#991b1b' :
                                 sub.status === 'Expired' ? '#92400e' : '#374151'
                        }}>
                          {sub.status}
                        </span>
                      </td>
                      <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                        {new Date(sub.subscribed_at).toLocaleDateString()}
                      </td>
                      <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                        {sub.expires_at ? new Date(sub.expires_at).toLocaleDateString() : 'No Expiry'}
                      </td>
                      <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>
                        {sub.status === 'Pending' ? (
                          <>
                            <button 
                              onClick={() => approveSubscription(sub.id)} 
                              style={{marginRight:4, backgroundColor:'#10b981', color:'white', border:'none', padding:'4px 8px', borderRadius:4, fontSize:12}}
                            >
                              Approve
                            </button>
                            <button 
                              onClick={() => rejectSubscription(sub.id)} 
                              style={{backgroundColor:'#ef4444', color:'white', border:'none', padding:'4px 8px', borderRadius:4, fontSize:12}}
                            >
                              Reject
                            </button>
                          </>
                        ) : (
                          <button 
                            onClick={() => cancelSubscription(sub.id)} 
                            style={{color:'#b91c1c', border:'none', background:'none', fontSize:12}}
                          >
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {!subscriptions.length && (
                    <tr><td colSpan={7} style={{padding: 16, textAlign:'center', color: '#6b7280'}}>No subscriptions found</td></tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </Section>
      )}

      {showCompanyModal && (
        <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.3)', display:'flex', alignItems:'center', justifyContent:'center'}}>
          <div style={{background:'#fff', padding:20, borderRadius:8, minWidth:420}}>
            <div style={{fontSize:18, fontWeight:600, marginBottom:12}}>{editingCompany ? 'Edit Company' : 'New Company'}</div>
            <div className="form-group">
              <label>Name</label>
              <input value={companyForm.name} onChange={(e)=>setCompanyForm({...companyForm, name:e.target.value})} />
            </div>
            <div className="form-group">
              <label>Domain</label>
              <input value={companyForm.domain} onChange={(e)=>setCompanyForm({...companyForm, domain:e.target.value})} />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea value={companyForm.description} onChange={(e)=>setCompanyForm({...companyForm, description:e.target.value})} />
            </div>
            <div className="form-group">
              <label>Plan</label>
              <select value={companyForm.subscription_plan} onChange={(e)=>setCompanyForm({...companyForm, subscription_plan:e.target.value})}>
                <option value="basic">basic</option>
                <option value="premium">premium</option>
                <option value="enterprise">enterprise</option>
              </select>
            </div>
            <div className="form-group">
              <label>
                <input type="checkbox" checked={companyForm.is_active} onChange={(e)=>setCompanyForm({...companyForm, is_active:e.target.checked})} /> Active
              </label>
            </div>
            <div style={{display:'flex', justifyContent:'flex-end', gap:8}}>
              <button onClick={()=>setShowCompanyModal(false)}>Cancel</button>
              <button onClick={saveCompany}>{editingCompany ? 'Update' : 'Create'}</button>
            </div>
          </div>
        </div>
      )}

      <Section title="Recent Admins">
        <div style={{padding: 12}}>
          <table style={{width: '100%', borderCollapse: 'collapse'}}>
            <thead>
              <tr>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Name</th>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Email</th>
                <th style={{textAlign: 'left', padding: 8, borderBottom: '1px solid #eee'}}>Status</th>
              </tr>
            </thead>
            <tbody>
              {admins.map((a) => (
                <tr key={a.id}>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{a.full_name}</td>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{a.email}</td>
                  <td style={{padding: 8, borderBottom: '1px solid #f1f5f9'}}>{a.is_active ? 'Active' : 'Inactive'}</td>
                </tr>
              ))}
              {!admins.length && (
                <tr><td colSpan={3} style={{padding: 8, color: '#6b7280'}}>No admins found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Section>

      {/* Company Admins Modal */}
      {showCompanyAdmins && (
        <div style={{position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000}}>
          <div style={{background:'white', borderRadius:8, padding:24, width:'80%', maxWidth:1000, maxHeight:'80vh', overflow:'auto'}}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16}}>
              <h3>Manage Admins - {selectedCompany?.name}</h3>
              <button onClick={() => setShowCompanyAdmins(false)} style={{background:'none', border:'none', fontSize:20}}>×</button>
            </div>
            
            <div style={{marginBottom:16}}>
              <button onClick={openCreateAdmin} style={{backgroundColor:'#3b82f6', color:'white', border:'none', padding:'8px 16px', borderRadius:4}}>
                + Add Admin
              </button>
            </div>

            <table style={{width:'100%', borderCollapse:'collapse'}}>
              <thead>
                <tr style={{borderBottom:'2px solid #e5e7eb'}}>
                  <th style={{textAlign:'left', padding:8}}>Full Name</th>
                  <th style={{textAlign:'left', padding:8}}>Email</th>
                  <th style={{textAlign:'left', padding:8}}>Phone</th>
                  <th style={{textAlign:'left', padding:8}}>Role</th>
                  <th style={{textAlign:'left', padding:8}}>Status</th>
                  <th style={{textAlign:'left', padding:8}}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {companyAdmins.map(admin => (
                  <tr key={admin.id} style={{borderBottom:'1px solid #f3f4f6'}}>
                    <td style={{padding:8}}>{admin.full_name}</td>
                    <td style={{padding:8}}>{admin.email}</td>
                    <td style={{padding:8}}>{admin.phone_number || 'N/A'}</td>
                    <td style={{padding:8}}>{admin.role}</td>
                    <td style={{padding:8}}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: 12,
                        fontSize: 12,
                        backgroundColor: admin.is_active ? '#d1fae5' : '#fee2e2',
                        color: admin.is_active ? '#065f46' : '#991b1b'
                      }}>
                        {admin.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td style={{padding:8}}>
                      <button 
                        onClick={() => toggleAdminStatus(admin)} 
                        style={{
                          marginRight:4, 
                          backgroundColor: admin.is_active ? '#f59e0b' : '#10b981', 
                          color:'white', 
                          border:'none', 
                          padding:'4px 8px', 
                          borderRadius:4
                        }}
                      >
                        {admin.is_active ? 'Suspend' : 'Activate'}
                      </button>
                      <button onClick={() => openEditAdmin(admin)} style={{marginRight:4, backgroundColor:'#3b82f6', color:'white', border:'none', padding:'4px 8px', borderRadius:4}}>Edit</button>
                      <button onClick={() => deleteAdmin(admin)} style={{color:'#b91c1c', border:'none', background:'none'}}>Delete</button>
                    </td>
                  </tr>
                ))}
                {!companyAdmins.length && (
                  <tr><td colSpan={6} style={{padding:16, textAlign:'center', color:'#6b7280'}}>No admins found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Admin Form Modal */}
      {showAdminModal && (
        <div style={{position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1001}}>
          <div style={{background:'white', borderRadius:8, padding:24, width:400}}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16}}>
              <h3>{editingAdmin ? 'Edit Admin' : 'Add Admin'}</h3>
              <button onClick={() => setShowAdminModal(false)} style={{background:'none', border:'none', fontSize:20}}>×</button>
            </div>
            
            <div style={{marginBottom:12}}>
              <label style={{display:'block', marginBottom:4, fontWeight:500}}>Full Name *</label>
              <input 
                type="text" 
                value={adminForm.full_name}
                onChange={(e) => setAdminForm({...adminForm, full_name: e.target.value})}
                style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                placeholder="Enter full name"
              />
            </div>
            
            <div style={{marginBottom:12}}>
              <label style={{display:'block', marginBottom:4, fontWeight:500}}>Email Address *</label>
              <input 
                type="email" 
                value={adminForm.email}
                onChange={(e) => setAdminForm({...adminForm, email: e.target.value})}
                style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                placeholder="Enter email address"
              />
            </div>
            
            <div style={{marginBottom:12}}>
              <label style={{display:'block', marginBottom:4, fontWeight:500}}>Phone Number</label>
              <input 
                type="tel" 
                value={adminForm.phone_number}
                onChange={(e) => setAdminForm({...adminForm, phone_number: e.target.value})}
                style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                placeholder="Enter phone number (optional)"
              />
            </div>
            
            <div style={{marginBottom:12}}>
              <label style={{display:'block', marginBottom:4, fontWeight:500}}>Password {!editingAdmin && '*'}</label>
              <input 
                type="password" 
                value={adminForm.password}
                onChange={(e) => setAdminForm({...adminForm, password: e.target.value})}
                style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                placeholder={editingAdmin ? "Leave blank to keep current" : "Enter password"}
              />
            </div>
            
            <div style={{marginBottom:16}}>
              <label style={{display:'block', marginBottom:4, fontWeight:500}}>Role *</label>
              <select 
                value={adminForm.role}
                onChange={(e) => setAdminForm({...adminForm, role: e.target.value})}
                style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
              >
                <option value="admin">Admin</option>
                <option value="recruiter">Recruiter</option>
              </select>
            </div>
            
            <div style={{display:'flex', gap:8}}>
              <button 
                onClick={saveAdmin}
                style={{flex:1, backgroundColor:'#3b82f6', color:'white', border:'none', padding:'8px', borderRadius:4}}
              >
                {editingAdmin ? 'Update' : 'Create'} Admin
              </button>
              <button 
                onClick={() => setShowAdminModal(false)}
                style={{flex:1, backgroundColor:'#6b7280', color:'white', border:'none', padding:'8px', borderRadius:4}}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Company Details Modal */}
      {showCompanyDetails && selectedCompanyDetails && (
        <div style={{position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1002}}>
          <div style={{background:'white', borderRadius:8, padding:24, width:500, maxHeight:'80vh', overflow:'auto'}}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16}}>
              <h3>Company Details - {selectedCompanyDetails.name}</h3>
              <button onClick={() => setShowCompanyDetails(false)} style={{background:'none', border:'none', fontSize:20}}>×</button>
            </div>
            
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16}}>
              <div>
                <label style={{display:'block', fontWeight:500, marginBottom:4}}>Company Name</label>
                <div style={{padding:8, backgroundColor:'#f9fafb', borderRadius:4}}>{selectedCompanyDetails.name}</div>
              </div>
              <div>
                <label style={{display:'block', fontWeight:500, marginBottom:4}}>Domain</label>
                <div style={{padding:8, backgroundColor:'#f9fafb', borderRadius:4}}>{selectedCompanyDetails.domain}</div>
              </div>
              <div>
                <label style={{display:'block', fontWeight:500, marginBottom:4}}>Status</label>
                <div style={{padding:8, backgroundColor:'#f9fafb', borderRadius:4}}>{selectedCompanyDetails.status}</div>
              </div>
              <div>
                <label style={{display:'block', fontWeight:500, marginBottom:4}}>Subscription Plan</label>
                <div style={{padding:8, backgroundColor:'#f9fafb', borderRadius:4}}>{selectedCompanyDetails.subscription_plan}</div>
              </div>
            </div>
            
            <div style={{marginBottom:16}}>
              <label style={{display:'block', fontWeight:500, marginBottom:4}}>Description</label>
              <div style={{padding:8, backgroundColor:'#f9fafb', borderRadius:4, minHeight:60}}>{selectedCompanyDetails.description || 'No description provided'}</div>
            </div>
            
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16}}>
              <div>
                <label style={{display:'block', fontWeight:500, marginBottom:4}}>Admin Name</label>
                <div style={{padding:8, backgroundColor:'#f9fafb', borderRadius:4}}>{selectedCompanyDetails.admin_name || 'Not assigned'}</div>
              </div>
              <div>
                <label style={{display:'block', fontWeight:500, marginBottom:4}}>Admin Email</label>
                <div style={{padding:8, backgroundColor:'#f9fafb', borderRadius:4}}>{selectedCompanyDetails.admin_email || 'Not assigned'}</div>
              </div>
            </div>
            
            <div style={{display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:16, marginBottom:16}}>
              <div style={{textAlign:'center', padding:12, backgroundColor:'#f0f9ff', borderRadius:6}}>
                <div style={{fontSize:20, fontWeight:'bold', color:'#0369a1'}}>{selectedCompanyDetails.jobs_count || 0}</div>
                <div style={{fontSize:12, color:'#6b7280'}}>Jobs</div>
              </div>
              <div style={{textAlign:'center', padding:12, backgroundColor:'#f0fdf4', borderRadius:6}}>
                <div style={{fontSize:20, fontWeight:'bold', color:'#16a34a'}}>{selectedCompanyDetails.applications_count || 0}</div>
                <div style={{fontSize:12, color:'#6b7280'}}>Applications</div>
              </div>
              <div style={{textAlign:'center', padding:12, backgroundColor:'#fefce8', borderRadius:6}}>
                <div style={{fontSize:20, fontWeight:'bold', color:'#ca8a04'}}>{selectedCompanyDetails.candidates_count || 0}</div>
                <div style={{fontSize:12, color:'#6b7280'}}>Candidates</div>
              </div>
              <div style={{textAlign:'center', padding:12, backgroundColor:'#fdf4ff', borderRadius:6}}>
                <div style={{fontSize:20, fontWeight:'bold', color:'#9333ea'}}>{selectedCompanyDetails.admin_count || 0}</div>
                <div style={{fontSize:12, color:'#6b7280'}}>Admins</div>
              </div>
            </div>
            
            <div style={{marginBottom:16}}>
              <label style={{display:'block', fontWeight:500, marginBottom:4}}>Created Date</label>
              <div style={{padding:8, backgroundColor:'#f9fafb', borderRadius:4}}>{new Date(selectedCompanyDetails.created_at).toLocaleString()}</div>
            </div>
            
            <div style={{display:'flex', gap:8}}>
              <button 
                onClick={() => setShowCompanyDetails(false)}
                style={{flex:1, backgroundColor:'#6b7280', color:'white', border:'none', padding:'8px', borderRadius:4}}
              >
                Close
              </button>
              <button 
                onClick={() => {
                  setShowCompanyDetails(false);
                  openManageAdmins({id: selectedCompanyDetails.id, name: selectedCompanyDetails.name});
                }}
                style={{flex:1, backgroundColor:'#3b82f6', color:'white', border:'none', padding:'8px', borderRadius:4}}
              >
                Manage Admins
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Offer Plan Form Modal */}
      {showOfferPlanModal && (
        <div style={{position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1003}}>
          <div style={{background:'white', borderRadius:8, padding:24, width:600, maxHeight:'80vh', overflow:'auto'}}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16}}>
              <h3>{editingOfferPlan ? 'Edit Plan' : 'Create New Plan'}</h3>
              <button onClick={() => setShowOfferPlanModal(false)} style={{background:'none', border:'none', fontSize:20}}>×</button>
            </div>
            
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16}}>
              <div>
                <label style={{display:'block', marginBottom:4, fontWeight:500}}>Plan Name *</label>
                <input 
                  type="text" 
                  value={offerPlanForm.plan_name}
                  onChange={(e) => setOfferPlanForm({...offerPlanForm, plan_name: e.target.value})}
                  style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                  placeholder="e.g., Platinum, Gold, Silver"
                />
              </div>
              
              <div>
                <label style={{display:'block', marginBottom:4, fontWeight:500}}>Price (USD) *</label>
                <input 
                  type="number" 
                  step="0.01"
                  value={offerPlanForm.price}
                  onChange={(e) => setOfferPlanForm({...offerPlanForm, price: e.target.value})}
                  style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                  placeholder="0.00"
                />
              </div>
            </div>
            
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16}}>
              <div>
                <label style={{display:'block', marginBottom:4, fontWeight:500}}>Job Post Limit</label>
                <input 
                  type="number" 
                  value={offerPlanForm.job_post_limit}
                  onChange={(e) => setOfferPlanForm({...offerPlanForm, job_post_limit: e.target.value})}
                  style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                  placeholder="Leave empty for unlimited"
                />
                <small style={{color:'#6b7280', fontSize:12}}>Leave empty for unlimited</small>
              </div>
              
              <div>
                <label style={{display:'block', marginBottom:4, fontWeight:500}}>Recruiter Limit *</label>
                <input 
                  type="number" 
                  value={offerPlanForm.recruiter_limit}
                  onChange={(e) => setOfferPlanForm({...offerPlanForm, recruiter_limit: e.target.value})}
                  style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                  placeholder="1"
                  min="1"
                />
              </div>
            </div>
            
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16}}>
              <div>
                <label style={{display:'block', marginBottom:4, fontWeight:500}}>Candidate Views</label>
                <input 
                  type="number" 
                  value={offerPlanForm.candidate_views}
                  onChange={(e) => setOfferPlanForm({...offerPlanForm, candidate_views: e.target.value})}
                  style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                  placeholder="Leave empty for unlimited"
                />
                <small style={{color:'#6b7280', fontSize:12}}>Leave empty for unlimited</small>
              </div>
              
              <div>
                <label style={{display:'block', marginBottom:4, fontWeight:500}}>Analytics Level *</label>
                <select 
                  value={offerPlanForm.analytics_level}
                  onChange={(e) => setOfferPlanForm({...offerPlanForm, analytics_level: e.target.value})}
                  style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                >
                  <option value="Basic">Basic</option>
                  <option value="Standard">Standard</option>
                  <option value="Advanced">Advanced</option>
                </select>
              </div>
            </div>
            
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16}}>
              <div>
                <label style={{display:'block', marginBottom:4, fontWeight:500}}>Support Level *</label>
                <input 
                  type="text" 
                  value={offerPlanForm.support_level}
                  onChange={(e) => setOfferPlanForm({...offerPlanForm, support_level: e.target.value})}
                  style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                  placeholder="e.g., 24/7 Priority, Business Hours, Email Only"
                />
              </div>
              
              <div>
                <label style={{display:'block', marginBottom:4, fontWeight:500}}>Status *</label>
                <select 
                  value={offerPlanForm.status}
                  onChange={(e) => setOfferPlanForm({...offerPlanForm, status: e.target.value})}
                  style={{width:'100%', padding:8, border:'1px solid #d1d5db', borderRadius:4}}
                >
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
              </div>
            </div>
            
            <div style={{display:'flex', gap:8}}>
              <button 
                onClick={saveOfferPlan}
                style={{flex:1, backgroundColor:'#3b82f6', color:'white', border:'none', padding:'8px', borderRadius:4}}
              >
                {editingOfferPlan ? 'Update Plan' : 'Create Plan'}
              </button>
              <button 
                onClick={() => setShowOfferPlanModal(false)}
                style={{flex:1, backgroundColor:'#6b7280', color:'white', border:'none', padding:'8px', borderRadius:4}}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Plan Selection Modal */}
      {showPlanSelectionModal && companyForPlanAssignment && (
        <div style={{position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(0,0,0,0.6)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1004}}>
          <div style={{background:'white', borderRadius:12, padding:32, width:'90%', maxWidth:1200, maxHeight:'85vh', overflow:'auto'}}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:24}}>
              <div>
                <h2 style={{margin:0, color:'#1f2937'}}>Select Subscription Plan</h2>
                <p style={{margin:'8px 0 0 0', color:'#6b7280'}}>Choose a plan to assign to <strong>{companyForPlanAssignment.name}</strong></p>
              </div>
              <button 
                onClick={() => {
                  setShowPlanSelectionModal(false);
                  setCompanyForPlanAssignment(null);
                }} 
                style={{background:'none', border:'none', fontSize:28, cursor:'pointer', color:'#6b7280'}}
              >
                ×
              </button>
            </div>
            
            {/* Plan Cards Grid */}
            <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(300px, 1fr))', gap:20}}>
              {offerPlans
                .filter(plan => plan.status === 'Active')
                .map(plan => (
                <div 
                  key={plan.id}
                  onClick={() => assignPlanToCompany(plan)}
                  style={{
                    border:'2px solid #e5e7eb',
                    borderRadius:12,
                    padding:24,
                    cursor:'pointer',
                    transition:'all 0.2s',
                    background:'white',
                    position:'relative',
                    overflow:'hidden'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#8b5cf6';
                    e.currentTarget.style.transform = 'translateY(-4px)';
                    e.currentTarget.style.boxShadow = '0 12px 24px rgba(139, 92, 246, 0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#e5e7eb';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  {/* Plan Header */}
                  <div style={{marginBottom:16}}>
                    <div style={{
                      display:'inline-block',
                      background:'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                      color:'white',
                      padding:'6px 16px',
                      borderRadius:20,
                      fontSize:12,
                      fontWeight:600,
                      marginBottom:12
                    }}>
                      {plan.plan_name}
                    </div>
                    <div style={{fontSize:36, fontWeight:'bold', color:'#1f2937'}}>
                      ${plan.price}
                      <span style={{fontSize:16, color:'#6b7280', fontWeight:400}}>/month</span>
                    </div>
                  </div>

                  {/* Plan Features */}
                  <div style={{marginBottom:20}}>
                    <div style={{display:'flex', alignItems:'center', padding:'8px 0', borderBottom:'1px solid #f3f4f6'}}>
                      <span style={{fontSize:14, color:'#059669', marginRight:8}}>✓</span>
                      <span style={{fontSize:14, color:'#374151'}}>
                        {plan.job_post_limit ? `${plan.job_post_limit} Job Posts` : 'Unlimited Job Posts'}
                      </span>
                    </div>
                    <div style={{display:'flex', alignItems:'center', padding:'8px 0', borderBottom:'1px solid #f3f4f6'}}>
                      <span style={{fontSize:14, color:'#059669', marginRight:8}}>✓</span>
                      <span style={{fontSize:14, color:'#374151'}}>
                        {plan.recruiter_limit} Recruiter{plan.recruiter_limit > 1 ? 's' : ''}
                      </span>
                    </div>
                    <div style={{display:'flex', alignItems:'center', padding:'8px 0', borderBottom:'1px solid #f3f4f6'}}>
                      <span style={{fontSize:14, color:'#059669', marginRight:8}}>✓</span>
                      <span style={{fontSize:14, color:'#374151'}}>
                        {plan.candidate_views ? `${plan.candidate_views.toLocaleString()} Candidate Views` : 'Unlimited Candidate Views'}
                      </span>
                    </div>
                    <div style={{display:'flex', alignItems:'center', padding:'8px 0', borderBottom:'1px solid #f3f4f6'}}>
                      <span style={{fontSize:14, color:'#059669', marginRight:8}}>✓</span>
                      <span style={{fontSize:14, color:'#374151'}}>
                        {plan.analytics_level} Analytics
                      </span>
                    </div>
                    <div style={{display:'flex', alignItems:'center', padding:'8px 0'}}>
                      <span style={{fontSize:14, color:'#059669', marginRight:8}}>✓</span>
                      <span style={{fontSize:14, color:'#374151'}}>
                        {plan.support_level} Support
                      </span>
                    </div>
                  </div>

                  {/* Select Button */}
                  <button
                    style={{
                      width:'100%',
                      background:'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                      color:'white',
                      border:'none',
                      padding:'12px',
                      borderRadius:8,
                      fontSize:14,
                      fontWeight:600,
                      cursor:'pointer'
                    }}
                  >
                    Select This Plan
                  </button>
                </div>
              ))}
            </div>

            {offerPlans.filter(plan => plan.status === 'Active').length === 0 && (
              <div style={{textAlign:'center', padding:60, color:'#6b7280'}}>
                <p style={{fontSize:18, marginBottom:12}}>No active offer plans available</p>
                <p style={{fontSize:14}}>Please create offer plans in the "Offer Plans" tab first.</p>
              </div>
            )}

            <div style={{marginTop:24, textAlign:'center'}}>
              <button 
                onClick={() => {
                  setShowPlanSelectionModal(false);
                  setCompanyForPlanAssignment(null);
                }}
                style={{
                  backgroundColor:'#6b7280',
                  color:'white',
                  border:'none',
                  padding:'10px 24px',
                  borderRadius:6,
                  cursor:'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuperAdminDashboard;


