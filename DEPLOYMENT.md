# Calendar App Deployment Guide for Ubuntu 24.04

This guide will walk you through deploying the Calendar Application on an Ubuntu 24.04 VM for user testing.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [System Setup](#system-setup)
3. [Database Setup](#database-setup)
4. [Backend Setup](#backend-setup)
5. [Frontend Setup](#frontend-setup)
6. [Nginx Configuration](#nginx-configuration)
7. [SSL/HTTPS Setup (Optional)](#ssl-https-setup)
8. [Systemd Services](#systemd-services)
9. [Initial Admin Setup](#initial-admin-setup)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

- Ubuntu 24.04 VM with sudo access
- Domain name or IP address for accessing the application
- At least 2GB RAM and 20GB disk space

## System Setup

### 1. Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Required System Packages

```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git curl
```

### 3. Install Node.js and npm

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

Verify installations:
```bash
python3 --version  # Should be 3.12+
node --version     # Should be v20+
npm --version      # Should be 10+
psql --version     # Should be 16+
```

## Database Setup

### 1. Create PostgreSQL Database and User

```bash
sudo -u postgres psql
```

In the PostgreSQL prompt:
```sql
CREATE DATABASE calendar_db;
CREATE USER calendar_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE calendar_user SET client_encoding TO 'utf8';
ALTER ROLE calendar_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE calendar_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE calendar_db TO calendar_user;
\q
```

### 2. Configure PostgreSQL for Local Connections

Edit the pg_hba.conf file:
```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Ensure this line exists:
```
local   all             all                                     peer
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

## Backend Setup

### 1. Create Application Directory

```bash
sudo mkdir -p /var/www/calendar_app
sudo chown $USER:$USER /var/www/calendar_app
cd /var/www/calendar_app
```

### 2. Copy Application Files

Transfer your application files to the VM. You can use `scp`, `rsync`, or `git clone`:

```bash
# Option 1: Using git (if you have a repository)
git clone <your-repo-url> .

# Option 2: Using scp from your local machine
# scp -r /path/to/calendar_app user@vm-ip:/var/www/calendar_app
```

### 3. Set Up Python Virtual Environment

```bash
cd /var/www/calendar_app/backend
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 5. Create Environment File

```bash
nano /var/www/calendar_app/backend/.env
```

Add the following content (adjust values as needed):
```env
# Django Settings
SECRET_KEY=your-very-long-random-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-vm-ip,localhost

# Database Settings
DB_NAME=calendar_db
DB_USER=calendar_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432

# CORS Settings
CORS_ALLOWED_ORIGINS=http://your-domain.com,http://your-vm-ip
```

**Important**: Generate a secure SECRET_KEY:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Update Django Settings

Edit `backend/calendar_project/settings.py` to use environment variables:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
```

### 7. Run Database Migrations

```bash
cd /var/www/calendar_app/backend
source venv/bin/activate
python manage.py migrate
```

### 8. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 9. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## Frontend Setup

### 1. Install Frontend Dependencies

```bash
cd /var/www/calendar_app/frontend
npm install
```

### 2. Configure API Endpoint

Edit `frontend/src/services/api.js` to use your production API URL:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://your-vm-ip:8000/api';
```

Or create a `.env` file in the frontend directory:
```bash
nano /var/www/calendar_app/frontend/.env
```

Add:
```env
REACT_APP_API_URL=http://your-domain.com/api
```

### 3. Build Frontend for Production

```bash
npm run build
```

This creates an optimized production build in the `build` directory.

## Nginx Configuration

### 1. Create Nginx Configuration File

```bash
sudo nano /etc/nginx/sites-available/calendar_app
```

Add the following configuration:

```nginx
# Backend API Server
upstream django_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com your-vm-ip;
    
    client_max_body_size 10M;
    
    # Frontend - React Build
    location / {
        root /var/www/calendar_app/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Django Admin
    location /admin/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Django Static Files
    location /static/ {
        alias /var/www/calendar_app/backend/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Django Media Files
    location /media/ {
        alias /var/www/calendar_app/backend/media/;
    }
}
```

### 2. Enable the Site

```bash
sudo ln -s /etc/nginx/sites-available/calendar_app /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
```

### 3. Test Nginx Configuration

```bash
sudo nginx -t
```

### 4. Restart Nginx

```bash
sudo systemctl restart nginx
```

## SSL/HTTPS Setup (Optional but Recommended)

### Using Let's Encrypt (Free SSL)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Follow the prompts. Certbot will automatically configure SSL and set up auto-renewal.

## Systemd Services

### 1. Create Gunicorn Service

```bash
sudo nano /etc/systemd/system/calendar_app.service
```

Add:

```ini
[Unit]
Description=Calendar App Gunicorn Service
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/calendar_app/backend
Environment="PATH=/var/www/calendar_app/backend/venv/bin"
ExecStart=/var/www/calendar_app/backend/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/calendar_app/access.log \
    --error-logfile /var/log/calendar_app/error.log \
    calendar_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 2. Create Log Directory

```bash
sudo mkdir -p /var/log/calendar_app
sudo chown www-data:www-data /var/log/calendar_app
```

### 3. Set Proper Permissions

```bash
sudo chown -R www-data:www-data /var/www/calendar_app
sudo chmod -R 755 /var/www/calendar_app
```

### 4. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable calendar_app
sudo systemctl start calendar_app
```

### 5. Check Service Status

```bash
sudo systemctl status calendar_app
```

## Initial Admin Setup

### 1. Access the Application

Open your browser and navigate to:
- `http://your-domain.com` or `http://your-vm-ip`

### 2. Login with Superuser

Use the superuser credentials you created earlier.

### 3. Create Teams

1. Go to Admin Panel
2. Create teams (e.g., "US West", "US East", "Europe")
3. Assign coaches to teams

### 4. Create Users

1. Go to Admin Panel → Users
2. Create users with appropriate roles (Engineer, Coach, Admin)
3. Assign users to teams
4. Note the temporary passwords generated

### 5. Test Core Features

- Login as different users
- Create time-off requests
- Generate on-call rotations
- Test calendar views
- Verify timezone handling

## Troubleshooting

### Check Service Logs

```bash
# Gunicorn logs
sudo journalctl -u calendar_app -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Application logs
sudo tail -f /var/log/calendar_app/error.log
```

### Common Issues

#### 1. Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d calendar_db -U calendar_user
```

#### 2. Static Files Not Loading

```bash
# Re-collect static files
cd /var/www/calendar_app/backend
source venv/bin/activate
python manage.py collectstatic --noinput

# Check permissions
sudo chown -R www-data:www-data /var/www/calendar_app/backend/staticfiles
```

#### 3. Frontend Not Loading

```bash
# Rebuild frontend
cd /var/www/calendar_app/frontend
npm run build

# Check Nginx configuration
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. CORS Errors

Update `.env` file with correct origins:
```env
CORS_ALLOWED_ORIGINS=http://your-domain.com,http://your-vm-ip
```

Restart the service:
```bash
sudo systemctl restart calendar_app
```

### Restart All Services

```bash
sudo systemctl restart postgresql
sudo systemctl restart calendar_app
sudo systemctl restart nginx
```

## Maintenance

### Update Application

```bash
cd /var/www/calendar_app

# Pull latest changes (if using git)
git pull

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Update frontend
cd ../frontend
npm install
npm run build

# Restart services
sudo systemctl restart calendar_app
sudo systemctl restart nginx
```

### Backup Database

```bash
# Create backup
sudo -u postgres pg_dump calendar_db > calendar_db_backup_$(date +%Y%m%d).sql

# Restore backup
sudo -u postgres psql calendar_db < calendar_db_backup_YYYYMMDD.sql
```

### Monitor Resources

```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
htop
```

## Security Recommendations

1. **Firewall**: Configure UFW to only allow necessary ports
   ```bash
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

2. **Regular Updates**: Keep system packages updated
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Strong Passwords**: Use strong passwords for database and admin accounts

4. **SSL Certificate**: Always use HTTPS in production

5. **Backup Strategy**: Implement regular automated backups

6. **Monitoring**: Set up monitoring for application health and performance

## Support

For issues or questions, refer to the application documentation or contact the development team.

---

**Made with Bob**