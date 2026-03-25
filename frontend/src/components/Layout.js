import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ThemeToggle from './ThemeToggle';
import './Layout.css';

const Layout = () => {
  const { user, logout, isCoach, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="navbar-brand">
          <Link to="/dashboard">Calendar App</Link>
        </div>
        
        <div className="navbar-menu">
          <Link to="/dashboard" className="nav-link">Dashboard</Link>
          <Link to="/calendar" className="nav-link">Calendar</Link>
          <Link to="/timeoff" className="nav-link">Time Off</Link>
          <Link to="/oncall" className="nav-link">On-Call</Link>
          <Link to="/days-in-lieu" className="nav-link">Days in Lieu</Link>
          
          {(isCoach() || isAdmin()) && (
            <Link to="/coach" className="nav-link">Coach Dashboard</Link>
          )}
          
          {(isCoach() || isAdmin()) && (
            <Link to="/admin" className="nav-link">Admin</Link>
          )}
        </div>

        <div className="navbar-user">
          <Link to="/profile" className="profile-button">
            {user?.first_name} {user?.last_name}
          </Link>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
          <ThemeToggle />
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;

// Made with Bob
