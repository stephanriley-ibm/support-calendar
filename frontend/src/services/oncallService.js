import api from './api';

const oncallService = {
  /**
   * Get all on-call shifts
   */
  getShifts: async (params = {}) => {
    const response = await api.get('/oncall/shifts/', { params });
    return response.data;
  },

  /**
   * Get my on-call shifts
   */
  getMyShifts: async () => {
    const response = await api.get('/oncall/shifts/my_shifts/');
    return response.data;
  },

  /**
   * Get upcoming shifts
   */
  getUpcoming: async (days = 90, teamId = null) => {
    const params = { days };
    if (teamId) {
      params.team = teamId;
    }
    const response = await api.get('/oncall/shifts/upcoming/', { params });
    return response.data;
  },

  /**
   * Get shift details
   */
  getShift: async (id) => {
    const response = await api.get(`/oncall/shifts/${id}/`);
    return response.data;
  },

  /**
   * Create on-call shift (manual, for holidays)
   */
  createShift: async (data) => {
    const response = await api.post('/oncall/shifts/', data);
    return response.data;
  },

  /**
   * Update on-call shift
   */
  updateShift: async (id, data) => {
    const response = await api.patch(`/oncall/shifts/${id}/`, data);
    return response.data;
  },

  /**
   * Delete on-call shift
   */
  deleteShift: async (id) => {
    const response = await api.delete(`/oncall/shifts/${id}/`);
    return response.data;
  },

  /**
   * Generate rotation for a date range
   * @param {string} startDate - Start date in YYYY-MM-DD format
   * @param {string} endDate - End date in YYYY-MM-DD format
   * @param {Array<number>|number} teamIds - Array of team IDs or single team ID
   */
  generateRotation: async (startDate, endDate, teamIds) => {
    const payload = {
      start_date: startDate,
      end_date: endDate,
    };
    
    // Handle both array and single value for backward compatibility
    if (Array.isArray(teamIds)) {
      payload.team_ids = teamIds;
    } else if (teamIds) {
      payload.team_id = teamIds;
    }
    
    const response = await api.post('/oncall/shifts/generate_rotation/', payload);
    return response.data;
  },

  /**
   * Get rotation preview
   * @param {string} startDate - Start date in YYYY-MM-DD format
   * @param {string} endDate - End date in YYYY-MM-DD format
   * @param {Array<number>|number} teamIds - Array of team IDs or single team ID
   */
  previewRotation: async (startDate, endDate, teamIds) => {
    const payload = {
      start_date: startDate,
      end_date: endDate,
    };
    
    // Handle both array and single value for backward compatibility
    if (Array.isArray(teamIds)) {
      payload.team_ids = teamIds;
    } else if (teamIds) {
      payload.team_id = teamIds;
    }
    
    const response = await api.post('/oncall/shifts/preview_rotation/', payload);
    return response.data;
  },

  /**
   * Delete rotation for a date range
   * @param {string} startDate - Start date in YYYY-MM-DD format
   * @param {string} endDate - End date in YYYY-MM-DD format
   * @param {Array<number>} teamIds - Optional array of team IDs to filter deletion
   */
  deleteRotation: async (startDate, endDate, teamIds = null) => {
    const payload = {
      start_date: startDate,
      end_date: endDate,
    };
    
    if (teamIds && teamIds.length > 0) {
      payload.team_ids = teamIds;
    }
    
    const response = await api.post('/oncall/shifts/delete_rotation/', payload);
    return response.data;
  },

  /**
   * Get all holidays
   */
  getHolidays: async (params = {}) => {
    const response = await api.get('/oncall/holidays/', { params });
    return response.data;
  },

  /**
   * Get holiday details
   */
  getHoliday: async (id) => {
    const response = await api.get(`/oncall/holidays/${id}/`);
    return response.data;
  },

  /**
   * Create holiday
   */
  createHoliday: async (data) => {
    const response = await api.post('/oncall/holidays/', data);
    return response.data;
  },

  /**
   * Update holiday
   */
  updateHoliday: async (id, data) => {
    const response = await api.patch(`/oncall/holidays/${id}/`, data);
    return response.data;
  },

  /**
   * Delete holiday
   */
  deleteHoliday: async (id) => {
    const response = await api.delete(`/oncall/holidays/${id}/`);
    return response.data;
  },

  /**
   * Get all days in lieu
   */
  getDaysInLieu: async (params = {}) => {
    const response = await api.get('/oncall/days-in-lieu/', { params });
    return response.data;
  },

  /**
   * Get my days in lieu
   */
  getMyDaysInLieu: async () => {
    const response = await api.get('/oncall/days-in-lieu/my_days/');
    return response.data;
  },

  /**
   * Get pending days in lieu (coach view)
   */
  getPendingDaysInLieu: async () => {
    const response = await api.get('/oncall/days-in-lieu/', {
      params: { status: 'scheduled' }
    });
    return response.data;
  },

  /**
   * Get day in lieu details
   */
  getDayInLieu: async (id) => {
    const response = await api.get(`/oncall/days-in-lieu/${id}/`);
    return response.data;
  },

  /**
   * Update day in lieu (coach adjustment)
   */
  updateDayInLieu: async (id, data) => {
    const response = await api.patch(`/oncall/days-in-lieu/${id}/`, data);
    return response.data;
  },

  /**
   * Reschedule day in lieu (coach only)
   */
  rescheduleDayInLieu: async (id, newDate, reason) => {
    const response = await api.post(`/oncall/days-in-lieu/${id}/reschedule/`, {
      new_date: newDate,
      reason: reason,
    });
    return response.data;
  },

  /**
   * Mark day in lieu as used
   */
  markUsed: async (id) => {
    const response = await api.post(`/oncall/days-in-lieu/${id}/mark_used/`);
    return response.data;
  },
};

export default oncallService;

// Made with Bob
