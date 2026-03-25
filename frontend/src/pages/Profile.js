import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import userService from '../services/userService';
import { COMMON_TIMEZONES, getBrowserTimezone, getTimezoneOffset } from '../utils/timezoneUtils';
import './Profile.css';

const Profile = () => {
  const { user, updateUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    username: user?.username || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    timezone: user?.timezone || 'UTC',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleDetectTimezone = () => {
    const detected = getBrowserTimezone();
    setFormData(prev => ({
      ...prev,
      timezone: detected,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);

    try {
      const updated = await userService.updateUser(user.id, formData);
      // Merge updated data with existing user data to preserve all fields
      updateUser({ ...user, ...updated });
      setSuccess('Profile updated successfully!');
      setEditing(false);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Failed to update profile:', err);
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      username: user?.username || '',
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
      timezone: user?.timezone || 'UTC',
    });
    setEditing(false);
    setError(null);
  };

  if (!user) {
    return <div className="loading-spinner"><div className="spinner"></div></div>;
  }

  return (
    <div className="profile-page">
      <div className="page-header">
        <h1>My Profile</h1>
      </div>

      {success && (
        <div className="alert alert-success">{success}</div>
      )}

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      <div className="profile-card">
        <div className="profile-header">
          <div className="profile-avatar">
            {user.first_name?.[0] || user.username?.[0] || user.email?.[0] || 'U'}
          </div>
          <div className="profile-title">
            <h2>{user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : user.username || user.email}</h2>
            <p className="profile-subtitle">{user.username ? `@${user.username}` : user.email} • {user.role}</p>
          </div>
        </div>

        <div className="profile-section">
          {!editing ? (
            <div className="profile-view">
              <div className="profile-grid">
                <div className="profile-field">
                  <label>Username</label>
                  <div className="field-value">{user.username || user.email || 'Not set'}</div>
                </div>

                <div className="profile-field">
                  <label>Email</label>
                  <div className="field-value">{user.email}</div>
                </div>

                <div className="profile-field">
                  <label>First Name</label>
                  <div className="field-value">{user.first_name || '-'}</div>
                </div>

                <div className="profile-field">
                  <label>Last Name</label>
                  <div className="field-value">{user.last_name || '-'}</div>
                </div>

                <div className="profile-field role-field">
                  <label>Role</label>
                  <div className="field-value">{user.role}</div>
                </div>

                <div className="profile-field">
                  <label>Team</label>
                  <div className="field-value">{user.team_name || 'No team assigned'}</div>
                </div>

                <div className="profile-field full-width">
                  <label>Timezone</label>
                  <div className="field-value">
                    {user.timezone} <span className="timezone-offset">({getTimezoneOffset(user.timezone)})</span>
                  </div>
                </div>
              </div>

              <div className="profile-actions">
                <button onClick={() => setEditing(true)} className="btn btn-primary">
                  Edit Profile
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="profile-form">
              <div className="form-group">
                <label htmlFor="username">Username *</label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label htmlFor="email">Email *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label htmlFor="first_name">First Name</label>
                <input
                  type="text"
                  id="first_name"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label htmlFor="last_name">Last Name</label>
                <input
                  type="text"
                  id="last_name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label htmlFor="timezone">Timezone *</label>
                <div className="timezone-input-group">
                  <select
                    id="timezone"
                    name="timezone"
                    value={formData.timezone}
                    onChange={handleChange}
                    required
                    disabled={saving}
                  >
                    {COMMON_TIMEZONES.map(tz => (
                      <option key={tz.value} value={tz.value}>
                        {tz.label}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={handleDetectTimezone}
                    className="btn btn-secondary btn-sm"
                    disabled={saving}
                    title="Detect timezone from browser"
                  >
                    Auto-detect
                  </button>
                </div>
                <small className="form-help">
                  Current: {formData.timezone} ({getTimezoneOffset(formData.timezone)})
                </small>
              </div>

              <div className="form-actions">
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
                <button type="button" onClick={handleCancel} className="btn btn-secondary" disabled={saving}>
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;

// Made with Bob
