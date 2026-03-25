import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import calendarService from '../services/calendarService';
import timeoffService from '../services/timeoffService';
import oncallService from '../services/oncallService';
import { format, parseISO } from 'date-fns';
import './Dashboard.css';

const Dashboard = () => {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [upcomingTimeOff, setUpcomingTimeOff] = useState([]);
  const [upcomingShifts, setUpcomingShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Calculate date range (current month)
      const today = new Date();
      const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
      const startDate = startOfMonth.toISOString().split('T')[0];
      const endDate = endOfMonth.toISOString().split('T')[0];

      // Load calendar summary
      const summaryData = await calendarService.getSummary(startDate, endDate, 'user');
      setSummary(summaryData);

      // Load upcoming time off
      const timeOffData = await timeoffService.getMyRequests();
      const upcoming = timeOffData.filter(req => 
        req.status === 'approved' && new Date(req.end_date) >= new Date()
      ).slice(0, 5);
      setUpcomingTimeOff(upcoming);

      // Load upcoming on-call shifts
      const shiftsData = await oncallService.getMyShifts();
      const upcomingShiftsData = shiftsData.filter(shift =>
        new Date(shift.date) >= new Date()
      ).slice(0, 5);
      setUpcomingShifts(upcomingShiftsData);

    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return <div className="alert alert-error">{error}</div>;
  }

  return (
    <div className="dashboard">
      <h1>Welcome, {user?.first_name}!</h1>
      
      <div className="dashboard-grid">
        {/* Summary Cards */}
        <div className="card summary-card">
          <div className="card-header">Time Off Summary</div>
          <div className="summary-stats">
            <div className="stat">
              <div className="stat-value">{summary?.timeoff_summary?.pending || 0}</div>
              <div className="stat-label">Pending Requests</div>
            </div>
            <div className="stat">
              <div className="stat-value">{summary?.timeoff_summary?.approved || 0}</div>
              <div className="stat-label">Approved</div>
            </div>
            <div className="stat">
              <div className="stat-value">{summary?.timeoff_summary?.upcoming || 0}</div>
              <div className="stat-label">Upcoming</div>
            </div>
          </div>
        </div>

        <div className="card summary-card">
          <div className="card-header">On-Call Summary</div>
          <div className="summary-stats">
            <div className="stat">
              <div className="stat-value">{summary?.oncall_summary?.upcoming_shifts || 0}</div>
              <div className="stat-label">Upcoming Shifts</div>
            </div>
            <div className="stat">
              <div className="stat-value">{summary?.oncall_summary?.this_month || 0}</div>
              <div className="stat-label">This Month</div>
            </div>
          </div>
        </div>

        <div className="card summary-card">
          <div className="card-header">Days in Lieu</div>
          <div className="summary-stats">
            <div className="stat">
              <div className="stat-value">{summary?.days_in_lieu_summary?.available || 0}</div>
              <div className="stat-label">Available</div>
            </div>
            <div className="stat">
              <div className="stat-value">{summary?.days_in_lieu_summary?.pending || 0}</div>
              <div className="stat-label">Pending</div>
            </div>
          </div>
        </div>

        {/* Upcoming Time Off */}
        <div className="card">
          <div className="card-header">Upcoming Time Off</div>
          {upcomingTimeOff.length === 0 ? (
            <p className="empty-message">No upcoming time off</p>
          ) : (
            <div className="list">
              {upcomingTimeOff.map(request => (
                <div key={request.id} className="list-item">
                  <div className="list-item-main">
                    <div className="list-item-title">
                      {format(parseISO(request.start_date), 'MMM d')} - {format(parseISO(request.end_date), 'MMM d, yyyy')}
                    </div>
                    <div className="list-item-subtitle">{request.reason}</div>
                  </div>
                  <span className={`badge badge-${request.status}`}>
                    {request.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upcoming On-Call Shifts */}
        <div className="card">
          <div className="card-header">Upcoming On-Call Shifts</div>
          {upcomingShifts.length === 0 ? (
            <p className="empty-message">No upcoming shifts</p>
          ) : (
            <div className="list">
              {upcomingShifts.map(shift => (
                <div key={shift.id} className="list-item">
                  <div className="list-item-main">
                    <div className="list-item-title">
                      {format(parseISO(shift.date), 'EEEE, MMM d, yyyy')}
                    </div>
                    <div className="list-item-subtitle">
                      {shift.shift_type.replace('_', ' ')}
                    </div>
                  </div>
                  {shift.is_holiday && (
                    <span className="badge badge-warning">Holiday</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

// Made with Bob
