# Calendar App Frontend

React-based frontend for the Calendar Application with time-off management and on-call rotation scheduling.

## Features

- **Authentication**: Login/logout with role-based access control
- **Dashboard**: Overview of time-off, on-call shifts, and days in lieu
- **Calendar View**: Unified calendar showing all events with filtering
- **Time-Off Management**: Request, view, and manage time-off requests
- **On-Call Schedule**: View and manage on-call rotation
- **Days in Lieu**: Track automatically generated compensation days
- **Coach Dashboard**: Approve requests and manage team schedules
- **Admin Panel**: User and team management

## Tech Stack

- React 18
- React Router v6
- Axios for API calls
- FullCalendar for calendar visualization
- date-fns for date manipulation

## Prerequisites

- Node.js 16+ and npm
- Backend API running on http://localhost:8000

## Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and set your backend API URL
REACT_APP_API_URL=http://localhost:8000/api
```

## Development

Start the development server:
```bash
npm start
```

The app will open at http://localhost:3000

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── Layout.js       # Main layout with navigation
│   ├── Login.js        # Login form
│   └── PrivateRoute.js # Protected route wrapper
├── contexts/           # React contexts
│   └── AuthContext.js  # Authentication state management
├── pages/              # Page components
│   ├── Dashboard.js    # Main dashboard
│   ├── Calendar.js     # Calendar view
│   ├── TimeOffRequests.js
│   ├── OnCallSchedule.js
│   ├── DaysInLieu.js
│   ├── CoachDashboard.js
│   └── AdminPanel.js
├── services/           # API service layer
│   ├── api.js          # Axios instance with interceptors
│   ├── authService.js  # Authentication methods
│   ├── calendarService.js
│   ├── timeoffService.js
│   ├── oncallService.js
│   └── userService.js
├── App.js              # Main app with routing
└── index.js            # Entry point
```

## Available Scripts

- `npm start` - Start development server
- `npm test` - Run tests
- `npm run build` - Build for production
- `npm run eject` - Eject from Create React App (one-way operation)

## Authentication

The app uses token-based authentication. Tokens are stored in localStorage and automatically included in API requests via Axios interceptors.

### User Roles

- **Engineer**: Can view calendar, request time-off, view on-call shifts
- **Coach**: All engineer permissions + approve requests, manage team schedule
- **Admin**: All permissions + user/team management

## API Integration

All API calls go through service files in `src/services/`. Each service exports methods that correspond to backend API endpoints.

Example:
```javascript
import timeoffService from '../services/timeoffService';

// Get my time-off requests
const requests = await timeoffService.getMyRequests();

// Create new request
const newRequest = await timeoffService.createRequest({
  start_date: '2024-01-15',
  end_date: '2024-01-19',
  reason: 'Vacation'
});
```

## Environment Variables

- `REACT_APP_API_URL` - Backend API base URL (default: http://localhost:8000/api)

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Deployment

The production build can be served by any static file server:

```bash
# Using serve
npm install -g serve
serve -s build -l 3000

# Using nginx, apache, etc.
# Copy build/ contents to web server root
```

## Current Status

### Completed ✅
- Project setup and configuration
- Service layer (API integration)
- Authentication system
- Routing and navigation
- Layout and basic UI components
- Dashboard page with data loading

### In Progress 🔄
- Calendar view with FullCalendar
- Time-off request forms
- Coach dashboard features

### Pending 📋
- On-call rotation management UI
- Days in lieu tracking UI
- Admin panel features
- Conflict detection warnings
- Notifications

## Next Steps

1. Implement FullCalendar integration in Calendar.js
2. Build time-off request form with validation
3. Add coach approval workflow UI
4. Implement on-call rotation generation interface
5. Add real-time conflict detection
6. Build notification system

## Contributing

When adding new features:
1. Create service methods in appropriate service file
2. Add page components in `src/pages/`
3. Update routing in `App.js`
4. Add navigation links in `Layout.js`
5. Update this README

## License

Proprietary - Internal use only
