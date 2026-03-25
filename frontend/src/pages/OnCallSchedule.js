import React, { useState, useEffect } from 'react';
import { format, parseISO } from 'date-fns';
import { useAuth } from '../contexts/AuthContext';
import oncallService from '../services/oncallService';
import userService from '../services/userService';
import './OnCallSchedule.css';

const OnCallSchedule = () => {
  const { user, isCoach, isAdmin } = useAuth();
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [showDeleteForm, setShowDeleteForm] = useState(false);
  const [showHolidayForm, setShowHolidayForm] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [confirmGenerate, setConfirmGenerate] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [teams, setTeams] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [engineers, setEngineers] = useState([]);
  const [holidayForm, setHolidayForm] = useState({
    engineer: '',
    holiday: '',
    start_time: '00:00',
    end_time: '23:59',
    notes: '',
  });
  const [submittingHoliday, setSubmittingHoliday] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    start_date: '',
    end_date: '',
    teams: [], // Changed from single team to array of teams
  });
  const [deleteForm, setDeleteForm] = useState({
    start_date: '',
    end_date: '',
    teams: [],
  });
  const [generating, setGenerating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [shiftsData, teamsData, holidaysData, engineersData] = await Promise.all([
        oncallService.getMyShifts(),
        userService.getTeams(),
        oncallService.getHolidays(),
        userService.getUsers(),
      ]);
      
      setShifts(shiftsData);
      // Handle paginated response
      setTeams(teamsData.results || teamsData || []);
      setHolidays(holidaysData.results || holidaysData || []);
      setEngineers(engineersData.results || engineersData || []);
      
      // Set default team if user has one
      if (user.team && generateForm.teams.length === 0) {
        setGenerateForm(prev => ({ ...prev, teams: [user.team] }));
      }
    } catch (err) {
      console.error('Failed to load data:', err);
      setError('Failed to load on-call schedule');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateFormChange = (e) => {
    const { name, value } = e.target;
    setGenerateForm(prev => ({
      ...prev,
      [name]: value,
    }));
    setPreview(null);
  };

  const handleTeamToggle = (teamId) => {
    setGenerateForm(prev => {
      const teams = prev.teams.includes(teamId)
        ? prev.teams.filter(id => id !== teamId)
        : [...prev.teams, teamId];
      return { ...prev, teams };
    });
    setPreview(null);
  };

  const handlePreview = async () => {
    if (!generateForm.start_date || !generateForm.end_date || generateForm.teams.length === 0) {
      setErrorMessage('Please fill in all fields and select at least one team');
      return;
    }

    try {
      setGenerating(true);
      const previewData = await oncallService.previewRotation(
        generateForm.start_date,
        generateForm.end_date,
        generateForm.teams
      );
      setPreview(previewData);
    } catch (err) {
      console.error('Failed to preview rotation:', err);
      setErrorMessage('Failed to preview rotation: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteFormChange = (e) => {
    const { name, value } = e.target;
    setDeleteForm(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleDeleteTeamToggle = (teamId) => {
    setDeleteForm(prev => {
      const teams = prev.teams.includes(teamId)
        ? prev.teams.filter(id => id !== teamId)
        : [...prev.teams, teamId];
      return { ...prev, teams };
    });
  };

  const handleDeleteClick = () => {
    if (!deleteForm.start_date || !deleteForm.end_date) {
      setErrorMessage('Please fill in start and end dates');
      return;
    }

    const teamText = deleteForm.teams.length > 0
      ? ` for selected team(s)`
      : ' for all teams';
    
    setConfirmDelete({
      start_date: deleteForm.start_date,
      end_date: deleteForm.end_date,
      teams: deleteForm.teams,
      message: `Delete all shifts between ${deleteForm.start_date} and ${deleteForm.end_date}${teamText}?`
    });
  };

  const confirmDeleteRotation = async () => {
    try {
      setDeleting(true);
      const result = await oncallService.deleteRotation(
        confirmDelete.start_date,
        confirmDelete.end_date,
        confirmDelete.teams.length > 0 ? confirmDelete.teams : null
      );
      setSuccessMessage(result.message || `Successfully deleted ${result.shifts_deleted} shift(s)`);
      setShowDeleteForm(false);
      setConfirmDelete(null);
      setDeleteForm({
        start_date: '',
        end_date: '',
        teams: [],
      });
      loadData();
    } catch (err) {
      console.error('Failed to delete rotation:', err);
      setErrorMessage('Failed to delete rotation: ' + (err.response?.data?.error || err.message));
    } finally {
      setDeleting(false);
    }
  };

  const handleGenerateClick = () => {
    setConfirmGenerate(true);
  };

  const handleGenerate = async () => {
    setConfirmGenerate(false);
    
    try {
      setGenerating(true);
      await oncallService.generateRotation(
        generateForm.start_date,
        generateForm.end_date,
        generateForm.teams
      );
      setSuccessMessage('Rotation generated successfully!');
      setShowGenerateForm(false);
      setPreview(null);
      setGenerateForm({
        start_date: '',
        end_date: '',
        teams: [],
      });
      loadData();
    } catch (err) {
      console.error('Failed to generate rotation:', err);
      setErrorMessage('Failed to generate rotation: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  const handleHolidayFormChange = (e) => {
    const { name, value } = e.target;
    setHolidayForm(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const getSelectedHolidayDate = () => {
    if (!holidayForm.holiday) return null;
    const selectedHoliday = holidays.find(h => h.id === parseInt(holidayForm.holiday));
    return selectedHoliday ? selectedHoliday.date : null;
  };

  const handleCreateHolidayShift = async () => {
    if (!holidayForm.engineer || !holidayForm.holiday) {
      setErrorMessage('Please fill in all required fields');
      return;
    }

    const holidayDate = getSelectedHolidayDate();
    if (!holidayDate) {
      setErrorMessage('Invalid holiday selected');
      return;
    }

    try {
      setSubmittingHoliday(true);
      await oncallService.createShift({
        shift_date: holidayDate,
        shift_type: 'holiday',
        engineer: parseInt(holidayForm.engineer),
        holiday: parseInt(holidayForm.holiday),
        start_time: holidayForm.start_time,
        end_time: holidayForm.end_time,
        notes: holidayForm.notes,
      });
      setSuccessMessage('Holiday shift created successfully!');
      setShowHolidayForm(false);
      setHolidayForm({
        engineer: '',
        holiday: '',
        start_time: '00:00',
        end_time: '23:59',
        notes: '',
      });
      loadData();
    } catch (err) {
      console.error('Failed to create holiday shift:', err);
      setErrorMessage('Failed to create holiday shift: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmittingHoliday(false);
    }
  };

  const getShiftTypeLabel = (type) => {
    const labels = {
      early_primary: 'Early Primary',
      late_primary: 'Late Primary',
      secondary: 'Secondary',
      early_secondary: 'Early Secondary',
      late_secondary: 'Late Secondary',
    };
    return labels[type] || type;
  };

  const getShiftTypeColor = (type) => {
    const colors = {
      early_primary: '#e74c3c',
      late_primary: '#e67e22',
      secondary: '#f1c40f',          // Bright Yellow (changed for better differentiation)
      early_secondary: '#3498db',
      late_secondary: '#9b59b6',
    };
    return colors[type] || '#95a5a6';
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="oncall-page">
      <div className="page-header">
        <h1>On-Call Schedule</h1>
        {(isCoach() || isAdmin()) && (
          <div className="button-group">
            <button
              onClick={() => {
                setShowGenerateForm(!showGenerateForm);
                setShowDeleteForm(false);
                setShowHolidayForm(false);
              }}
              className="btn btn-primary"
            >
              {showGenerateForm ? 'Cancel' : 'Generate Rotation'}
            </button>
            <button
              onClick={() => {
                setShowHolidayForm(!showHolidayForm);
                setShowGenerateForm(false);
                setShowDeleteForm(false);
              }}
              className="btn btn-success"
            >
              {showHolidayForm ? 'Cancel' : 'Create Holiday Shift'}
            </button>
            <button
              onClick={() => {
                setShowDeleteForm(!showDeleteForm);
                setShowGenerateForm(false);
                setShowHolidayForm(false);
              }}
              className="btn btn-danger"
            >
              {showDeleteForm ? 'Cancel' : 'Delete Rotation'}
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      {showGenerateForm && (
        <div className="card generate-form">
          <div className="card-header">Generate On-Call Rotation</div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="start_date">Start Date *</label>
              <input
                type="date"
                id="start_date"
                name="start_date"
                value={generateForm.start_date}
                onChange={handleGenerateFormChange}
                disabled={generating}
              />
            </div>

            <div className="form-group">
              <label htmlFor="end_date">End Date *</label>
              <input
                type="date"
                id="end_date"
                name="end_date"
                value={generateForm.end_date}
                onChange={handleGenerateFormChange}
                min={generateForm.start_date}
                disabled={generating}
              />
            </div>

            <div className="form-group full-width">
              <label>Teams * (Select one or more)</label>
              <div className="team-checkboxes">
                {teams.map(team => (
                  <label key={team.id} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={generateForm.teams.includes(team.id)}
                      onChange={() => handleTeamToggle(team.id)}
                      disabled={generating}
                    />
                    <span>{team.name}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="form-actions">
            <button 
              onClick={handlePreview}
              className="btn btn-secondary"
              disabled={generating}
            >
              {generating ? 'Loading...' : 'Preview'}
            </button>
            <button
              onClick={handleGenerateClick}
              className="btn btn-primary"
              disabled={generating || !preview}
            >
              Generate
            </button>
          </div>

          {preview && (
            <div className="preview-section">
              <h3>Preview ({preview.shifts?.length || 0} shifts)</h3>
              <div className="preview-info">
                <p><strong>Weekends:</strong> {preview.weekend_count}</p>
                <p><strong>Total Shifts:</strong> {preview.total_shifts}</p>
              </div>
              {preview.shifts && preview.shifts.length > 0 && (
                <div className="preview-list">
                  {preview.shifts.slice(0, 10).map((shift, idx) => (
                    <div key={idx} className="preview-item">
                      <span className="preview-date">
                        {format(parseISO(shift.date), 'MMM d, yyyy')}
                      </span>
                      <span 
                        className="preview-type"
                        style={{ backgroundColor: getShiftTypeColor(shift.shift_type) }}
                      >
                        {getShiftTypeLabel(shift.shift_type)}
                      </span>
                      <span className="preview-user">{shift.user_name}</span>
                    </div>
                  ))}
                  {preview.shifts.length > 10 && (
                    <p className="preview-more">
                      ... and {preview.shifts.length - 10} more shifts
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

    {showHolidayForm && (
      <div className="card generate-form">
        <div className="card-header">Create Holiday Shift</div>
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="holiday">Holiday *</label>
            <select
              id="holiday"
              name="holiday"
              value={holidayForm.holiday}
              onChange={handleHolidayFormChange}
              disabled={submittingHoliday}
            >
              <option value="">Select Holiday</option>
              {holidays.map(holiday => (
                <option key={holiday.id} value={holiday.id}>
                  {holiday.name} ({holiday.date})
                </option>
              ))}
            </select>
            {holidayForm.holiday && (
              <small className="form-help">
                Shift will be created for: {getSelectedHolidayDate()}
              </small>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="engineer">Engineer *</label>
            <select
              id="engineer"
              name="engineer"
              value={holidayForm.engineer}
              onChange={handleHolidayFormChange}
              disabled={submittingHoliday}
            >
              <option value="">Select Engineer</option>
              {engineers.map(eng => (
                <option key={eng.id} value={eng.id}>
                  {eng.first_name} {eng.last_name} ({eng.username})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="start_time">Start Time</label>
            <input
              type="time"
              id="start_time"
              name="start_time"
              value={holidayForm.start_time}
              onChange={handleHolidayFormChange}
              disabled={submittingHoliday}
            />
          </div>

          <div className="form-group">
            <label htmlFor="end_time">End Time</label>
            <input
              type="time"
              id="end_time"
              name="end_time"
              value={holidayForm.end_time}
              onChange={handleHolidayFormChange}
              disabled={submittingHoliday}
            />
          </div>

          <div className="form-group full-width">
            <label htmlFor="notes">Notes (Optional)</label>
            <textarea
              id="notes"
              name="notes"
              value={holidayForm.notes}
              onChange={handleHolidayFormChange}
              disabled={submittingHoliday}
              rows="3"
              placeholder="Any additional notes about this shift..."
            />
          </div>
        </div>

        <div className="form-actions">
          <button
            onClick={handleCreateHolidayShift}
            className="btn btn-success"
            disabled={submittingHoliday}
          >
            {submittingHoliday ? 'Creating...' : 'Create Holiday Shift'}
          </button>
        </div>
      </div>
    )}

    {showDeleteForm && (
        <div className="card delete-form">
          <div className="card-header">Delete On-Call Rotation</div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="delete_start_date">Start Date *</label>
              <input
                type="date"
                id="delete_start_date"
                name="start_date"
                value={deleteForm.start_date}
                onChange={handleDeleteFormChange}
                disabled={deleting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="delete_end_date">End Date *</label>
              <input
                type="date"
                id="delete_end_date"
                name="end_date"
                value={deleteForm.end_date}
                onChange={handleDeleteFormChange}
                min={deleteForm.start_date}
                disabled={deleting}
              />
            </div>

            <div className="form-group full-width">
              <label>Teams (Optional - leave empty to delete all teams)</label>
              <div className="team-checkboxes">
                {teams.map(team => (
                  <label key={team.id} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={deleteForm.teams.includes(team.id)}
                      onChange={() => handleDeleteTeamToggle(team.id)}
                      disabled={deleting}
                    />
                    <span>{team.name}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="alert alert-warning">
            <strong>Warning:</strong> This will permanently delete all shifts and associated days-in-lieu in the specified date range. This action cannot be undone.
          </div>

          <div className="form-actions">
            <button
              onClick={handleDeleteClick}
              className="btn btn-danger"
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete Rotation'}
            </button>
          </div>
        </div>
      )}

      {confirmGenerate && (
        <div className="modal-overlay" onClick={() => setConfirmGenerate(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Confirm Generation</h2>
              <button className="modal-close" onClick={() => setConfirmGenerate(false)}>×</button>
            </div>
            <div className="modal-body">
              <p>Generate rotation? This will create on-call shifts and days in lieu.</p>
            </div>
            <div className="modal-actions">
              <button
                onClick={() => setConfirmGenerate(false)}
                className="btn btn-secondary"
                disabled={generating}
              >
                Cancel
              </button>
              <button
                onClick={handleGenerate}
                className="btn btn-primary"
                disabled={generating}
              >
                {generating ? 'Generating...' : 'Generate'}
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmDelete && (
        <div className="modal-overlay" onClick={() => setConfirmDelete(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Confirm Deletion</h2>
              <button className="modal-close" onClick={() => setConfirmDelete(null)}>×</button>
            </div>
            <div className="modal-body">
              <p>{confirmDelete.message}</p>
              <p className="warning-text">This action cannot be undone!</p>
            </div>
            <div className="modal-actions">
              <button
                onClick={() => setConfirmDelete(null)}
                className="btn btn-secondary"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteRotation}
                className="btn btn-danger"
                disabled={deleting}
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="modal-overlay" onClick={() => setSuccessMessage(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Success</h2>
              <button className="modal-close" onClick={() => setSuccessMessage(null)}>×</button>
            </div>
            <div className="modal-body">
              <p>{successMessage}</p>
            </div>
            <div className="modal-actions">
              <button
                onClick={() => setSuccessMessage(null)}
                className="btn btn-primary"
              >
                OK
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

      <div className="card">
        <div className="card-header">My Upcoming Shifts</div>
        
        {shifts.length === 0 ? (
          <p className="empty-message">No upcoming on-call shifts</p>
        ) : (
          <div className="shifts-list">
            {shifts.map(shift => (
              <div key={shift.id} className="shift-item">
                <div 
                  className="shift-indicator"
                  style={{ backgroundColor: getShiftTypeColor(shift.shift_type) }}
                ></div>
                <div className="shift-main">
                  <div className="shift-date">
                    {format(parseISO(shift.date), 'EEEE, MMMM d, yyyy')}
                  </div>
                  <div className="shift-type">
                    {getShiftTypeLabel(shift.shift_type)}
                  </div>
                  {shift.is_holiday && (
                    <span className="holiday-badge">Holiday</span>
                  )}
                </div>
                {shift.days_in_lieu_generated && (
                  <div className="shift-badge">
                    <span className="badge badge-approved">Day in Lieu Generated</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OnCallSchedule;

// Made with Bob
