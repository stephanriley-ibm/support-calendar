import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Login.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState('');
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  // Clear error when user starts typing (but only if they change the value after error)
  const [lastErrorUsername, setLastErrorUsername] = useState('');
  const [lastErrorPassword, setLastErrorPassword] = useState('');

  useEffect(() => {
    if (localError) {
      // Only clear if user actually changed the input after the error
      if (username !== lastErrorUsername || password !== lastErrorPassword) {
        setLocalError('');
      }
    }
  }, [username, password, localError, lastErrorUsername, lastErrorPassword]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLocalError('');

    try {
      const response = await login(username, password);
      
      // Check if user must change password
      if (response.must_change_password || response.user?.must_change_password) {
        navigate('/change-password');
      } else {
        navigate('/');
      }
    } catch (err) {
      // Set local error that persists and remember the values that caused the error
      const errorMsg = err.message || 'Login failed. Please check your credentials and try again.';
      console.log('Setting error:', errorMsg); // Debug log
      setLocalError(errorMsg);
      setLastErrorUsername(username);
      setLastErrorPassword(password);
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Calendar App</h1>
        <h2>Sign In</h2>
        
        {localError && (
          <div className="error-message" style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#fee', border: '1px solid #fcc', borderRadius: '4px', color: '#c33' }}>
            {localError}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button 
            type="submit" 
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;

// Made with Bob
