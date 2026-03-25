import React, { useState, useEffect } from 'react';
import { format, parseISO } from 'date-fns';
import timeoffService from '../services/timeoffService';
import './TimeOffRequests.css';

const TimeOffRequests = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingRequest, setEditingRequest] = useState(null);
  const [formData, setFormData] = useState({
    start_date: '',
    end_date: '',
    reason: '',
  });
  const [formError, setFormError] = useState(null);
  const [formSuccess, setFormSuccess] = useState(null);
  const [conflicts, setConflicts] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    loadRequests();
  }, []);

  useEffect(() => {
    // Check for edit parameter in URL
    const urlParams = new URLSearchParams(window.location.search);
    const editId = urlParams.get('edit');
    
    if (editId && requests.length > 0) {
      const requestToEdit = requests.find(r => r.id === parseInt(editId));
      if (requestToEdit && requestToEdit.status === 'pending') {
        handleEdit(requestToEdit);
        // Clear the URL parameter
        window.history.replaceState({}, '', '/time-off');
      }
    }
  }, [requests]);

  const loadRequests = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await timeoffService.getMyRequests();
      setRequests(data);
    } catch (err) {
      console.error('Failed to load requests:', err);
      setError('Failed to load time-off requests');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Clear conflicts when dates change
    if (name === 'start_date' || name === 'end_date') {
      setConflicts(null);
    }
  };

  const checkConflicts = async () => {
    if (!formData.start_date || !formData.end_date) {
      return;
    }

    try {
      const conflictData = await timeoffService.checkConflicts(
        formData.start_date,
        formData.end_date
      );
      setConflicts(conflictData);
    } catch (err) {
      console.error('Failed to check conflicts:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    setFormSuccess(null);
    setSubmitting(true);

    try {
      if (editingRequest) {
        await timeoffService.updateRequest(editingRequest.id, formData);
        setFormSuccess('Time-off request updated successfully!');
      } else {
        await timeoffService.createRequest(formData);
        setFormSuccess('Time-off request submitted successfully!');
      }
      
      setFormData({
        start_date: '',
        end_date: '',
        reason: '',
      });
      setConflicts(null);
      setShowForm(false);
      setEditingRequest(null);
      loadRequests();
    } catch (err) {
      console.error('Failed to save request:', err);
      setFormError(err.response?.data?.detail || err.response?.data?.non_field_errors?.[0] || 'Failed to save request');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (request) => {
    setEditingRequest(request);
    setFormData({
      start_date: request.start_date,
      end_date: request.end_date,
      reason: request.reason,
    });
    setShowForm(true);
    setFormError(null);
    setFormSuccess(null);
  };

  const handleCancel = (request) => {
    setConfirmDelete(request);
  };

  const handleDelete = (request) => {
    setConfirmDelete(request);
  };

  const confirmDeleteRequest = async () => {
    try {
      await timeoffService.cancelRequest(confirmDelete.id);
      setConfirmDelete(null);
      loadRequests();
    } catch (err) {
      console.error('Failed to delete request:', err);
      setErrorMessage('Failed to delete request');
    }
  };

  const cancelForm = () => {
    setShowForm(false);
    setEditingRequest(null);
    setFormData({
      start_date: '',
      end_date: '',
      reason: '',
    });
    setFormError(null);
    setConflicts(null);
  };

  const getStatusBadgeClass = (status) => {
    return `badge badge-${status}`;
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="timeoff-page">
      <div className="page-header">
        <h1>Time Off Requests</h1>
        <button
          onClick={() => {
            if (showForm) {
              cancelForm();
            } else {
              setShowForm(true);
            }
          }}
          className="btn btn-primary"
        >
          {showForm ? 'Cancel' : 'New Request'}
        </button>
      </div>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      {formSuccess && (
        <div className="alert alert-success">{formSuccess}</div>
      )}

      {showForm && (
        <div className="card request-form">
          <div className="card-header">{editingRequest ? 'Edit Time-Off Request' : 'New Time-Off Request'}</div>
          
          {formError && (
            <div className="alert alert-error">{formError}</div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="start_date">Start Date *</label>
                <input
                  type="date"
                  id="start_date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleInputChange}
                  onBlur={checkConflicts}
                  required
                  disabled={submitting}
                />
              </div>

              <div className="form-group">
                <label htmlFor="end_date">End Date *</label>
                <input
                  type="date"
                  id="end_date"
                  name="end_date"
                  value={formData.end_date}
                  onChange={handleInputChange}
                  onBlur={checkConflicts}
                  min={formData.start_date}
                  required
                  disabled={submitting}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="reason">Reason *</label>
              <textarea
                id="reason"
                name="reason"
                value={formData.reason}
                onChange={handleInputChange}
                required
                disabled={submitting}
                placeholder="Enter reason for time off..."
              />
            </div>

            {conflicts && (
              <div className={`alert ${conflicts.has_conflicts ? 'alert-warning' : 'alert-info'}`}>
                {conflicts.has_conflicts ? (
                  <>
                    <strong>⚠️ Potential Conflicts:</strong>
                    <p>{conflicts.message}</p>
                    <ul>
                      {conflicts.conflicts.map((conflict, idx) => (
                        <li key={idx}>
                          {conflict.date}: {conflict.count} team member(s) already off
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <p>✓ No conflicts detected</p>
                )}
              </div>
            )}

            <div className="form-actions">
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={submitting}
              >
                {submitting ? 'Submitting...' : 'Submit Request'}
              </button>
              <button
                type="button"
                onClick={cancelForm}
                className="btn btn-secondary"
                disabled={submitting}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="card-header">My Requests</div>
        
        {requests.length === 0 ? (
          <p className="empty-message">No time-off requests yet</p>
        ) : (
          <div className="requests-list">
            {requests.map(request => (
              <div key={request.id} className="request-item">
                <div className="request-main">
                  <div className="request-dates">
                    {format(parseISO(request.start_date), 'MMM d, yyyy')} - {format(parseISO(request.end_date), 'MMM d, yyyy')}
                  </div>
                  <div className="request-reason">{request.reason}</div>
                  {request.rejection_reason && (
                    <div className="rejection-reason">
                      <strong>Rejection reason:</strong> {request.rejection_reason}
                    </div>
                  )}
                  <div className="request-meta">
                    Submitted: {format(parseISO(request.created_at), 'MMM d, yyyy')}
                  </div>
                </div>
                
                <div className="request-actions">
                  <span className={getStatusBadgeClass(request.status)}>
                    {request.status}
                  </span>
                  
                  {request.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleEdit(request)}
                        className="btn btn-secondary btn-sm"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleCancel(request.id)}
                        className="btn btn-danger btn-sm"
                      >
                        Cancel
                      </button>
                    </>
                  )}
                  {request.status === 'approved' && (
                    <button
                      onClick={() => handleDelete(request)}
                      className="btn btn-danger btn-sm"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {confirmDelete && (
        <div className="modal-overlay" onClick={() => setConfirmDelete(null)}>
          <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="confirm-header">
              <h3>Delete Approved Time-Off</h3>
            </div>
            <div className="confirm-body">
              <p>Are you sure you want to delete this approved time-off request?</p>
              <p><strong>{format(parseISO(confirmDelete.start_date), 'MMM d, yyyy')} - {format(parseISO(confirmDelete.end_date), 'MMM d, yyyy')}</strong></p>
              <p>{confirmDelete.reason}</p>
            </div>
            <div className="confirm-actions">
              <button onClick={() => setConfirmDelete(null)} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={confirmDeleteRequest} className="btn btn-danger">
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

export default TimeOffRequests;

// Made with Bob
