import React, { createContext, useState, useContext, useEffect } from 'react';
import authService from '../services/authService';
import userService from '../services/userService';
import { getBrowserTimezone } from '../utils/timezoneUtils';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load user on mount if token exists
  useEffect(() => {
    const initAuth = async () => {
      if (authService.isAuthenticated()) {
        try {
          const userData = await authService.getCurrentUser();
          
          // Auto-detect and set timezone if not already set
          if (!userData.timezone || userData.timezone === 'UTC') {
            const browserTimezone = getBrowserTimezone();
            try {
              await userService.updateUser(userData.id, { timezone: browserTimezone });
              userData.timezone = browserTimezone;
            } catch (err) {
              console.error('Failed to set timezone:', err);
            }
          }
          
          setUser(userData);
        } catch (err) {
          console.error('Failed to load user:', err);
          authService.logout();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username, password) => {
    try {
      setError(null);
      const response = await authService.login(username, password);
      setUser(response.user);
      return response;
    } catch (err) {
      // Handle different error response formats
      let errorMessage = 'Login failed. Please try again.';
      
      if (err.response?.data) {
        // Check for different error formats from backend
        if (err.response.data.error) {
          errorMessage = err.response.data.error;
        } else if (err.response.data.detail) {
          errorMessage = err.response.data.detail;
        } else if (err.response.data.message) {
          errorMessage = err.response.data.message;
        } else if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setError(null);
  };

  const updateUser = (userData) => {
    setUser(userData);
  };

  const getUserTimezone = () => {
    return user?.timezone || getBrowserTimezone();
  };

  const hasRole = (role) => {
    return authService.hasRole(user, role);
  };

  const isCoach = () => {
    return authService.isCoach(user);
  };

  const isAdmin = () => {
    return authService.isAdmin(user);
  };

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    updateUser,
    getUserTimezone,
    hasRole,
    isCoach,
    isAdmin,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;

// Made with Bob
