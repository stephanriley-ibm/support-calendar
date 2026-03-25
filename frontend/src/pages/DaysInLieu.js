import React, { useState, useEffect } from 'react';
import { format, parseISO } from 'date-fns';
import oncallService from '../services/oncallService';
import './DaysInLieu.css';

const DaysInLieu = () => {
  const [daysInLieu, setDaysInLieu] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('available');
  const [confirmMarkUsed, setConfirmMarkUsed] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    loadDaysInLieu();
  }, []);

  const loadDaysInLieu = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await oncallService.getMyDaysInLieu();
      setDaysInLieu(data);
    } catch (err) {
      console.error('Failed to load days in lieu:', err);
      setError('Failed to load days in lieu');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkUsedClick = (day) => {
    setConfirmMarkUsed(day);
  };

  const handleMarkUsed = async () => {
    try {
      await oncallService.markUsed(confirmMarkUsed.id);
      setConfirmMarkUsed(null);
      loadDaysInLieu();
    } catch (err) {
      console.error('Failed to mark as used:', err);
      setErrorMessage('Failed to mark as used: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getStatusBadgeClass = (status) => {
    return `badge badge-${status}`;
  };

  const getFilteredDays = () => {
    switch (filter) {
      case 'available':
        return daysInLieu.filter(day => day.status === 'scheduled');
      case 'used':
        return daysInLieu.filter(day => day.status === 'used');
      case 'expired':
        return daysInLieu.filter(day => day.status === 'expired');
      case 'all':
      default:
        return daysInLieu;
    }
  };

  const filteredDays = getFilteredDays();
  const availableCount = daysInLieu.filter(day => day.status === 'scheduled').length;

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="daysinlieu-page">
      <div className="page-header">
        <h1>Days in Lieu</h1>
        <div className="available-badge">
          {availableCount} Available
        </div>
      </div>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      <div className="filter-tabs">
        <button
          className={`filter-tab ${filter === 'available' ? 'active' : ''}`}
          onClick={() => setFilter('available')}
        >
          Scheduled
        </button>
        <button
          className={`filter-tab ${filter === 'used' ? 'active' : ''}`}
          onClick={() => setFilter('used')}
        >
          Used
        </button>
        <button
          className={`filter-tab ${filter === 'expired' ? 'active' : ''}`}
          onClick={() => setFilter('expired')}
        >
          Expired
        </button>
        <button
          className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All
        </button>
      </div>

      <div className="card">
        {filteredDays.length === 0 ? (
          <p className="empty-message">No days in lieu found</p>
        ) : (
          <div className="days-list">
            {filteredDays.map(day => (
              <div key={day.id} className="day-item">
                <div className="day-main">
                  <div className="day-date">
                    {format(parseISO(day.scheduled_date), 'EEEE, MMMM d, yyyy')}
                  </div>
                  <div className="day-source">
                    From on-call shift: {format(parseISO(day.oncall_shift_date), 'MMM d, yyyy')}
                    {day.shift_type && (
                      <span className="shift-type-label">
                        ({day.shift_type.replace(/_/g, ' ')})
                      </span>
                    )}
                  </div>
                  {day.coach_adjusted && (
                    <div className="adjustment-note">
                      <span className="adjustment-icon">✏️</span>
                      Adjusted by coach
                      {day.adjustment_reason && `: ${day.adjustment_reason}`}
                    </div>
                  )}
                  {day.status === 'used' && day.used_date && (
                    <div className="taken-note">
                      Used on: {format(parseISO(day.used_date), 'MMM d, yyyy')}
                    </div>
                  )}
                  <div className="day-meta">
                    Generated: {format(parseISO(day.created_at), 'MMM d, yyyy')}
                  </div>
                </div>

                <div className="day-actions">
                  <span className={getStatusBadgeClass(day.status)}>
                    {day.status}
                  </span>
                  
                  {day.status === 'scheduled' && (
                    <button
                      onClick={() => handleMarkUsedClick(day)}
                      className="btn btn-primary btn-sm"
                    >
                      Mark as Used
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {confirmMarkUsed && (
        <div className="modal-overlay" onClick={() => setConfirmMarkUsed(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Confirm Mark as Used</h2>
              <button className="modal-close" onClick={() => setConfirmMarkUsed(null)}>×</button>
            </div>
            <div className="modal-body">
              <p>Mark this day in lieu as used?</p>
              <p><strong>Date:</strong> {format(parseISO(confirmMarkUsed.scheduled_date), 'EEEE, MMMM d, yyyy')}</p>
            </div>
            <div className="modal-actions">
              <button
                onClick={() => setConfirmMarkUsed(null)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleMarkUsed}
                className="btn btn-primary"
              >
                Mark as Used
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="info-card">
        <h3>About Days in Lieu</h3>
        <p>
          Days in lieu are automatically generated and scheduled when you work on-call shifts.
          The scheduled date depends on your shift type:
        </p>
        <ul>
          <li><strong>Early Primary (Sat):</strong> Thursday & Friday before the shift</li>
          <li><strong>Late Primary (Sun):</strong> Monday & Tuesday after the shift</li>
          <li><strong>Secondary (Sat-Sun):</strong> Wednesday after the shift</li>
        </ul>
        <p>
          Your coach can adjust the scheduled dates if needed. Mark them as used when you take them off.
        </p>
      </div>
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

export default DaysInLieu;

// Made with Bob
