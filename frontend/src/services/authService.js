import api from './api';

const authService = {
  /**
   * Login user
   */
  login: async (username, password) => {
    const response = await api.post('/auth/users/login/', {
      username,
      password,
    });
    
    if (response.data.token) {
      localStorage.setItem('authToken', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    
    return response.data;
  },

  /**
   * Logout user
   */
  logout: async () => {
    try {
      await api.post('/auth/users/logout/');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
    }
  },

  /**
   * Get current user
   */
  getCurrentUser: async () => {
    const response = await api.get('/auth/users/me/');
    localStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: () => {
    return !!localStorage.getItem('authToken');
  },

  /**
   * Get stored user data
   */
  getUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Check if user has specific role
   */
  hasRole: (role) => {
    const user = authService.getUser();
    return user?.role === role;
  },

  /**
   * Check if user is coach
   */
  isCoach: () => {
    return authService.hasRole('coach');
  },

  /**
   * Check if user is admin
   */
  isAdmin: () => {
    return authService.hasRole('admin');
  },

  /**
   * Check if user is engineer
   */
  isEngineer: () => {
    return authService.hasRole('engineer');
  },
};

export default authService;

// Made with Bob
