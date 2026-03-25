# Calendar App - Quick Reference Guide

## Deployment Overview

This Calendar Application consists of:
- **Backend**: Django REST API with PostgreSQL database
- **Frontend**: React single-page application
- **Web Server**: Nginx (reverse proxy)
- **App Server**: Gunicorn (WSGI server)

## Prerequisites

- Ubuntu 24.04 VM
- Sudo access
- Domain name or public IP address
- At least 2GB RAM, 20GB disk space

## Quick Deployment Steps

### Option 1: Automated Deployment (Recommended)

1. Copy application files to VM
2. Run the deployment script:
   ```bash
   cd /path/to/calendar_app
   chmod +x deploy.sh
   sudo ./deploy.sh
   ```
3. Follow the prompts
4. Access application at `http://your-domain`

### Option 2: Manual Deployment

Follow the detailed steps in [`DEPLOYMENT.md`](./DEPLOYMENT.md)

## Essential Commands

### Service Management

```bash
# Check service status
sudo systemctl status calendar_app
sudo systemctl status nginx
sudo systemctl status postgresql

# Start services
sudo systemctl start calendar_app
sudo systemctl start nginx

# Stop services
sudo systemctl stop calendar_app
sudo systemctl stop nginx

# Restart services
sudo systemctl restart calendar_app
sudo systemctl restart nginx

# Enable services on boot
sudo systemctl enable calendar_app
sudo systemctl enable nginx
```

### View Logs

```bash
# Application logs (real-time)
sudo journalctl -u calendar_app -f

# Application error logs
sudo tail -f /var/log/calendar_app/error.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

### Database Operations

```bash
# Access PostgreSQL
sudo -u postgres psql

# Connect to calendar database
sudo -u postgres psql -d calendar_db

# Backup database
sudo -u postgres pg_dump calendar_db > backup_$(date +%Y%m%d).sql

# Restore database
sudo -u postgres psql calendar_db < backup_YYYYMMDD.sql

# Run migrations
cd /var/www/calendar_app/backend
source venv/bin/activate
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Application Updates

```bash
# Quick update (if using update script)
cd /var/www/calendar_app
sudo ./update.sh

# Manual update
cd /var/www/calendar_app/backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

cd /var/www/calendar_app/frontend
npm install
npm run build

sudo systemctl restart calendar_app
sudo systemctl restart nginx
```

### Troubleshooting

```bash
# Check if services are running
ps aux | grep gunicorn
ps aux | grep nginx

# Check listening ports
sudo netstat -tlnp | grep :8000  # Gunicorn
sudo netstat -tlnp | grep :80    # Nginx

# Test Nginx configuration
sudo nginx -t

# Check disk space
df -h

# Check memory usage
free -h

# Check system resources
htop

# Verify database connection
cd /var/www/calendar_app/backend
source venv/bin/activate
python manage.py dbshell
```

## Common Issues and Solutions

### Issue: Application not accessible

**Check:**
1. Services running: `sudo systemctl status calendar_app nginx`
2. Firewall: `sudo ufw status`
3. Nginx config: `sudo nginx -t`
4. Logs: `sudo journalctl -u calendar_app -n 50`

**Solution:**
```bash
sudo systemctl restart calendar_app
sudo systemctl restart nginx
```

### Issue: Database connection error

**Check:**
1. PostgreSQL running: `sudo systemctl status postgresql`
2. Database exists: `sudo -u postgres psql -l`
3. Credentials in `.env` file

**Solution:**
```bash
sudo systemctl restart postgresql
# Verify .env file has correct DB credentials
```

### Issue: Static files not loading

**Solution:**
```bash
cd /var/www/calendar_app/backend
source venv/bin/activate
python manage.py collectstatic --noinput
sudo chown -R www-data:www-data /var/www/calendar_app
sudo systemctl restart calendar_app
```

### Issue: CORS errors

**Solution:**
Update `backend/.env`:
```env
CORS_ALLOWED_ORIGINS=http://your-domain.com,https://your-domain.com
```

Then restart:
```bash
sudo systemctl restart calendar_app
```

### Issue: Frontend not updating

**Solution:**
```bash
cd /var/www/calendar_app/frontend
npm run build
sudo systemctl restart nginx
# Clear browser cache
```

## File Locations

```
/var/www/calendar_app/          # Application root
├── backend/                     # Django backend
│   ├── venv/                   # Python virtual environment
│   ├── .env                    # Environment variables
│   ├── manage.py               # Django management
│   └── staticfiles/            # Collected static files
├── frontend/                    # React frontend
│   ├── build/                  # Production build
│   └── .env                    # Frontend environment
└── logs/                        # Application logs

/etc/nginx/sites-available/calendar_app    # Nginx config
/etc/systemd/system/calendar_app.service   # Systemd service
/var/log/calendar_app/                     # Application logs
```

## Security Checklist

- [ ] Change default SECRET_KEY in `.env`
- [ ] Use strong database password
- [ ] Set DEBUG=False in production
- [ ] Configure firewall (UFW)
- [ ] Install SSL certificate (Let's Encrypt)
- [ ] Regular backups scheduled
- [ ] Keep system packages updated
- [ ] Restrict SSH access
- [ ] Use strong passwords for all accounts
- [ ] Monitor logs regularly

## Performance Optimization

### Gunicorn Workers

Adjust workers in `/etc/systemd/system/calendar_app.service`:
```ini
--workers 3  # Formula: (2 x CPU cores) + 1
```

### Database Connection Pooling

Add to `backend/calendar_project/settings.py`:
```python
DATABASES = {
    'default': {
        # ... existing config ...
        'CONN_MAX_AGE': 600,  # 10 minutes
    }
}
```

### Nginx Caching

Already configured in nginx config for static assets.

## Backup Strategy

### Automated Daily Backups

Create cron job:
```bash
sudo crontab -e
```

Add:
```cron
# Daily backup at 2 AM
0 2 * * * /var/www/calendar_app/backup.sh
```

### Manual Backup

```bash
cd /var/www/calendar_app
sudo ./backup.sh
```

Backups stored in: `/var/backups/calendar_app/`

## Monitoring

### Check Application Health

```bash
# HTTP status
curl -I http://your-domain.com

# API health
curl http://your-domain.com/api/

# Check response time
time curl http://your-domain.com
```

### Resource Monitoring

```bash
# CPU and Memory
htop

# Disk usage
df -h

# Network connections
sudo netstat -an | grep :80
```

## SSL/HTTPS Setup

### Using Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

## Initial Setup After Deployment

1. **Access Application**: `http://your-domain.com`

2. **Login as Superuser**: Use credentials created during deployment

3. **Create Teams**:
   - Go to Admin Panel
   - Click "Teams" → "Add Team"
   - Create teams (e.g., "US West", "US East", "Europe")

4. **Create Users**:
   - Go to Admin Panel → "Users"
   - Click "Add User"
   - Fill in details, assign role and team
   - Note the temporary password

5. **Test Features**:
   - Create time-off request
   - Generate on-call rotation
   - View calendar
   - Test dark mode
   - Update profile

## Support and Documentation

- **Full Deployment Guide**: [`DEPLOYMENT.md`](./DEPLOYMENT.md)
- **Deployment Scripts**: [`DEPLOYMENT_SCRIPTS.md`](./DEPLOYMENT_SCRIPTS.md)
- **Application Logs**: `/var/log/calendar_app/`
- **System Logs**: `sudo journalctl -u calendar_app`

## Contact

For issues or questions, contact the development team or refer to the application documentation.

---

**Made with Bob**