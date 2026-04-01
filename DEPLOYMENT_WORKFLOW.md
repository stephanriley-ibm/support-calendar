# Deployment Workflow - Local to UAT

This guide provides a streamlined workflow for deploying changes from your local development environment to UAT.

## Prerequisites

- Local development environment set up with `.env` file
- UAT server accessible via SSH
- Git repository configured

## Quick Deployment Steps

### 1. Local Development & Testing

```bash
# Make your changes locally
cd calendar_app/backend

# Test with local SQLite database
python manage.py runserver

# Test frontend
cd ../frontend
npm start
```

### 2. Commit Changes

```bash
# From project root
git add .
git commit -m "Your commit message"
git push origin main
```

### 3. Deploy to UAT

```bash
# SSH to UAT server
ssh fyre.calendar  # or your configured host

# Navigate to project directory
cd /var/www/support_calendar

# Pull latest changes
git pull origin main

# Activate virtual environment
source backend/venv/bin/activate

# Install any new Python dependencies
cd backend
pip install -r requirements.txt

# Run database migrations (if any)
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Build frontend (if frontend changes)
cd ../frontend
npm install  # if package.json changed
npm run build

# Restart backend service
sudo systemctl restart calendar-backend

# Restart Nginx (if needed)
sudo systemctl restart nginx
```

## Automated Deployment Script

Create this script on your UAT server for faster deployments:

```bash
#!/bin/bash
# /var/www/support_calendar/deploy.sh

set -e  # Exit on error

echo "🚀 Starting deployment..."

# Navigate to project directory
cd /var/www/support_calendar

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Backend updates
echo "🐍 Updating backend..."
source backend/venv/bin/activate
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Frontend updates
echo "⚛️  Building frontend..."
cd ../frontend
npm install
npm run build

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart calendar-backend
sudo systemctl restart nginx

echo "✅ Deployment complete!"
```

Make it executable:
```bash
chmod +x /var/www/support_calendar/deploy.sh
```

Then deploy with:
```bash
ssh fyre.calendar
cd /var/www/support_calendar
./deploy.sh
```

## Environment Configuration

### Local (.env)
```bash
# backend/.env (local development)
SECRET_KEY=django-insecure-3h67&)@d#t=o4dqh6)-u0ckeky-05q^8mn_8_adk%*=nm_=!48
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
# DB_NAME is not set, so SQLite is used
STATIC_URL=/django-static/
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### UAT (.env)
```bash
# backend/.env (on UAT server)
SECRET_KEY=your-production-secret-key
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

## Key Points

### ✅ What Gets Deployed
- Code changes (Python, JavaScript, CSS)
- Database migrations
- New dependencies
- Static files
- Frontend build

### ❌ What Doesn't Get Deployed
- `.env` file (environment-specific, not in git)
- `db.sqlite3` (local database)
- `node_modules/` (installed on each server)
- `venv/` (virtual environment)
- `__pycache__/` (Python cache)

### 🔒 Settings.py
**You never need to modify settings.py for deployment!**
- Same settings.py works on both local and UAT
- Environment differences are handled by `.env` files
- Database automatically switches based on `DB_NAME` presence

## Common Scenarios

### Scenario 1: Code Changes Only
```bash
# On UAT
git pull
sudo systemctl restart calendar-backend
```

### Scenario 2: Database Model Changes
```bash
# On UAT
git pull
source backend/venv/bin/activate
cd backend
python manage.py migrate
sudo systemctl restart calendar-backend
```

### Scenario 3: Frontend Changes
```bash
# On UAT
git pull
cd frontend
npm run build
sudo systemctl restart nginx
```

### Scenario 4: New Dependencies
```bash
# On UAT
git pull
source backend/venv/bin/activate
cd backend
pip install -r requirements.txt
sudo systemctl restart calendar-backend
```

### Scenario 5: Full Deployment
```bash
# On UAT
./deploy.sh
```

## Troubleshooting

### Changes Not Appearing
1. Check git pull was successful
2. Verify service restart: `sudo systemctl status calendar-backend`
3. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
4. Clear browser cache (Ctrl+Shift+R)

### Database Errors
1. Check .env has correct database credentials
2. Verify PostgreSQL is running: `sudo systemctl status postgresql`
3. Check migrations: `python manage.py showmigrations`
4. Run migrations: `python manage.py migrate`

### Static Files Not Loading
1. Run collectstatic: `python manage.py collectstatic --noinput`
2. Check Nginx configuration
3. Verify STATIC_URL in .env matches Nginx config

### CORS Errors
1. Check CORS_ALLOWED_ORIGINS in .env includes frontend URL
2. Restart backend: `sudo systemctl restart calendar-backend`

## Rollback Procedure

If deployment causes issues:

```bash
# On UAT
cd /var/www/support_calendar

# Find the last working commit
git log --oneline -10

# Rollback to previous commit
git reset --hard <commit-hash>

# Restart services
sudo systemctl restart calendar-backend
sudo systemctl restart nginx
```

## Best Practices

1. **Test locally first** - Always test changes with local SQLite before deploying
2. **Small commits** - Deploy small, incremental changes
3. **Backup database** - Before major changes: `pg_dump support_calendar > backup.sql`
4. **Check logs** - Monitor logs after deployment
5. **Document changes** - Keep good commit messages
6. **Environment parity** - Keep .env files updated on both environments

## Quick Commands Reference

```bash
# Check service status
sudo systemctl status calendar-backend
sudo systemctl status nginx

# View logs
sudo journalctl -u calendar-backend -f
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo systemctl restart calendar-backend
sudo systemctl restart nginx

# Check Django configuration
cd /var/www/support_calendar/backend
source venv/bin/activate
python manage.py check

# Test database connection
python manage.py dbshell