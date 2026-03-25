import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import PrivateRoute from './components/PrivateRoute';
import Login from './components/Login';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Calendar from './pages/Calendar';
import TimeOffRequests from './pages/TimeOffRequests';
import OnCallSchedule from './pages/OnCallSchedule';
import DaysInLieu from './pages/DaysInLieu';
import CoachDashboard from './pages/CoachDashboard';
import AdminPanel from './pages/AdminPanel';
import Profile from './pages/Profile';
import ChangePassword from './pages/ChangePassword';
import './App.css';
import './styles/theme.css';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AuthProvider>
          <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/change-password" element={<ChangePassword />} />
          
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="calendar" element={<Calendar />} />
            <Route path="timeoff" element={<TimeOffRequests />} />
            <Route path="oncall" element={<OnCallSchedule />} />
            <Route path="days-in-lieu" element={<DaysInLieu />} />
            <Route path="profile" element={<Profile />} />
            
            <Route
              path="coach"
              element={
                <PrivateRoute requiredRole="coach">
                  <CoachDashboard />
                </PrivateRoute>
              }
            />
            
            <Route
              path="admin"
              element={
                <PrivateRoute requiredRole="coach">
                  <AdminPanel />
                </PrivateRoute>
              }
            />
          </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;

// Made with Bob
