# Calendar Application - Project Status

**Last Updated:** 2026-04-02  
**Version:** v1.0 (UAT Testing Phase)  
**Repository:** https://github.com/your-org/calendar_app

## 📋 Project Overview

A comprehensive calendar application for managing time-off requests and on-call rotations with role-based permissions.

### Core Features
- **Time-Off Management**: Request, approve/reject time-off with conflict detection (max 2 engineers per team per day)
- **On-Call Rotation**: Automated weekend shift generation (Early Primary, Late Primary, Secondary) with manual holiday shift creation
- **Days-in-Lieu**: Automatic generation based on shift type (Thu-Fri, Wed, Mon-Tue)
- **Role-Based Access**: Engineer, Coach, and Admin roles with appropriate permissions
- **Dark Mode**: User-toggleable theme
- **Multi-Team Support**: Manage multiple teams and their schedules

### Technology Stack
- **Backend**: Django 4.2.27, Django REST Framework, PostgreSQL
- **Frontend**: React, Axios, FullCalendar
- **Authentication**: Token-based authentication (DRF Token)
- **Deployment**: Ubuntu 24.04, Gunicorn, Nginx

## 🚀 Current State

### Deployment Status
- **Local Development**: ✅ Fully functional with SQLite
- **UAT Server**: ⚠️ Deployed at `http://9.60.151.79`, currently testing
- **Production**: ❌ Not yet deployed

### Recent Changes (Last 7 Days)

#### 2026-04-02: CSRF Error Resolution & Frontend Caching
- **Fixed**: Removed `SessionAuthentication` from REST_FRAMEWORK settings to resolve CSRF token errors
- **Fixed**: Removed `CORS_ALLOW_CREDENTIALS = True` (wasn't in original working config)
- **Fixed**: Password reset button bug in AdminPanel.js (was showing "Delete" instead of "Reset Password")
- **Fixed**: Login error handling in api.js (incorrect URL check `/auth/login` → `/users/login`)
- **Enhanced**: Error message extraction in AuthContext.js to handle multiple response formats
- **Documented**: Frontend rebuild requirement for UAT deployments

#### 2026-04-01: Environment Configuration System
- **Implemented**: Environment-based configuration using `python-dotenv`
- **Created**: `.env.local` for local development (SQLite)
- **Created**: `.env.uat` template for UAT deployment (PostgreSQL)
- **Updated**: `settings.py` to read from environment variables
- **Created**: `ENVIRONMENT_SETUP.md` documentation
- **Created**: `DEPLOYMENT_WORKFLOW.md` guide
- **Updated**: `.gitignore` to exclude `backend/staticfiles/` and `frontend/build/`

#### Previous Work
- Implemented all core features (time-off, on-call, admin panel)
- Added dark mode theme toggle
- Created comprehensive admin panel with user management
- Implemented temporary password system with forced password change
- Extended admin access to coaches with team-restricted permissions

## 🐛 Known Issues

### Critical
None currently

### High Priority
1. **Frontend Caching on UAT**: After code changes, frontend must be rebuilt (`npm run build`) for changes to appear
2. **node_modules Permissions**: Permission denied errors when running `npm run build` on UAT
   - **Workaround**: `sudo chown -R sriley:sriley node_modules && sudo chmod -R 755 node_modules`

### Medium Priority
None currently

### Low Priority
None currently

## 📁 Key Files & Locations

### Backend
- **Settings**: `backend/config/settings.py` - Main Django configuration
- **Environment**: `backend/.env` - Environment-specific configuration (not in git)
- **User Auth**: `backend/users/views.py` - Login endpoint at line 153-193
- **Models**: `backend/users/models.py`, `backend/timeoff/models.py`, `backend/oncall/models.py`

### Frontend
- **API Client**: `frontend/src/services/api.js` - Axios configuration with interceptors
- **Auth Context**: `frontend/src/contexts/AuthContext.js` - Authentication state management
- **Login**: `frontend/src/components/Login.js` - Login form with error handling
- **Admin Panel**: `frontend/src/components/AdminPanel.js` - User management interface
- **Calendar**: `frontend/src/components/Calendar.js` - Main calendar view

### Documentation
- **Environment Setup**: `ENVIRONMENT_SETUP.md` - Configuration guide
- **Deployment**: `DEPLOYMENT_WORKFLOW.md` - Deployment procedures
- **Git Permissions**: `FIX_GIT_PERMISSIONS.md` - Troubleshooting guide
- **Project Structure**: `project-structure.md` - Architecture overview

## 🔧 Configuration

### Important Settings Changes
- **Removed**: `CORS_ALLOW_CREDENTIALS = True` (was causing CSRF errors)
- **Removed**: `SessionAuthentication` from REST_FRAMEWORK (only using TokenAuthentication)

## 🚢 Deployment Process

### Backend Changes Only
```bash
cd /var/www/support_calendar
git pull origin main
sudo systemctl restart support_calendar.service
```

### Frontend Changes (REQUIRED for UI updates)
```bash
cd /var/www/support_calendar
git pull origin main
cd frontend
npm run build
sudo systemctl restart nginx
```

### Full Deployment (Backend + Frontend)
```bash
cd /var/www/support_calendar
git pull origin main
sudo systemctl restart support_calendar.service
cd frontend
npm run build
sudo systemctl restart nginx
```

### After Deployment
- Hard refresh browser: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (Mac)

## 📝 Next Steps

### Immediate (This Week)
1. ✅ Fix CSRF error on UAT (COMPLETED)
2. ✅ Fix password reset button bug (COMPLETED)
3. ⏳ Fix node_modules permissions on UAT
4. ⏳ Complete UAT testing with all user roles
5. ⏳ Verify all features work on UAT

### Short Term (Next 2 Weeks)
1. Create notification system for:
   - Time-off request approvals/rejections
   - On-call shift assignments
   - Days-in-lieu generation
2. Write comprehensive user guide
3. Create admin documentation
4. Performance testing and optimization

### Medium Term (Next Month)
1. Production deployment planning
2. Backup and disaster recovery procedures
3. Monitoring and alerting setup
4. User training sessions

### Future Enhancements
1. Email notifications
2. Mobile responsive improvements
3. Calendar export (iCal format)
4. Reporting and analytics dashboard
5. Integration with PagerDuty or similar tools

## 🔍 Testing Checklist

### UAT Testing Status
- [ ] User login/logout
- [ ] Password reset functionality
- [ ] Time-off request creation
- [ ] Time-off approval/rejection (Coach)
- [ ] Conflict detection
- [ ] On-call rotation generation
- [ ] Manual holiday shift creation
- [ ] Days-in-lieu tracking
- [ ] Admin panel user management
- [ ] Dark mode toggle
- [ ] Multi-team support
- [ ] Calendar filtering

## 📞 Support & Contacts

### Development Team
- **Lead Developer**: [Your Name]
- **Repository**: https://github.com/your-org/calendar_app

### UAT Server
- **IP**: 9.60.151.79
- **SSH**: `ssh fyre.calendar`
- **Location**: `/var/www/support_calendar`

### Database
- **Type**: PostgreSQL
- **Name**: support_calendar_db
- **User**: support_calendar_user

## 🔐 Security Notes

- `.env` files are excluded from git (contain sensitive data)
- `DEBUG=False` on UAT/Production
- Strong database passwords in use
- Token-based authentication (no session cookies)
- CSRF protection configured for production

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [FullCalendar Documentation](https://fullcalendar.io/docs)

---

**Note**: This document should be updated after major changes or deployments. Keep it current to help future developers (or future you!) understand the project state quickly.