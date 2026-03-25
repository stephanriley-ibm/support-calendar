import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './ChangePassword.css';

function ChangePassword() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    old_password: '',
    new_password: '',
    new_password_confirm: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.new_password !== formData.new_password_confirm) {
      setError('New passwords do not match');
      return;
    }

    if (formData.new_password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);

    try {
      await api.post('/auth/users/change_password/', formData);
      setSuccess(true);
      
      // Wait 3 seconds before redirecting
      setTimeout(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
      }, 3000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to change password');
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="change-password-container">
        <div className="change-password-card success-card">
          <div className="success-icon">✓</div>
          <h2>Password Changed Successfully!</h2>
          <p className="success-message">
            Your password has been updated. You will be redirected to the login page in a moment...
          </p>
          <div className="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="change-password-container">
      <div className="change-password-card">
        <h2>Change Password</h2>
        <p className="change-password-notice">
          You must change your temporary password before continuing.
        </p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="old_password">Current Password</label>
            <input
              type="password"
              id="old_password"
              name="old_password"
              value={formData.old_password}
              onChange={handleChange}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="new_password">New Password</label>
            <input
              type="password"
              id="new_password"
              name="new_password"
              value={formData.new_password}
              onChange={handleChange}
              required
              minLength="8"
            />
            <small>Must be at least 8 characters long</small>
          </div>

          <div className="form-group">
            <label htmlFor="new_password_confirm">Confirm New Password</label>
            <input
              type="password"
              id="new_password_confirm"
              name="new_password_confirm"
              value={formData.new_password_confirm}
              onChange={handleChange}
              required
              minLength="8"
            />
          </div>

          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Changing Password...' : 'Change Password'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChangePassword;

// Made with Bob
