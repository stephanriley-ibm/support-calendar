import api from './api';

const timeoffService = {
  /**
   * Get all time-off requests
   */
  getRequests: async (params = {}) => {
    const response = await api.get('/timeoff/requests/', { params });
    return response.data;
  },

  /**
   * Get my time-off requests
   */
  getMyRequests: async () => {
    const response = await api.get('/timeoff/requests/my_requests/');
    return response.data;
  },

  /**
   * Get pending requests (coach view)
   */
  getPendingRequests: async () => {
    const response = await api.get('/timeoff/requests/pending/');
    return response.data;
  },

  /**
   * Get upcoming time-off
   */
  getUpcoming: async (days = 90, teamId = null) => {
    const params = { days };
    if (teamId) {
      params.team = teamId;
    }
    const response = await api.get('/timeoff/requests/upcoming/', { params });
    return response.data;
  },

  /**
   * Get request details
   */
  getRequest: async (id) => {
    const response = await api.get(`/timeoff/requests/${id}/`);
    return response.data;
  },

  /**
   * Create time-off request
   */
  createRequest: async (data) => {
    const response = await api.post('/timeoff/requests/', data);
    return response.data;
  },

  /**
   * Update time-off request
   */
  updateRequest: async (id, data) => {
    const response = await api.patch(`/timeoff/requests/${id}/`, data);
    return response.data;
  },

  /**
   * Cancel time-off request
   */
  cancelRequest: async (id) => {
    const response = await api.delete(`/timeoff/requests/${id}/`);
    return response.data;
  },

  /**
   * Approve time-off request
   */
  approveRequest: async (id) => {
    const response = await api.post(`/timeoff/requests/${id}/approve/`);
    return response.data;
  },

  /**
   * Reject time-off request
   */
  rejectRequest: async (id, reason) => {
    const response = await api.post(`/timeoff/requests/${id}/reject/`, {
      action: 'reject',
      rejection_reason: reason,
    });
    return response.data;
  },

  /**
   * Check for conflicts
   */
  checkConflicts: async (startDate, endDate, excludeRequestId = null) => {
    const data = {
      start_date: startDate,
      end_date: endDate,
    };
    
    if (excludeRequestId) {
      data.exclude_request_id = excludeRequestId;
    }
    
    const response = await api.post('/timeoff/requests/check_conflicts/', data);
    return response.data;
  },
};

export default timeoffService;

// Made with Bob
