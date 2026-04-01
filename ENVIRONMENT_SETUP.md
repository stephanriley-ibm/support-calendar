# Environment Configuration Guide

This guide explains how to configure the application for different environments (local development, UAT, production) using environment variables.

## Overview

The application uses `python-dotenv` to load environment-specific configuration from `.env` files. This allows you to:
- Keep sensitive data (passwords, secret keys) out of version control
- Use the same codebase across different environments
- Easily switch between SQLite (local) and PostgreSQL (UAT/production)
- Deploy to UAT without modifying settings.py

## How It Works

1. **settings.py** reads environment variables using `os.getenv()`
2. **python-dotenv** loads variables from a `.env` file in the backend directory
3. Each environment has its own `.env` file with appropriate values
4. The `.env` file is excluded from git (in `.gitignore`)

## Environment Files

### `.env.local` - Local Development
Use this for local development with SQLite database:

```bash
# Copy to .env for local development
cp backend/.env.local backend/.env
```

**Features:**
- DEBUG=True for detailed error messages
- Uses SQLite database (no PostgreSQL needed)
- Allows localhost and 127.0.0.1
- CORS configured for React dev server on port 3000

### `.env.uat` - UAT/Testing Environment
Use this template for your UAT server:

```bash
# On UAT server, copy and customize
cp backend/.env.uat backend/.env
# Then edit backend/.env with your actual values
```

**Features:**
- DEBUG=False for security
- Uses PostgreSQL database
- Configured for your UAT server IP/domain
- CORS configured for production frontend

### `.env.example` - Documentation
Reference file showing all available environment variables. Not used directly.

## Setup Instructions

### Local Development Setup

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Create your .env file:**
   ```bash
   cp .env.local .env
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run development server:**
   ```bash
   python manage.py runserver
   ```

### UAT/Production Setup

1. **Copy the UAT template:**
   ```bash
   cd /var/www/support_calendar/backend
   cp .env.uat .env
   ```

2. **Edit .env with your actual values:**
   ```bash
   nano .env
   ```

3. **Generate a secure SECRET_KEY:**
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Update the .env file:**
   ```bash
   SECRET_KEY=your-generated-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=9.60.151.79,your-domain.com
   
   DB_NAME=support_calendar
   DB_USER=calendar_user
   DB_PASSWORD=your-secure-password
   DB_HOST=localhost
   DB_PORT=5432
   
   STATIC_URL=/django-static/
   
   CORS_ALLOWED_ORIGINS=http://9.60.151.79,http://your-domain.com
   ```

5. **Restart services:**
   ```bash
   sudo systemctl restart calendar-backend
   sudo systemctl restart nginx
   ```

## Environment Variables Reference

### Django Settings

| Variable | Description | Local Default | UAT/Prod |
|----------|-------------|---------------|----------|
| `SECRET_KEY` | Django secret key for cryptographic signing | Development key | Generate new secure key |
| `DEBUG` | Enable debug mode | `True` | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` | Your server IP/domain |

### Database Settings

| Variable | Description | Local Default | UAT/Prod |
|----------|-------------|---------------|----------|
| `DB_NAME` | Database name | (empty = use SQLite) | `support_calendar` |
| `DB_USER` | Database user | - | `calendar_user` |
| `DB_PASSWORD` | Database password | - | Your secure password |
| `DB_HOST` | Database host | - | `localhost` |
| `DB_PORT` | Database port | - | `5432` |

**Note:** If `DB_NAME` is not set, the application automatically uses SQLite for local development.

### Static Files

| Variable | Description | Default |
|----------|-------------|---------|
| `STATIC_URL` | URL prefix for static files | `/django-static/` |

### CORS Settings

| Variable | Description | Local Default | UAT/Prod |
|----------|-------------|---------------|----------|
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed origins | `http://localhost:3000,http://127.0.0.1:3000` | Your server URLs |

## Deployment Workflow

### Pushing Changes to UAT

1. **Make changes locally** and test with SQLite
2. **Commit and push** to your repository
3. **On UAT server, pull changes:**
   ```bash
   cd /var/www/support_calendar
   git pull origin main
   ```

4. **Install any new dependencies:**
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Run migrations if needed:**
   ```bash
   python manage.py migrate
   ```

6. **Collect static files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

7. **Restart services:**
   ```bash
   sudo systemctl restart calendar-backend
   ```

**Important:** You don't need to modify settings.py! The .env file on UAT already has the correct configuration.

## Troubleshooting

### "Import dotenv could not be resolved"
This is just a linting warning. Make sure `python-dotenv` is installed:
```bash
pip install python-dotenv
```

### Database connection errors on UAT
Check your .env file has correct database credentials:
```bash
cat backend/.env | grep DB_
```

### CORS errors
Verify CORS_ALLOWED_ORIGINS in .env includes your frontend URL:
```bash
cat backend/.env | grep CORS
```

### Static files not loading
1. Check STATIC_URL in .env matches Nginx configuration
2. Run `python manage.py collectstatic --noinput`
3. Verify Nginx is serving from the correct directory

## Security Best Practices

1. **Never commit .env files** - They're in .gitignore for a reason
2. **Use strong SECRET_KEY** - Generate a new one for each environment
3. **Set DEBUG=False** in production - Prevents information leakage
4. **Use strong database passwords** - Especially in production
5. **Limit ALLOWED_HOSTS** - Only include your actual domains/IPs
6. **Keep .env file permissions restricted:**
   ```bash
   chmod 600 backend/.env
   ```

## Quick Reference

### Switch to SQLite (local dev)
```bash
# In backend/.env, remove or comment out DB_NAME:
# DB_NAME=
```

### Switch to PostgreSQL (UAT/prod)
```bash
# In backend/.env, set DB_NAME and other DB variables:
DB_NAME=support_calendar
DB_USER=calendar_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### Check current configuration
```bash
cd backend
python manage.py shell
>>> from django.conf import settings
>>> print(f"DEBUG: {settings.DEBUG}")
>>> print(f"Database: {settings.DATABASES['default']['ENGINE']}")
>>> print(f"Allowed Hosts: {settings.ALLOWED_HOSTS}")