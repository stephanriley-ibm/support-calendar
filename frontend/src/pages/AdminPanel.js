import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import userService from '../services/userService';
import oncallService from '../services/oncallService';
import './AdminPanel.css';

const AdminPanel = () => {
  const { user, isAdmin, isCoach } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [credentials, setCredentials] = useState(null);
  const [copiedField, setCopiedField] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState(null);

  // Users state
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'username', direction: 'asc' });
  const [showUserForm, setShowUserForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    password_confirm: '',
    role: 'engineer',
    team: '',
    oncall_eligible: true,
  });

  // Teams state
  const [teams, setTeams] = useState([]);
  const [showTeamForm, setShowTeamForm] = useState(false);
  const [editingTeam, setEditingTeam] = useState(null);
  const [teamForm, setTeamForm] = useState({
    name: '',
    coach: '',
    max_concurrent_off: 2,
    description: '',
  });

  // Holidays state
  const [holidays, setHolidays] = useState([]);
  const [showHolidayForm, setShowHolidayForm] = useState(false);
  const [editingHoliday, setEditingHoliday] = useState(null);
  const [holidayForm, setHolidayForm] = useState({
    name: '',
    date: '',
    is_recurring: false,
    description: '',
  });

  useEffect(() => {
    // Load teams on mount for user form dropdown
    loadTeams();
  }, []);

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'teams') {
      loadTeams();
    } else if (activeTab === 'holidays') {
      loadHolidays();
    }
  }, [activeTab]);

  // Load data functions
  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await userService.getUsers();
      const usersList = response.results || response || [];
      setUsers(usersList);
      setFilteredUsers(usersList);
    } catch (err) {
      console.error('Failed to load users:', err);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  // Filter and sort users whenever search query, sort config, or users change
  useEffect(() => {
    let result = [...users];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(user =>
        user.username?.toLowerCase().includes(query) ||
        user.full_name?.toLowerCase().includes(query) ||
        user.email?.toLowerCase().includes(query) ||
        user.team_name?.toLowerCase().includes(query)
      );
    }

    // Apply sorting
    if (sortConfig.key) {
      result.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        // Handle null/undefined values
        if (aValue === null || aValue === undefined) aValue = '';
        if (bValue === null || bValue === undefined) bValue = '';

        // Convert to lowercase for string comparison
        if (typeof aValue === 'string') aValue = aValue.toLowerCase();
        if (typeof bValue === 'string') bValue = bValue.toLowerCase();

        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }

    setFilteredUsers(result);
  }, [users, searchQuery, sortConfig]);

  // Handle sort column click
  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Get sort indicator for column headers
  const getSortIndicator = (key) => {
    if (sortConfig.key !== key) return ' ↕';
    return sortConfig.direction === 'asc' ? ' ↑' : ' ↓';
  };

  const loadTeams = async () => {
    try {
      setLoading(true);
      const response = await userService.getTeams();
      setTeams(response.results || response || []);
    } catch (err) {
      console.error('Failed to load teams:', err);
      setError('Failed to load teams');
    } finally {
      setLoading(false);
    }
  };

  const loadHolidays = async () => {
    try {
      setLoading(true);
      const response = await oncallService.getHolidays();
      // Handle paginated response
      const data = response.results || response || [];
      setHolidays(data);
    } catch (err) {
      console.error('Failed to load holidays:', err);
      setError('Failed to load holidays');
      setHolidays([]);
    } finally {
      setLoading(false);
    }
  };

  // Copy to clipboard function
  const copyToClipboard = async (text, field) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // User management functions
  const handleUserSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      if (editingUser) {
        await userService.updateUser(editingUser.id, userForm);
        setSuccess('User updated successfully');
      } else {
        // Prepare data - remove empty fields for auto-generation
        const userData = { ...userForm };
        
        // Remove username if empty (will be auto-generated)
        if (!userData.username || userData.username.trim() === '') {
          delete userData.username;
        }
        
        // Remove password fields if empty (will be auto-generated)
        if (!userData.password || userData.password.trim() === '') {
          delete userData.password;
          delete userData.password_confirm;
        }
        
        const response = await userService.createUser(userData);
        // Display temporary password if generated
        if (response.temp_password) {
          setCredentials({
            username: response.username,
            password: response.temp_password,
            message: 'User created successfully!'
          });
          setSuccess('User created successfully!');
        } else {
          setSuccess('User created successfully');
        }
      }
      resetUserForm();
      loadUsers();
    } catch (err) {
      console.error('Failed to save user:', err);
      setError(err.response?.data?.detail || 'Failed to save user');
    }
  };

  const handleEditUser = (user) => {
    setEditingUser(user);
    setUserForm({
      username: user.username,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      password: '',
      password_confirm: '',
      role: user.role,
      team: user.team || '',
      oncall_eligible: user.oncall_eligible !== undefined ? user.oncall_eligible : true,
    });
    setShowUserForm(true);
  };

  const handleDeleteUser = (id, username) => {
    setConfirmDialog({
      title: 'Delete User',
      message: `Are you sure you want to delete ${username}? This action cannot be undone.`,
      type: 'danger',
      confirmText: 'Delete',
      onConfirm: async () => {
        try {
          await userService.deleteUser(id);
          setSuccess('User deleted successfully');
          loadUsers();
          setConfirmDialog(null);
        } catch (err) {
          console.error('Failed to delete user:', err);
          setError('Failed to delete user');
          setConfirmDialog(null);
        }
      },
      onCancel: () => setConfirmDialog(null)
    });
  };

  const handleResetPassword = (userId, username) => {
    setConfirmDialog({
      title: 'Reset Password',
      message: `Reset password for ${username}? A new temporary password will be generated.`,
      confirmText: 'Reset Password',
      onConfirm: async () => {
        try {
          const response = await userService.resetPassword(userId);
          setCredentials({
            username: response.username,
            password: response.temp_password,
            message: 'Password reset successfully!'
          });
          setSuccess('Password reset successfully!');
          setConfirmDialog(null);
        } catch (err) {
          console.error('Failed to reset password:', err);
          setError('Failed to reset password');
          setConfirmDialog(null);
        }
      },
      onCancel: () => setConfirmDialog(null)
    });
  };

  const resetUserForm = () => {
    setUserForm({
      username: '',
      email: '',
      first_name: '',
      last_name: '',
      password: '',
      password_confirm: '',
      role: 'engineer',
      team: isCoach() && !isAdmin() ? (user.team || '') : '',
      oncall_eligible: true,
    });
    setEditingUser(null);
    setShowUserForm(false);
  };

  // Team management functions
  const handleTeamSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      if (editingTeam) {
        await userService.updateTeam(editingTeam.id, teamForm);
        setSuccess('Team updated successfully');
      } else {
        await userService.createTeam(teamForm);
        setSuccess('Team created successfully');
      }
      resetTeamForm();
      loadTeams();
    } catch (err) {
      console.error('Failed to save team:', err);
      setError(err.response?.data?.detail || 'Failed to save team');
    }
  };

  const handleEditTeam = (team) => {
    setEditingTeam(team);
    setTeamForm({
      name: team.name,
      coach: team.coach || '',
      max_concurrent_off: team.max_concurrent_off,
      description: team.description || '',
    });
    setShowTeamForm(true);
  };

  const handleDeleteTeamClick = (team) => {
    setConfirmDialog({
      type: 'deleteTeam',
      item: team,
      message: `Are you sure you want to delete the team "${team.name}"?`,
      action: handleDeleteTeam
    });
  };

  const handleDeleteTeam = async () => {
    const team = confirmDialog.item;
    setConfirmDialog(null);
    
    try {
      await userService.deleteTeam(team.id);
      setSuccess('Team deleted successfully');
      loadTeams();
    } catch (err) {
      console.error('Failed to delete team:', err);
      setError('Failed to delete team');
    }
  };

  const resetTeamForm = () => {
    setTeamForm({
      name: '',
      coach: '',
      max_concurrent_off: 2,
      description: '',
    });
    setEditingTeam(null);
    setShowTeamForm(false);
  };

  // Holiday management functions
  const handleHolidaySubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      if (editingHoliday) {
        await oncallService.updateHoliday(editingHoliday.id, holidayForm);
        setSuccess('Holiday updated successfully');
      } else {
        await oncallService.createHoliday(holidayForm);
        setSuccess('Holiday created successfully');
      }
      resetHolidayForm();
      loadHolidays();
    } catch (err) {
      console.error('Failed to save holiday:', err);
      setError(err.response?.data?.detail || 'Failed to save holiday');
    }
  };

  const handleEditHoliday = (holiday) => {
    setEditingHoliday(holiday);
    setHolidayForm({
      name: holiday.name,
      date: holiday.date,
      is_recurring: holiday.is_recurring,
      description: holiday.description || '',
    });
    setShowHolidayForm(true);
  };

  const handleDeleteHolidayClick = (holiday) => {
    setConfirmDialog({
      type: 'deleteHoliday',
      item: holiday,
      message: `Are you sure you want to delete the holiday "${holiday.name}"?`,
      action: handleDeleteHoliday
    });
  };

  const handleDeleteHoliday = async () => {
    const holiday = confirmDialog.item;
    setConfirmDialog(null);
    
    try {
      await oncallService.deleteHoliday(holiday.id);
      setSuccess('Holiday deleted successfully');
      loadHolidays();
    } catch (err) {
      console.error('Failed to delete holiday:', err);
      setError('Failed to delete holiday');
    }
  };

  const resetHolidayForm = () => {
    setHolidayForm({
      name: '',
      date: '',
      is_recurring: false,
      description: '',
    });
    setEditingHoliday(null);
    setShowHolidayForm(false);
  };

  if (!isCoach() && !isAdmin()) {
    return (
      <div className="admin-panel">
        <div className="alert alert-error">
          Access denied. Coach or Admin privileges required.
        </div>
      </div>
    );
  }

  return (
    <div className="admin-panel">
      <div className="page-header">
        <h1>Admin Panel</h1>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)} className="alert-close">×</button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
          <button onClick={() => {
            setSuccess(null);
            setCredentials(null);
          }} className="alert-close">×</button>
        </div>
      )}

      {credentials && (
        <div className="credentials-display">
          <div className="credentials-header">
            <h3>⚠️ Important: Save These Credentials</h3>
            <button onClick={() => setCredentials(null)} className="alert-close">×</button>
          </div>
          <p className="credentials-warning">
            This password will not be shown again. The user must change it on first login.
          </p>
          <div className="credential-item">
            <label>Username:</label>
            <div className="credential-value">
              <code>{credentials.username}</code>
              <button
                onClick={() => copyToClipboard(credentials.username, 'username')}
                className="btn btn-sm btn-copy"
                title="Copy username"
              >
                {copiedField === 'username' ? '✓ Copied!' : '📋 Copy'}
              </button>
            </div>
          </div>
          <div className="credential-item">
            <label>Temporary Password:</label>
            <div className="credential-value">
              <code className="password-code">{credentials.password}</code>
              <button
                onClick={() => copyToClipboard(credentials.password, 'password')}
                className="btn btn-sm btn-copy"
                title="Copy password"
              >
                {copiedField === 'password' ? '✓ Copied!' : '📋 Copy'}
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmDialog && (
        <div className="modal-overlay" onClick={() => setConfirmDialog(null)}>
          <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="confirm-header">
              <h3>{confirmDialog.title || 'Confirm Action'}</h3>
            </div>
            <div className="confirm-body">
              <p>{confirmDialog.message}</p>
            </div>
            <div className="confirm-actions">
              <button onClick={confirmDialog.onCancel || (() => setConfirmDialog(null))} className="btn btn-secondary">
                Cancel
              </button>
              <button
                onClick={confirmDialog.onConfirm || confirmDialog.action}
                className={`btn ${confirmDialog.type === 'danger' ? 'btn-danger' : 'btn-primary'}`}
              >
                {confirmDialog.confirmText || (confirmDialog.type === 'danger' ? 'Delete' : 'Confirm')}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="admin-tabs">
        <button
          className={`tab-button ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          Users
        </button>
        <button
          className={`tab-button ${activeTab === 'teams' ? 'active' : ''}`}
          onClick={() => setActiveTab('teams')}
        >
          Teams
        </button>
        <button
          className={`tab-button ${activeTab === 'holidays' ? 'active' : ''}`}
          onClick={() => setActiveTab('holidays')}
        >
          Holidays
        </button>
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="admin-content">
          <div className="content-header">
            <h2>User Management</h2>
            <button
              onClick={() => {
                // Initialize form with coach's team if user is a coach
                if (isCoach() && !isAdmin() && user.team) {
                  setUserForm({
                    username: '',
                    email: '',
                    first_name: '',
                    last_name: '',
                    password: '',
                    password_confirm: '',
                    role: 'engineer',
                    team: user.team,
                    oncall_eligible: true,
                  });
                }
                setShowUserForm(true);
              }}
              className="btn btn-primary"
            >
              Add User
            </button>
          </div>

          <div className="search-bar">
            <input
              type="text"
              placeholder="Search by name, email, or team..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="btn btn-sm btn-secondary"
                style={{ marginLeft: '10px' }}
              >
                Clear
              </button>
            )}
            <span style={{ marginLeft: '15px', color: 'var(--text-secondary)' }}>
              Showing {filteredUsers.length} of {users.length} users
            </span>
          </div>

          {showUserForm && (
            <div className="modal-overlay" onClick={() => resetUserForm()}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>{editingUser ? 'Edit User' : 'Add User'}</h3>
                  <button onClick={() => resetUserForm()} className="modal-close">×</button>
                </div>
                <form onSubmit={handleUserSubmit} className="form">
                  <div className="form-row">
                    <div className="form-group">
                      <label>Username {!editingUser}</label>
                      <input
                        type="text"
                        value={userForm.username}
                        onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
                        required={editingUser}
                        disabled={editingUser}
                        placeholder={!editingUser ? "Leave blank to auto-generate" : ""}
                      />
                    </div>
                    <div className="form-group">
                      <label>Email *</label>
                      <input
                        type="email"
                        value={userForm.email}
                        onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label>First Name *</label>
                      <input
                        type="text"
                        value={userForm.first_name}
                        onChange={(e) => setUserForm({ ...userForm, first_name: e.target.value })}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Last Name *</label>
                      <input
                        type="text"
                        value={userForm.last_name}
                        onChange={(e) => setUserForm({ ...userForm, last_name: e.target.value })}
                        required
                      />
                    </div>
                  </div>

                  {!editingUser && (
                    <>
                      <div className="form-info">
                        <strong>Password:</strong> Leave blank to auto-generate a temporary password.
                        The user will be required to change it on first login.
                      </div>
                      <div className="form-row">
                        <div className="form-group">
                          <label>Password (optional)</label>
                          <input
                            type="password"
                            value={userForm.password}
                            onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                            placeholder="Leave blank to auto-generate"
                          />
                        </div>
                        <div className="form-group">
                          <label>Confirm Password</label>
                          <input
                            type="password"
                            value={userForm.password_confirm}
                            onChange={(e) => setUserForm({ ...userForm, password_confirm: e.target.value })}
                            placeholder="Leave blank to auto-generate"
                          />
                        </div>
                      </div>
                    </>
                  )}

                  <div className="form-row">
                    <div className="form-group">
                      <label>Role *</label>
                      <select
                        value={userForm.role}
                        onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                        required
                      >
                        <option value="engineer">Engineer</option>
                        <option value="coach">Coach</option>
                        <option value="admin">Admin</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Team</label>
                      <select
                        value={userForm.team}
                        onChange={(e) => setUserForm({ ...userForm, team: e.target.value })}
                        disabled={isCoach() && !isAdmin()}
                      >
                        <option value="">No Team</option>
                        {teams
                          .filter(team => isAdmin() || (isCoach() && team.coach === user.id))
                          .map(team => (
                            <option key={team.id} value={team.id}>{team.name}</option>
                          ))}
                      </select>
                      {isCoach() && !isAdmin() && (
                        <small style={{color: 'var(--text-secondary)', marginTop: '5px', display: 'block'}}>
                          You can only add members to your own team
                        </small>
                      )}
                    </div>
                  </div>

                  {userForm.role === 'engineer' && (
                    <div className="form-group" style={{ marginTop: '15px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={userForm.oncall_eligible}
                          onChange={(e) => setUserForm({ ...userForm, oncall_eligible: e.target.checked })}
                          style={{ marginRight: '10px', width: '18px', height: '18px', cursor: 'pointer' }}
                        />
                        <span>On-Call Eligible</span>
                      </label>
                      <small style={{color: 'var(--text-secondary)', marginTop: '5px', display: 'block', marginLeft: '28px'}}>
                        Uncheck to exclude this engineer from on-call rotation assignments
                      </small>
                    </div>
                  )}

                  <div className="form-actions">
                    <button type="button" onClick={() => resetUserForm()} className="btn btn-secondary">
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary">
                      {editingUser ? 'Update' : 'Create'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {loading ? (
            <div className="loading-spinner"><div className="spinner"></div></div>
          ) : (
            <div className="data-table">
              <table>
                <thead>
                  <tr>
                    <th onClick={() => handleSort('username')} style={{ cursor: 'pointer' }}>
                      Username{getSortIndicator('username')}
                    </th>
                    <th onClick={() => handleSort('full_name')} style={{ cursor: 'pointer' }}>
                      Name{getSortIndicator('full_name')}
                    </th>
                    <th onClick={() => handleSort('email')} style={{ cursor: 'pointer' }}>
                      Email{getSortIndicator('email')}
                    </th>
                    <th onClick={() => handleSort('role')} style={{ cursor: 'pointer' }}>
                      Role{getSortIndicator('role')}
                    </th>
                    <th onClick={() => handleSort('team_name')} style={{ cursor: 'pointer' }}>
                      Team{getSortIndicator('team_name')}
                    </th>
                    <th onClick={() => handleSort('oncall_eligible')} style={{ cursor: 'pointer' }}>
                      On-Call{getSortIndicator('oncall_eligible')}
                    </th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '20px', color: 'var(--text-secondary)' }}>
                        {searchQuery ? 'No users found matching your search' : 'No users found'}
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map(user => (
                      <tr key={user.id}>
                        <td>{user.username}</td>
                        <td>{user.full_name}</td>
                        <td>{user.email}</td>
                        <td><span className={`badge badge-${user.role}`}>{user.role}</span></td>
                        <td>{user.team_name || '-'}</td>
                        <td>
                          {user.role === 'engineer' ? (
                            <span style={{
                              color: user.oncall_eligible ? 'var(--success-color, #28a745)' : 'var(--text-tertiary)',
                              fontWeight: '500'
                            }}>
                              {user.oncall_eligible ? '✓ Yes' : '✗ No'}
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-tertiary)' }}>N/A</span>
                          )}
                        </td>
                        <td>
                          <button onClick={() => handleEditUser(user)} className="btn btn-sm btn-secondary">
                            Edit
                          </button>
                          <button onClick={() => handleResetPassword(user.id, user.username)} className="btn btn-sm btn-warning">
                            Reset Password
                          </button>
                          {(isCoach() || isAdmin()) && (
                            <button onClick={() => handleDeleteUser(user.id, user.username)} className="btn btn-sm btn-danger">
                              Delete
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Teams Tab */}
      {activeTab === 'teams' && (
        <div className="admin-content">
          <div className="content-header">
            <h2>Team Management</h2>
            <button
              onClick={() => setShowTeamForm(true)}
              className="btn btn-primary"
            >
              Add Team
            </button>
          </div>

          {showTeamForm && (
            <div className="modal-overlay" onClick={() => resetTeamForm()}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>{editingTeam ? 'Edit Team' : 'Add Team'}</h3>
                  <button onClick={() => resetTeamForm()} className="modal-close">×</button>
                </div>
                <form onSubmit={handleTeamSubmit} className="form">
                  <div className="form-group">
                    <label>Team Name *</label>
                    <input
                      type="text"
                      value={teamForm.name}
                      onChange={(e) => setTeamForm({ ...teamForm, name: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Coach</label>
                    <select
                      value={teamForm.coach}
                      onChange={(e) => setTeamForm({ ...teamForm, coach: e.target.value })}
                    >
                      <option value="">No Coach</option>
                      {users.filter(u => u.role === 'coach' || u.role === 'admin').map(user => (
                        <option key={user.id} value={user.id}>{user.full_name}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Max Concurrent Off *</label>
                    <input
                      type="number"
                      min="1"
                      value={teamForm.max_concurrent_off}
                      onChange={(e) => setTeamForm({ ...teamForm, max_concurrent_off: parseInt(e.target.value) })}
                      required
                    />
                    <small>Maximum number of team members that can be off on the same day</small>
                  </div>

                  <div className="form-group">
                    <label>Description</label>
                    <textarea
                      value={teamForm.description}
                      onChange={(e) => setTeamForm({ ...teamForm, description: e.target.value })}
                      rows="3"
                    />
                  </div>

                  <div className="form-actions">
                    <button type="button" onClick={() => resetTeamForm()} className="btn btn-secondary">
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary">
                      {editingTeam ? 'Update' : 'Create'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {loading ? (
            <div className="loading-spinner"><div className="spinner"></div></div>
          ) : (
            <div className="data-table">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Coach</th>
                    <th>Members</th>
                    <th>Max Off</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {teams.map(team => (
                    <tr key={team.id}>
                      <td>{team.name}</td>
                      <td>{team.coach_name}</td>
                      <td>{team.member_count}</td>
                      <td>{team.max_concurrent_off}</td>
                      <td>
                        <button onClick={() => handleEditTeam(team)} className="btn btn-sm btn-secondary">
                          Edit
                        </button>
                        <button onClick={() => handleDeleteTeamClick(team)} className="btn btn-sm btn-danger">
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Holidays Tab */}
      {activeTab === 'holidays' && (
        <div className="admin-content">
          <div className="content-header">
            <h2>Holiday Management</h2>
            <button
              onClick={() => setShowHolidayForm(true)}
              className="btn btn-primary"
            >
              Add Holiday
            </button>
          </div>

          {showHolidayForm && (
            <div className="modal-overlay" onClick={() => resetHolidayForm()}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>{editingHoliday ? 'Edit Holiday' : 'Add Holiday'}</h3>
                  <button onClick={() => resetHolidayForm()} className="modal-close">×</button>
                </div>
                <form onSubmit={handleHolidaySubmit} className="form">
                  <div className="form-group">
                    <label>Holiday Name *</label>
                    <input
                      type="text"
                      value={holidayForm.name}
                      onChange={(e) => setHolidayForm({ ...holidayForm, name: e.target.value })}
                      required
                      placeholder="e.g., Christmas, New Year's Day"
                    />
                  </div>

                  <div className="form-group">
                    <label>Date *</label>
                    <input
                      type="date"
                      value={holidayForm.date}
                      onChange={(e) => setHolidayForm({ ...holidayForm, date: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={holidayForm.is_recurring}
                        onChange={(e) => setHolidayForm({ ...holidayForm, is_recurring: e.target.checked })}
                      />
                      Recurring annually
                    </label>
                  </div>

                  <div className="form-group">
                    <label>Description</label>
                    <textarea
                      value={holidayForm.description}
                      onChange={(e) => setHolidayForm({ ...holidayForm, description: e.target.value })}
                      rows="3"
                    />
                  </div>

                  <div className="form-actions">
                    <button type="button" onClick={() => resetHolidayForm()} className="btn btn-secondary">
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary">
                      {editingHoliday ? 'Update' : 'Create'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {loading ? (
            <div className="loading-spinner"><div className="spinner"></div></div>
          ) : (
            <div className="data-table">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Date</th>
                    <th>Recurring</th>
                    <th>Description</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {holidays.map(holiday => (
                    <tr key={holiday.id}>
                      <td>{holiday.name}</td>
                      <td>{holiday.date}</td>
                      <td>{holiday.is_recurring ? 'Yes' : 'No'}</td>
                      <td>{holiday.description || '-'}</td>
                      <td>
                        <button onClick={() => handleEditHoliday(holiday)} className="btn btn-sm btn-secondary">
                          Edit
                        </button>
                        <button onClick={() => handleDeleteHolidayClick(holiday)} className="btn btn-sm btn-danger">
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdminPanel;

// Made with Bob
