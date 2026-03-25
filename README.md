# Calendar Application - Team Time-Off & On-Call Rotation Manager

A comprehensive web application for managing team time-off requests and automated on-call weekend rotations with days-in-lieu compensation.

## 📋 Project Overview

This application provides a centralized system for:
- **Time-Off Management**: Submit, approve, and track time-off requests with conflict detection
- **On-Call Rotation**: Automated weekend shift scheduling with fair distribution
- **Days-in-Lieu**: Automatic compensation day scheduling for on-call engineers
- **Team Visibility**: Multi-level calendar views (user, team, organization)
- **Coach Dashboard**: Streamlined approval workflow for team managers

## 🏗️ Architecture

- **Backend**: Django 4.2+ with Django REST Framework
- **Frontend**: React 18+ with Redux Toolkit
- **Database**: PostgreSQL 14+
- **Task Queue**: Celery with Redis

## 📚 Documentation

This project includes comprehensive documentation:

1. **[Technical Specification](calendar-app-technical-spec.md)** - Complete system architecture, database schema, API endpoints, and business rules
2. **[Project Structure](project-structure.md)** - Detailed directory layout and file organization
3. **[Implementation Guide](implementation-guide.md)** - Step-by-step implementation instructions with code examples

## 🎯 Key Features

### Time-Off Management
- Submit time-off requests with date ranges and reasons
- Automatic conflict detection (max 2 engineers per team per day)
- Coach approval workflow
- Calendar integration with visual indicators

### On-Call Rotation System
- **Weekend Structure**:
  - Saturday: Early Primary, Late Primary, Secondary shifts
  - Sunday: Early Primary, Late Primary (with cross-coverage)
- **Automated Days-in-Lieu**:
  - Early Primary: Thursday + Friday following week
  - Late Primary: Monday + Tuesday following week
  - Saturday Secondary: Wednesday following week
- Fair distribution algorithm
- Manual holiday shift creation
- PagerDuty integration ready

### User Roles
- **Engineer**: Submit requests, view calendar, track days-in-lieu
- **Coach**: Approve requests, manage team calendar
- **Admin**: System configuration, rotation generation

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 14+
- Redis (for Celery)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 📊 Development Roadmap

### Phase 1: Foundation (Weeks 1-2)
- Project setup and configuration
- User authentication and basic models
- React project initialization

### Phase 2: Core Features (Weeks 3-4)
- Time-off request system
- Conflict detection
- Calendar view implementation

### Phase 3: On-Call System (Weeks 5-6)
- Rotation algorithm
- Days-in-lieu generation
- On-call management UI

### Phase 4: Coach Features (Week 7)
- Coach dashboard
- Approval workflow
- Notification system

### Phase 5: Polish & Testing (Week 8)
- Comprehensive testing
- UI/UX improvements
- Documentation and deployment

## 🔐 Security

- Token-based authentication
- Role-based access control
- Input validation and sanitization
- HTTPS enforcement in production

## 📈 Future Enhancements

- PagerDuty integration for schedule sync
- Google Calendar / Outlook integration
- Mobile app (React Native)
- Advanced analytics and reporting
- Slack/Teams notifications

## 📝 License

[Your License Here]

## 👥 Team

[Your Team Information]

## 📞 Support

For questions or issues, please contact [Your Contact Information]

---

**Note**: This is a planning document. Refer to the detailed technical specification and implementation guide for complete development instructions.