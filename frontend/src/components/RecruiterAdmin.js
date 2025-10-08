import React, { useState, useEffect } from 'react';
import './RecruiterAdmin.css';

const RecruiterAdmin = () => {
  const [recruiters, setRecruiters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingRecruiter, setEditingRecruiter] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    role_filter: '',
    is_active: null
  });

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    password: '',
    password_confirm: '',
    company_name: '',
    domain: '',
    company_size: '',
    company_description: '',
    role: 'recruiter',
    is_active: true
  });

  // Fetch recruiters (company-isolated)
  const fetchRecruiters = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.role_filter) params.append('role_filter', filters.role_filter);
      if (filters.is_active !== null) params.append('is_active', filters.is_active);

      const response = await fetch(`http://localhost:8000/api/v1/recruiter-fast/admin/list-fast?${params}`);
      if (response.ok) {
        const data = await response.json();
        setRecruiters(data);
      } else {
        setError('Failed to fetch recruiters');
      }
    } catch (error) {
      setError('Error fetching recruiters: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecruiters();
  }, [filters]);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const url = editingRecruiter 
        ? `http://localhost:8000/api/v1/recruiter-fast/admin/update-fast/${editingRecruiter.id}`
        : 'http://localhost:8000/api/v1/recruiter-fast/admin/create-fast';
      
      const method = editingRecruiter ? 'PUT' : 'POST';
      
      const submitData = { ...formData };
      if (!editingRecruiter) {
        // For new recruiters, include password confirmation
        if (submitData.password !== submitData.password_confirm) {
          setError('Passwords do not match');
          return;
        }
      } else {
        // For updates, remove password fields if empty
        if (!submitData.password) {
          delete submitData.password;
          delete submitData.password_confirm;
        }
      }

      let requestBody;
      if (!editingRecruiter) {
        // For new recruiters, use fast endpoint format
        requestBody = {
          full_name: submitData.full_name,
          email: submitData.email,
          password: submitData.password,
          phone_number: submitData.phone_number || "",
          company_name: submitData.company_name,
          domain: submitData.domain,
          company_size: submitData.company_size,
          company_description: submitData.company_description || "",
          role: submitData.role
        };
      } else {
        // For updates, use original format
        requestBody = submitData;
      }

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const result = await response.json();
        setMessage(editingRecruiter ? 'Recruiter updated successfully!' : 'Recruiter created successfully!');
        resetForm();
        fetchRecruiters();
        
        // Clear message after 3 seconds
        setTimeout(() => setMessage(''), 3000);
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail) || 'Failed to save recruiter';
        setError(errorMessage);
      }
    } catch (error) {
      setError('Error saving recruiter: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      full_name: '',
      email: '',
      phone_number: '',
      password: '',
      password_confirm: '',
      company_name: '',
      domain: '',
      company_size: '',
      company_description: '',
      role: 'recruiter',
      is_active: true
    });
    setEditingRecruiter(null);
    setShowForm(false);
  };

  // Edit recruiter
  const handleEdit = (recruiter) => {
    setFormData({
      full_name: recruiter.full_name,
      email: recruiter.email,
      phone_number: recruiter.phone_number || '',
      password: '',
      password_confirm: '',
      company_name: recruiter.company_name,
      domain: recruiter.domain,
      company_size: recruiter.company_size,
      company_description: recruiter.company_description || '',
      role: recruiter.role,
      is_active: recruiter.is_active
    });
    setEditingRecruiter(recruiter);
    setShowForm(true);
  };

  // Toggle recruiter status
  const handleToggleStatus = async (recruiterId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/recruiter-fast/admin/toggle-status-fast/${recruiterId}`, {
        method: 'PUT'
      });
      
      if (response.ok) {
        fetchRecruiters();
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail) || 'Failed to toggle status';
        setError(errorMessage);
      }
    } catch (error) {
      setError('Error toggling status: ' + error.message);
    }
  };

  // Delete recruiter
  const handleDelete = async (recruiterId, recruiterName) => {
    if (!window.confirm(`Are you sure you want to delete ${recruiterName}? This action cannot be undone.`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/v1/recruiter-fast/admin/delete-fast/${recruiterId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        fetchRecruiters();
      } else {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail) || 'Failed to delete recruiter';
        setError(errorMessage);
      }
    } catch (error) {
      setError('Error deleting recruiter: ' + error.message);
    }
  };

  return (
    <div className="recruiter-admin">
      <div className="admin-header">
        <h1>Recruiter Management</h1>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setShowForm(true)}
          >
            ➕ Add New Recruiter
          </button>
          <button 
            className="btn-back"
            onClick={() => window.location.href = '/jobs-dashboard'}
          >
            ← Back to Dashboard
          </button>
          <button 
            className="btn-logout"
            onClick={() => {
              localStorage.removeItem('token');
              window.location.href = '/';
            }}
          >
            🚪 Logout
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {String(error)}
        </div>
      )}

      {message && (
        <div className="alert alert-success">
          {String(message)}
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Search by name, email, or company..."
            value={filters.search}
            onChange={(e) => setFilters({...filters, search: e.target.value})}
            className="form-input"
          />
        </div>
        <div className="filter-group">
          <select
            value={filters.role_filter}
            onChange={(e) => setFilters({...filters, role_filter: e.target.value})}
            className="form-input"
          >
            <option value="">All Roles</option>
            <option value="admin">Admin</option>
            <option value="recruiter">Recruiter</option>
          </select>
        </div>
        <div className="filter-group">
          <select
            value={filters.is_active === null ? '' : filters.is_active.toString()}
            onChange={(e) => setFilters({
              ...filters, 
              is_active: e.target.value === '' ? null : e.target.value === 'true'
            })}
            className="form-input"
          >
            <option value="">All Status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
      </div>

      {/* Recruiters Table */}
      <div className="recruiters-table">
        {loading ? (
          <div className="loading">Loading recruiters...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Company</th>
                <th>Role</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {recruiters.map(recruiter => (
                <tr key={recruiter.id}>
                  <td>{String(recruiter.full_name || '')}</td>
                  <td>{String(recruiter.email || '')}</td>
                  <td>{String(recruiter.company_name || '')}</td>
                  <td>
                    <span className={`role-badge ${recruiter.role}`}>
                      {String(recruiter.role || '')}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${recruiter.is_active ? 'active' : 'inactive'}`}>
                      {recruiter.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button 
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleEdit(recruiter)}
                      >
                        Edit
                      </button>
                      <button 
                        className={`btn btn-sm ${recruiter.is_active ? 'btn-warning' : 'btn-success'}`}
                        onClick={() => handleToggleStatus(recruiter.id)}
                      >
                        {recruiter.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                      <button 
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDelete(recruiter.id, recruiter.full_name)}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add/Edit Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => resetForm()}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingRecruiter ? 'Edit Recruiter' : 'Add New Recruiter'}</h2>
              <button className="modal-close" onClick={() => resetForm()}>✕</button>
            </div>
            
            <form onSubmit={handleSubmit} className="recruiter-form">
              <div className="form-grid">
                <div className="form-group">
                  <label>Full Name *</label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                    required
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Phone Number</label>
                  <input
                    type="tel"
                    value={formData.phone_number}
                    onChange={(e) => setFormData({...formData, phone_number: e.target.value})}
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Company Name *</label>
                  <input
                    type="text"
                    value={formData.company_name}
                    onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                    required
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Domain *</label>
                  <select
                    value={formData.domain}
                    onChange={(e) => setFormData({...formData, domain: e.target.value})}
                    required
                    className="form-input"
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
                </div>
                
                <div className="form-group">
                  <label>Company Size *</label>
                  <select
                    value={formData.company_size}
                    onChange={(e) => setFormData({...formData, company_size: e.target.value})}
                    required
                    className="form-input"
                  >
                    <option value="">Select Company Size</option>
                    <option value="1-10">1-10</option>
                    <option value="11-50">11-50</option>
                    <option value="51-200">51-200</option>
                    <option value="201-500">201-500</option>
                    <option value="501-1000">501-1000</option>
                    <option value="1000+">1000+</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Role *</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                    required
                    className="form-input"
                  >
                    <option value="recruiter">Recruiter</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Status</label>
                  <select
                    value={formData.is_active.toString()}
                    onChange={(e) => setFormData({...formData, is_active: e.target.value === 'true'})}
                    className="form-input"
                  >
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                  </select>
                </div>
              </div>
              
              <div className="form-group">
                <label>Company Description</label>
                <textarea
                  value={formData.company_description}
                  onChange={(e) => setFormData({...formData, company_description: e.target.value})}
                  rows="3"
                  className="form-input"
                />
              </div>
              
              {!editingRecruiter && (
                <div className="form-grid">
                  <div className="form-group">
                    <label>Password *</label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({...formData, password: e.target.value})}
                      required
                      className="form-input"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Confirm Password *</label>
                    <input
                      type="password"
                      value={formData.password_confirm}
                      onChange={(e) => setFormData({...formData, password_confirm: e.target.value})}
                      required
                      className="form-input"
                    />
                  </div>
                </div>
              )}
              
              {editingRecruiter && (
                <div className="form-grid">
                  <div className="form-group">
                    <label>New Password (leave empty to keep current)</label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({...formData, password: e.target.value})}
                      className="form-input"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Confirm New Password</label>
                    <input
                      type="password"
                      value={formData.password_confirm}
                      onChange={(e) => setFormData({...formData, password_confirm: e.target.value})}
                      className="form-input"
                    />
                  </div>
                </div>
              )}
              
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => resetForm()}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : (editingRecruiter ? 'Update Recruiter' : 'Create Recruiter')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecruiterAdmin;
