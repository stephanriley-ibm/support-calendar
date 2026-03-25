# Calendar Application - Project Structure

## Directory Layout

```
calendar-app/
├── backend/                          # Django backend
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── config/                       # Project configuration
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Base settings
│   │   │   ├── development.py       # Dev settings
│   │   │   └── production.py        # Prod settings
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── apps/                         # Django apps
│   │   ├── users/                    # User management
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # User, Team models
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── permissions.py
│   │   │   └── tests/
│   │   │
│   │   ├── timeoff/                  # Time-off management
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # TimeOffRequest model
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── services.py          # Business logic
│   │   │   ├── validators.py        # Conflict detection
│   │   │   └── tests/
│   │   │
│   │   ├── oncall/                   # On-call rotation
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # OnCallShift, DayInLieu
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── services.py          # Rotation algorithm
│   │   │   ├── generators.py        # Days-in-lieu generation
│   │   │   └── tests/
│   │   │
│   │   ├── calendar/                 # Calendar aggregation
│   │   │   ├── __init__.py
│   │   │   ├── views.py             # Calendar API
│   │   │   ├── urls.py
│   │   │   ├── services.py          # Event aggregation
│   │   │   └── tests/
│   │   │
│   │   └── notifications/            # Notification system
│   │       ├── __init__.py
│   │       ├── models.py
│   │       ├── services.py          # Email/notification logic
│   │       ├── tasks.py             # Celery tasks
│   │       └── tests/
│   │
│   └── utils/                        # Shared utilities
│       ├── __init__.py
│       ├── date_helpers.py
│       ├── permissions.py
│       └── exceptions.py
│
├── frontend/                         # React frontend
│   ├── package.json
│   ├── .env.example
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   └── src/
│       ├── index.js
│       ├── App.js
│       ├── App.css
│       │
│       ├── components/               # Reusable components
│       │   ├── common/
│       │   │   ├── Button.js
│       │   │   ├── Modal.js
│       │   │   ├── DatePicker.js
│       │   │   ├── LoadingSpinner.js
│       │   │   └── ErrorBoundary.js
│       │   │
│       │   ├── layout/
│       │   │   ├── Header.js
│       │   │   ├── Navigation.js
│       │   │   ├── Sidebar.js
│       │   │   └── Footer.js
│       │   │
│       │   ├── calendar/
│       │   │   ├── CalendarView.js
│       │   │   ├── CalendarFilters.js
│       │   │   ├── EventCard.js
│       │   │   └── EventDetailsModal.js
│       │   │
│       │   ├── timeoff/
│       │   │   ├── TimeOffForm.js
│       │   │   ├── TimeOffList.js
│       │   │   ├── TimeOffCard.js
│       │   │   └── ConflictWarning.js
│       │   │
│       │   ├── oncall/
│       │   │   ├── OnCallSchedule.js
│       │   │   ├── ShiftCard.js
│       │   │   ├── RotationGenerator.js
│       │   │   └── ManualShiftForm.js
│       │   │
│       │   └── coach/
│       │       ├── CoachDashboard.js
│       │       ├── PendingRequestsList.js
│       │       ├── ApprovalActions.js
│       │       └── TeamCalendar.js
│       │
│       ├── pages/                    # Page components
│       │   ├── Dashboard.js
│       │   ├── Calendar.js
│       │   ├── TimeOff.js
│       │   ├── OnCall.js
│       │   ├── Coach.js
│       │   ├── Profile.js
│       │   ├── Login.js
│       │   └── NotFound.js
│       │
│       ├── services/                 # API services
│       │   ├── api.js               # Axios instance
│       │   ├── authService.js
│       │   ├── timeoffService.js
│       │   ├── oncallService.js
│       │   └── calendarService.js
│       │
│       ├── store/                    # State management
│       │   ├── index.js
│       │   ├── authSlice.js
│       │   ├── timeoffSlice.js
│       │   ├── oncallSlice.js
│       │   └── calendarSlice.js
│       │
│       ├── hooks/                    # Custom hooks
│       │   ├── useAuth.js
│       │   ├── useCalendar.js
│       │   ├── useTimeOff.js
│       │   └── useOnCall.js
│       │
│       ├── utils/                    # Utility functions
│       │   ├── dateHelpers.js
│       │   ├── validators.js
│       │   ├── formatters.js
│       │   └── constants.js
│       │
│       └── styles/                   # Global styles
│           ├── variables.css
│           ├── theme.js
│           └── global.css
│
├── docs/                             # Documentation
│   ├── api/                          # API documentation
│   ├── user-guide/                   # User guides
│   └── development/                  # Dev documentation
│
├── scripts/                          # Utility scripts
│   ├── setup.sh                      # Initial setup
│   ├── seed_data.py                  # Database seeding
│   └── deploy.sh                     # Deployment script
│
├── docker/                           # Docker configuration
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── .gitignore
├── README.md
└── LICENSE
```

