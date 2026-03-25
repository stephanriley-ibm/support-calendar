import React, { useState, useEffect } from 'react';
import { format, parseISO, eachDayOfInterval } from 'date-fns';
import timeoffService from '../services/timeoffService';
import oncallService from '../services/oncallService';
import './CoachDashboard.css';

const CoachDashboard = () => {
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [reviewingRequest, setReviewingRequest] = useState(null);
  const [conflictingRequests, setConflictingRequests] = useState([]);
  const [loadingConflicts, setLoadingConflicts] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const timeoffData = await timeoffService.getPendingRequests();
      setPendingRequests(timeoffData);
    } catch (err) {
      console.error('Failed to load data:', err);
      setError('Failed to load pending items');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewRequest = async (request) => {
    setReviewingRequest(request);
    setRejectionReason('');
    
    // Fetch conflicting time-off requests
    try {
      setLoadingConflicts(true);
      const conflicts = await timeoffService.checkConflicts(
        request.start_date,
        request.end_date
      );
      
      // Filter out the current request and only show approved requests
      const relevantConflicts = conflicts.conflicting_requests?.filter(
        r => r.id !== request.id && r.status === 'approved'
      ) || [];
      
      setConflictingRequests(relevantConflicts);
    } catch (err) {
      console.error('Failed to load conflicts:', err);
      setConflictingRequests([]);
    } finally {
      setLoadingConflicts(false);
    }
  };

  const handleApproveTimeOff = async (id) => {
    try {
      await timeoffService.approveRequest(id);
      setReviewingRequest(null);
      loadData();
    } catch (err) {
      console.error('Failed to approve request:', err);
      setErrorMessage('Failed to approve request: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRejectTimeOff = async (id) => {
    if (!rejectionReason.trim()) {
      setErrorMessage('Please provide a rejection reason');
      return;
    }

    try {
      await timeoffService.rejectRequest(id, rejectionReason);
      setReviewingRequest(null);
      setRejectionReason('');
      loadData();
    } catch (err) {
      console.error('Failed to reject request:', err);
      setErrorMessage('Failed to reject request');
    }
  };

  const closeReviewModal = () => {
    setReviewingRequest(null);
    setConflictingRequests([]);
    setRejectionReason('');
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="coach-dashboard">
      <h1>Coach Dashboard</h1>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      <div className="card">
          <div className="card-header">Pending Time-Off Requests</div>
          
          {pendingRequests.length === 0 ? (
            <p className="empty-message">No pending time-off requests</p>
          ) : (
            <div className="approval-list">
              {pendingRequests.map(request => (
                <div key={request.id} className="approval-item">
                  <div className="approval-main">
                    <div className="approval-user">
                      {request.user_name}
                      {request.team_name && (
                        <span className="team-badge">{request.team_name}</span>
                      )}
                    </div>
                    <div className="approval-dates">
                      {format(parseISO(request.start_date), 'MMM d, yyyy')} - {format(parseISO(request.end_date), 'MMM d, yyyy')}
                    </div>
                    <div className="approval-reason">{request.reason}</div>
                    <div className="approval-meta">
                      Submitted: {format(parseISO(request.created_at), 'MMM d, yyyy')}
                    </div>
                  </div>

                  <div className="approval-actions">
                    <button
                      onClick={() => handleReviewRequest(request)}
                      className="btn btn-primary"
                    >
                      Review
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
      </div>

      {/* Review Modal */}
      {reviewingRequest && (
        <div className="modal-overlay" onClick={closeReviewModal}>
          <div className="review-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Review Time-Off Request</h2>
              <button className="close-btn" onClick={closeReviewModal}>×</button>
            </div>

            <div className="modal-body">
              {/* Request Details */}
              <div className="review-section">
                <h3>Request Details</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <strong>Employee:</strong>
                    <span>{reviewingRequest.user_name}</span>
                  </div>
                  <div className="detail-item">
                    <strong>Team:</strong>
                    <span>{reviewingRequest.team_name || 'N/A'}</span>
                  </div>
                  <div className="detail-item">
                    <strong>Start Date:</strong>
                    <span>{format(parseISO(reviewingRequest.start_date), 'EEEE, MMM d, yyyy')}</span>
                  </div>
                  <div className="detail-item">
                    <strong>End Date:</strong>
                    <span>{format(parseISO(reviewingRequest.end_date), 'EEEE, MMM d, yyyy')}</span>
                  </div>
                  <div className="detail-item">
                    <strong>Duration:</strong>
                    <span>
                      {eachDayOfInterval({
                        start: parseISO(reviewingRequest.start_date),
                        end: parseISO(reviewingRequest.end_date)
                      }).length} days
                    </span>
                  </div>
                  <div className="detail-item">
                    <strong>Submitted:</strong>
                    <span>{format(parseISO(reviewingRequest.created_at), 'MMM d, yyyy')}</span>
                  </div>
                  <div className="detail-item full-width">
                    <strong>Reason:</strong>
                    <span>{reviewingRequest.reason || 'No reason provided'}</span>
                  </div>
                </div>
              </div>

              {/* Conflicting Requests */}
              <div className="review-section">
                <h3>Team Availability</h3>
                {loadingConflicts ? (
                  <div className="loading-text">Loading conflicts...</div>
                ) : conflictingRequests.length > 0 ? (
                  <>
                    <div className="conflict-warning">
                      ⚠️ {conflictingRequests.length} team member(s) already have approved time-off during this period:
                    </div>
                    <div className="conflict-list">
                      {conflictingRequests.map(conflict => (
                        <div key={conflict.id} className="conflict-item">
                          <div className="conflict-user">{conflict.user_name}</div>
                          <div className="conflict-dates">
                            {format(parseISO(conflict.start_date), 'MMM d')} - {format(parseISO(conflict.end_date), 'MMM d, yyyy')}
                          </div>
                          <div className="conflict-reason">{conflict.reason}</div>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="no-conflicts">
                    ✓ No conflicting time-off requests found
                  </div>
                )}
              </div>

              {/* Rejection Reason (if rejecting) */}
              {rejectionReason !== null && rejectionReason !== '' && (
                <div className="review-section">
                  <h3>Rejection Reason</h3>
                  <textarea
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="Enter reason for rejection..."
                    rows="4"
                    className="rejection-textarea"
                  />
                </div>
              )}
            </div>

            <div className="modal-actions">
              {rejectionReason === '' ? (
                <>
                  <button
                    onClick={() => handleApproveTimeOff(reviewingRequest.id)}
                    className="btn btn-success"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => setRejectionReason(' ')}
                    className="btn btn-danger"
                  >
                    Reject
                  </button>
                  <button
                    onClick={closeReviewModal}
                    className="btn btn-secondary"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => handleRejectTimeOff(reviewingRequest.id)}
                    className="btn btn-danger"
                    disabled={!rejectionReason.trim()}
                  >
                    Confirm Rejection
                  </button>
                  <button
                    onClick={() => setRejectionReason('')}
                    className="btn btn-secondary"
                  >
                    Back
                  </button>
                </>
              )}
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

export default CoachDashboard;

// Made with Bob
