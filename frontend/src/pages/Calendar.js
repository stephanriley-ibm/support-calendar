import React, { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import { useAuth } from '../contexts/AuthContext';
import calendarService from '../services/calendarService';
import userService from '../services/userService';
import timeoffService from '../services/timeoffService';
import './Calendar.css';

const Calendar = () => {
  const { user, isCoach } = useAuth();
  const [events, setEvents] = useState([]);
  const [allEvents, setAllEvents] = useState([]); // Store all events before filtering
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // Default to 'team' view for coaches, 'my' for others
  const [filter, setFilter] = useState(isCoach() ? 'team' : 'my');
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState('');
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [eventTypeFilter, setEventTypeFilter] = useState({
    timeoff: true,
    oncall: true,
    day_in_lieu: true,
  });

  useEffect(() => {
    loadTeams();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadEvents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter, selectedTeam]);

  const loadTeams = async () => {
    try {
      const response = await userService.getTeams();
      // Handle paginated response
      const teamsData = response.results || response || [];
      setTeams(teamsData);
      
      // Auto-select coach's team if they're a coach
      if (isCoach() && user.team && teamsData.length > 0) {
        setSelectedTeam(user.team.toString());
      }
    } catch (err) {
      console.error('Failed to load teams:', err);
      setTeams([]);
    }
  };

  const loadEvents = async () => {
    try {
      setLoading(true);
      setError(null);

      // Calculate date range (load full year to show all generated events)
      const today = new Date();
      const startOfYear = new Date(today.getFullYear(), 0, 1);
      const endOfYear = new Date(today.getFullYear(), 11, 31);
      const startDate = startOfYear.toISOString().split('T')[0];
      const endDate = endOfYear.toISOString().split('T')[0];

      // Determine filter type
      let filterType = 'user';
      let teamId = null;
      
      if (filter === 'my') {
        filterType = 'user';
      } else if (filter === 'team' && selectedTeam) {
        filterType = 'team';
        teamId = selectedTeam;
      } else if (filter === 'all') {
        filterType = 'organization';
      }

      const response = await calendarService.getEvents(startDate, endDate, filterType, teamId);
      const eventsData = response.events || [];
      
      // Transform events for FullCalendar
      const formattedEvents = eventsData.map(event => {
        // Convert details object to string if needed
        let detailsText = event.details;
        if (typeof event.details === 'object' && event.details !== null) {
          const parts = [];
          
          // For on-call shifts
          if (event.type && event.type.startsWith('oncall')) {
            if (event.details.shift_type_display) {
              parts.push(`Shift: ${event.details.shift_type_display}`);
            } else if (event.details.shift_type) {
              parts.push(`Shift: ${event.details.shift_type.replace(/_/g, ' ')}`);
            }
            if (event.details.day_of_week) {
              parts.push(`Day: ${event.details.day_of_week}`);
            }
            if (event.details.start_time && event.details.end_time) {
              parts.push(`Time: ${event.details.start_time} - ${event.details.end_time}`);
            }
            if (event.details.holiday) {
              parts.push(`Holiday: ${event.details.holiday}`);
            }
          }
          // For time-off requests
          else if (event.type === 'timeoff') {
            if (event.details.reason) parts.push(`Reason: ${event.details.reason}`);
            if (event.details.duration_days) parts.push(`Duration: ${event.details.duration_days} day${event.details.duration_days > 1 ? 's' : ''}`);
            if (event.details.approved_by) parts.push(`Approved by: ${event.details.approved_by}`);
          }
          // For days in lieu
          else if (event.type === 'day_in_lieu') {
            if (event.details.oncall_date) parts.push(`For on-call: ${event.details.oncall_date}`);
            if (event.details.status) parts.push(`Status: ${event.details.status}`);
          }
          
          detailsText = parts.length > 0 ? parts.join(' | ') : null;
        }
        
        return {
          id: event.id,
          title: event.title,
          start: event.start,
          end: event.end,
          backgroundColor: getEventColor(event.type),
          borderColor: getEventColor(event.type),
          extendedProps: {
            id: event.id,
            type: event.type,
            status: event.status,
            user: event.user?.name || event.user,
            userId: event.user?.id,
            details: detailsText,
          },
        };
      });

      setAllEvents(formattedEvents);
      applyEventTypeFilter(formattedEvents);
    } catch (err) {
      console.error('Failed to load events:', err);
      setError('Failed to load calendar events');
    } finally {
      setLoading(false);
    }
  };

  const getEventColor = (type) => {
    const colors = {
      timeoff: '#667eea',
      oncall_early_primary: '#e74c3c',      // Red
      oncall_late_primary: '#e67e22',       // Orange
      oncall_secondary: '#f1c40f',          // Bright Yellow (changed for better differentiation)
      oncall_early_secondary: '#3498db',    // Blue (for Late Primary engineer doing Early Secondary)
      oncall_late_secondary: '#9b59b6',     // Purple (for Early Primary engineer doing Late Secondary)
      oncall_holiday: '#8b0000',            // Dark red for holiday shifts
      day_in_lieu: '#27ae60',               // Green
    };
    return colors[type] || '#95a5a6';
  };

  const applyEventTypeFilter = (eventsToFilter = allEvents) => {
    const filtered = eventsToFilter.filter(event => {
      const type = event.extendedProps.type;
      if (type === 'timeoff') return eventTypeFilter.timeoff;
      if (type === 'day_in_lieu') return eventTypeFilter.day_in_lieu;
      if (type && type.startsWith('oncall')) return eventTypeFilter.oncall;
      return true;
    });
    setEvents(filtered);
  };

  const handleEventTypeFilterChange = (filterType) => {
    const newFilter = {
      ...eventTypeFilter,
      [filterType]: !eventTypeFilter[filterType],
    };
    setEventTypeFilter(newFilter);
    
    // Apply filter to current events
    const filtered = allEvents.filter(event => {
      const type = event.extendedProps.type;
      if (type === 'timeoff') return newFilter.timeoff;
      if (type === 'day_in_lieu') return newFilter.day_in_lieu;
      if (type && type.startsWith('oncall')) return newFilter.oncall;
      return true;
    });
    setEvents(filtered);
  };

  const handleEventClick = (info) => {
    const event = info.event;
    const props = event.extendedProps;
    
    console.log('Event clicked:', props);
    console.log('User data:', props.user, 'Type:', typeof props.user);
    
    // Ensure user is always a string
    let userName = props.user;
    if (typeof props.user === 'object' && props.user !== null) {
      userName = props.user.name || JSON.stringify(props.user);
    }
    
    // Format details based on event type
    let formattedDetails = props.details;
    if (typeof props.details === 'object' && props.details !== null) {
      // For on-call shifts
      if (props.type && props.type.startsWith('oncall')) {
        const parts = [];
        if (props.details.shift_type) {
          parts.push(`Shift: ${props.details.shift_type.replace(/_/g, ' ')}`);
        }
        if (props.details.day_of_week) {
          parts.push(`Day: ${props.details.day_of_week}`);
        }
        if (props.details.start_time) {
          parts.push(`Time: ${props.details.start_time} - ${props.details.end_time || 'N/A'}`);
        }
        if (props.details.holiday) {
          parts.push(`Holiday: ${props.details.holiday}`);
        }
        formattedDetails = parts.length > 0 ? parts.join(' | ') : null;
      }
      // For time-off requests
      else if (props.type === 'timeoff') {
        const parts = [];
        if (props.details.reason) {
          parts.push(`Reason: ${props.details.reason}`);
        }
        if (props.details.duration_days) {
          parts.push(`Duration: ${props.details.duration_days} day${props.details.duration_days > 1 ? 's' : ''}`);
        }
        formattedDetails = parts.length > 0 ? parts.join(' | ') : null;
      }
      // For days in lieu
      else if (props.type === 'day_in_lieu') {
        const parts = [];
        if (props.details.oncall_date) {
          parts.push(`For on-call: ${props.details.oncall_date}`);
        }
        if (props.details.status) {
          parts.push(`Status: ${props.details.status}`);
        }
        formattedDetails = parts.length > 0 ? parts.join(' | ') : null;
      }
    }
    
    setSelectedEvent({
      id: props.id,
      title: event.title,
      type: props.type,
      status: props.status,
      user: userName,
      userId: props.userId || props.user?.id,
      details: formattedDetails,
      start: event.start,
      end: event.end,
    });
  };

  const handleEdit = async (eventId) => {
    // Navigate to Time Off Requests page with edit mode
    window.location.href = `/time-off?edit=${eventId}`;
  };

  const handleDelete = (event) => {
    setConfirmDelete(event);
  };

  const confirmDeleteRequest = async () => {
    try {
      await timeoffService.cancelRequest(confirmDelete.id);
      setConfirmDelete(null);
      setSelectedEvent(null);
      loadEvents();
    } catch (err) {
      console.error('Failed to delete request:', err);
      setErrorMessage('Failed to delete request');
    }
  };

  const closeModal = () => {
    setSelectedEvent(null);
  };

  const closeDeleteConfirm = () => {
    setConfirmDelete(null);
  };

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    if (newFilter === 'team') {
      // Auto-select user's team if they have one
      if (user.team) {
        setSelectedTeam(user.team.toString());
      }
    } else {
      setSelectedTeam('');
    }
  };

  if (loading && events.length === 0) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="calendar-page">
      <div className="calendar-header">
        <h1>Calendar</h1>
        
        <div className="calendar-filters">
          <div className="filter-group">
            <label>View:</label>
            <select 
              value={filter} 
              onChange={(e) => handleFilterChange(e.target.value)}
              className="filter-select"
            >
              <option value="my">My Calendar</option>
              <option value="team">Team Calendar</option>
              <option value="all">Organization</option>
            </select>
          </div>

          {filter === 'team' && (
            <div className="filter-group">
              <label>Team:</label>
              <select 
                value={selectedTeam} 
                onChange={(e) => setSelectedTeam(e.target.value)}
                className="filter-select"
              >
                <option value="">Select Team</option>
                {teams.map(team => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button onClick={loadEvents} className="btn btn-secondary">
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      <div className="calendar-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#667eea' }}></span>
          Time Off
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#e74c3c' }}></span>
          Early Primary
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#e67e22' }}></span>
          Late Primary
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#f1c40f' }}></span>
          Secondary
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#3498db' }}></span>
          Early Secondary
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#9b59b6' }}></span>
          Late Secondary
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#8b0000' }}></span>
          Holiday Shift
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#27ae60' }}></span>
          Day in Lieu
        </div>
      </div>

      <div className="event-type-filters">
        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={eventTypeFilter.timeoff}
            onChange={() => handleEventTypeFilterChange('timeoff')}
          />
          <span>Time Off</span>
        </label>
        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={eventTypeFilter.oncall}
            onChange={() => handleEventTypeFilterChange('oncall')}
          />
          <span>On-Call Shifts</span>
        </label>
        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={eventTypeFilter.day_in_lieu}
            onChange={() => handleEventTypeFilterChange('day_in_lieu')}
          />
          <span>Days in Lieu</span>
        </label>
      </div>

      <div className="calendar-container">
        <FullCalendar
          plugins={[dayGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          events={events}
          eventClick={handleEventClick}
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,dayGridWeek'
          }}
          height="auto"
          eventDisplay="block"
        />
      </div>

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="event-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedEvent.title}</h2>
              <button className="close-btn" onClick={closeModal}>×</button>
            </div>
            
            <div className="modal-body">
              <div className="event-detail">
                <strong>Type:</strong>
                <span>{selectedEvent.type.replace(/_/g, ' ').toUpperCase()}</span>
              </div>
              
              {selectedEvent.status && (
                <div className="event-detail">
                  <strong>Status:</strong>
                  <span className={`badge badge-${selectedEvent.status}`}>
                    {selectedEvent.status}
                  </span>
                </div>
              )}
              
              {selectedEvent.user && (
                <div className="event-detail">
                  <strong>User:</strong>
                  <span>{selectedEvent.user}</span>
                </div>
              )}
              
              {selectedEvent.details && (
                <div className="event-detail">
                  <strong>Details:</strong>
                  <span>{selectedEvent.details}</span>
                </div>
              )}
            </div>

            {/* Show edit/delete buttons only for user's own time-off requests */}
            {selectedEvent.type === 'timeoff' && selectedEvent.userId === user.id && (
              <div className="modal-actions">
                {selectedEvent.status === 'pending' && (
                  <button
                    className="btn btn-primary"
                    onClick={() => handleEdit(selectedEvent.id)}
                  >
                    Edit
                  </button>
                )}
                {(selectedEvent.status === 'approved' || selectedEvent.status === 'rejected') && (
                  <button
                    className="btn btn-danger"
                    onClick={() => handleDelete(selectedEvent)}
                  >
                    Delete
                  </button>
                )}
                <button className="btn btn-secondary" onClick={closeModal}>
                  Close
                </button>
              </div>
            )}
            
            {/* Close button for non-editable events */}
            {(selectedEvent.type !== 'timeoff' || selectedEvent.userId !== user.id) && (
              <div className="modal-actions">
                <button className="btn btn-secondary" onClick={closeModal}>
                  Close
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {confirmDelete && (
        <div className="modal-overlay" onClick={closeDeleteConfirm}>
          <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Confirm Delete</h3>
            <p>Are you sure you want to delete this time-off request?</p>
            <p className="warning-text">This action cannot be undone.</p>
            <div className="dialog-actions">
              <button className="btn btn-secondary" onClick={closeDeleteConfirm}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={confirmDeleteRequest}>
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="modal-overlay" onClick={() => setErrorMessage(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Error</h2>
              <button className="modal-close" onClick={() => setErrorMessage(null)}>×</button>
            </div>
            <div className="modal-body">
              <p>{errorMessage}</p>
            </div>
            <div className="modal-actions">
              <button
                onClick={() => setErrorMessage(null)}
                className="btn btn-secondary"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Calendar;

// Made with Bob