## Key Files and Their Purposes

### Backend Key Files

#### `backend/config/settings/base.py`
Core Django settings shared across all environments:
- Installed apps configuration
- Middleware setup
- Database configuration
- REST Framework settings
- Authentication settings

#### `backend/apps/users/models.py`
```python
# User model with role-based permissions
# Team model for organizing engineers
# Coach relationship management
```

#### `backend/apps/timeoff/services.py`
```python
# TimeOffService class
# - create_request()
# - approve_request()
# - reject_request()
# - check_conflicts()
# - get_team_availability()
```

#### `backend/apps/oncall/services.py`
```python
# OnCallRotationService class
# - generate_rotation()
# - assign_shifts()
# - calculate_fairness()
# - check_availability()
```

#### `backend/apps/oncall/generators.py`
```python
# DaysInLieuGenerator class
# - generate_for_shift()
# - calculate_dates()
# - create_records()
```

### Frontend Key Files

#### `frontend/src/App.js`
Main application component with routing and authentication wrapper

#### `frontend/src/services/api.js`
```javascript
// Axios instance with:
// - Base URL configuration
// - Authentication interceptors
// - Error handling
// - Request/response transformers
```

#### `frontend/src/components/calendar/CalendarView.js`
```javascript
// Main calendar component using FullCalendar
// - Event rendering
// - Filter integration
// - Click handlers
// - Responsive views
```

#### `frontend/src/store/index.js`
```javascript
// Redux store configuration
// - Combined reducers
// - Middleware setup
// - Persistence configuration
```

## Development Workflow

### Backend Development

1. **Create new feature**
   ```bash
   cd backend
   python manage.py startapp feature_name
   ```

2. **Create models**
   - Define in `models.py`
   - Create migrations: `python manage.py makemigrations`
   - Apply migrations: `python manage.py migrate`

3. **Create API endpoints**
   - Define serializers in `serializers.py`
   - Create views in `views.py`
   - Register URLs in `urls.py`

4. **Write tests**
   - Unit tests in `tests/test_models.py`
   - API tests in `tests/test_views.py`
   - Run: `pytest`

### Frontend Development

1. **Create new component**
   ```bash
   cd frontend/src/components
   mkdir feature_name
   touch feature_name/FeatureName.js
   ```

2. **Create service**
   - Add API calls in `services/featureService.js`
   - Use axios instance from `services/api.js`

3. **Add state management**
   - Create slice in `store/featureSlice.js`
   - Add to store configuration

4. **Write tests**
   - Component tests with React Testing Library
   - Run: `npm test`

## Environment Configuration

### Backend `.env`
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/calendar_db
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Email configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# PagerDuty (optional)
PAGERDUTY_API_KEY=your-api-key
```

### Frontend `.env`
```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENV=development
```

## Database Setup

### PostgreSQL Database Creation
```sql
CREATE DATABASE calendar_db;
CREATE USER calendar_user WITH PASSWORD 'your_password';
ALTER ROLE calendar_user SET client_encoding TO 'utf8';
ALTER ROLE calendar_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE calendar_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE calendar_db TO calendar_user;
```

### Initial Migrations
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Running the Application

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Celery (for background tasks)
```bash
cd backend
celery -A config worker -l info
celery -A config beat -l info  # For scheduled tasks
```

## Testing Strategy

### Backend Tests
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test API endpoints
- **Model Tests**: Test database models and relationships
- **Service Tests**: Test business logic

### Frontend Tests
- **Component Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user flows (Cypress)

## Deployment Considerations

### Backend Deployment
- Use Gunicorn as WSGI server
- Configure Nginx as reverse proxy
- Set up PostgreSQL with replication
- Configure Redis for caching and Celery
- Set up SSL certificates
- Configure environment variables

### Frontend Deployment
- Build production bundle: `npm run build`
- Serve static files via CDN
- Configure environment variables
- Set up CI/CD pipeline

## Git Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches
- `hotfix/*`: Production hotfixes

### Commit Convention
```
type(scope): subject

body

footer
```

Types: feat, fix, docs, style, refactor, test, chore

## Next Steps

1. Review this structure with the team
2. Set up development environment
3. Initialize Git repository
4. Create initial project scaffolding
5. Begin Phase 1 implementation
