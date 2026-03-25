import api from './api';

const userService = {
  /**
   * Get all users
   */
  getUsers: async (params = {}) => {
    const response = await api.get('/auth/users/', { params });
    return response.data;
  },

  /**
   * Get current user profile
   */
  getProfile: async () => {
    const response = await api.get('/auth/users/me/');
    return response.data;
  },

  /**
   * Get user details
   */
  getUser: async (id) => {
    const response = await api.get(`/auth/users/${id}/`);
    return response.data;
  },

  /**
   * Update user profile
   */
  updateProfile: async (data) => {
    const response = await api.patch('/auth/users/me/', data);
    return response.data;
  },

  /**
   * Update user
   */
  updateUser: async (id, data) => {
    const response = await api.patch(`/auth/users/${id}/`, data);
    return response.data;
  },

  /**
   * Create user (admin only)
   */
  createUser: async (data) => {
    const response = await api.post('/auth/users/', data);
    return response.data;
  },

  /**
   * Delete user (admin only)
   */
  deleteUser: async (id) => {
    const response = await api.delete(`/auth/users/${id}/`);
    return response.data;
  },

  /**
   * Get all teams
   */
  getTeams: async (params = {}) => {
    const response = await api.get('/auth/teams/', { params });
    return response.data;
  },

  /**
   * Get team details
   */
  getTeam: async (id) => {
    const response = await api.get(`/auth/teams/${id}/`);
    return response.data;
  },

  /**
   * Get team members
   */
  getTeamMembers: async (id) => {
    const response = await api.get(`/auth/teams/${id}/members/`);
    return response.data;
  },

  /**
   * Create team (admin only)
   */
  createTeam: async (data) => {
    const response = await api.post('/auth/teams/', data);
    return response.data;
  },

  /**
   * Update team
   */
  updateTeam: async (id, data) => {
    const response = await api.patch(`/auth/teams/${id}/`, data);
    return response.data;
  },

  /**
   * Delete team (admin only)
   */
  deleteTeam: async (id) => {
    const response = await api.delete(`/auth/teams/${id}/`);
    return response.data;
  },

  /**
   * Add member to team
   */
  addTeamMember: async (teamId, userId) => {
    const response = await api.post(`/auth/teams/${teamId}/add_member/`, {
      user_id: userId,
    });
    return response.data;
  },

  /**
   * Remove member from team
   */
  removeTeamMember: async (teamId, userId) => {
    const response = await api.post(`/auth/teams/${teamId}/remove_member/`, {
      user_id: userId,
    });
    return response.data;
  },

  /**
   * Reset user password - generates new temporary password
   * Admin can reset any user, Coach can reset their team members
   */
  resetPassword: async (userId) => {
    const response = await api.post(`/auth/users/${userId}/reset_password/`);
    return response.data;
  },
};

export default userService;

// Made with Bob
