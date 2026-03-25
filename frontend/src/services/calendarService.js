import api from './api';

const calendarService = {
  /**
   * Get calendar events
   */
  getEvents: async (startDate, endDate, filter = 'user', teamId = null, eventTypes = null) => {
    const params = {
      start_date: startDate,
      end_date: endDate,
      filter,
    };
    
    if (teamId) {
      params.team_id = teamId;
    }
    
    if (eventTypes && eventTypes.length > 0) {
      params.event_types = eventTypes;
    }
    
    const response = await api.get('/calendar/', { params });
    return response.data;
  },

  /**
   * Get calendar summary
   */
  getSummary: async (startDate, endDate, filter = 'user', teamId = null) => {
    const params = {
      start_date: startDate,
      end_date: endDate,
      filter,
    };
    
    if (teamId) {
      params.team_id = teamId;
    }
    
    const response = await api.get('/calendar/summary/', { params });
    return response.data;
  },
};

export default calendarService;

// Made with Bob
