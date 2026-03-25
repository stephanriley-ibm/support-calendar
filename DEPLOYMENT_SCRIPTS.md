# Deployment Scripts and Configuration Files

This document contains the scripts and configuration files needed for deployment.

## Required Files to Create

### 1. Backend Requirements File

Create `backend/requirements.txt`:

```txt
Django==5.0.1
djangorestframework==3.14.0
django-cors-headers==4.3.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
gunicorn==21.2.0
```

### 2. Backend Environment File

Create `backend/.env`:

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

**Generate SECRET_KEY with:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Frontend Environment File

Create `frontend/.env`:

```env
REACT_APP_API_URL=http://your-domain.com/api
```

### 4. Update Django Settings

Update `backend/calendar_project/settings.py` to add at the top:

```python
import os
from dotenv import load_dotenv

load_dotenv()
```

And update these sections:

```python
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

# Add static files configuration
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
```

## Deployment Scripts

### Quick Deploy Script

Create `deploy.sh` in the project root:

```bash
#!/bin/bash

# Calendar App Deployment Script for Ubuntu 24.04

set -e  # Exit on error

echo "=== Calendar App Deployment Script ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/var/www/calendar_app"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_error "Please do not run as root. Run as your regular user with sudo access."
    exit 1
fi

# Step 1: Update system packages
echo ""
echo "Step 1: Updating system packages..."
sudo apt update
sudo apt upgrade -y
print_status "System packages updated"

# Step 2: Install required packages
echo ""
echo "Step 2: Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git curl
print_status "System packages installed"

# Step 3: Install Node.js
echo ""
echo "Step 3: Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    print_status "Node.js installed"
else
    print_status "Node.js already installed"
fi

# Step 4: Setup PostgreSQL
echo ""
echo "Step 4: Setting up PostgreSQL database..."
read -p "Enter database name [calendar_db]: " DB_NAME
DB_NAME=${DB_NAME:-calendar_db}

read -p "Enter database user [calendar_user]: " DB_USER
DB_USER=${DB_USER:-calendar_user}

read -sp "Enter database password: " DB_PASSWORD
echo ""

sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || print_warning "Database may already exist"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || print_warning "User may already exist"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
print_status "PostgreSQL database configured"

# Step 5: Create application directory
echo ""
echo "Step 5: Setting up application directory..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR
print_status "Application directory created"

# Step 6: Copy application files
echo ""
echo "Step 6: Copying application files..."
print_warning "Please ensure your application files are in the current directory"
read -p "Press Enter to continue..."

if [ -d "backend" ] && [ -d "frontend" ]; then
    cp -r backend frontend $APP_DIR/
    print_status "Application files copied"
else
    print_error "backend and frontend directories not found in current directory"
    exit 1
fi

# Step 7: Setup Python virtual environment
echo ""
echo "Step 7: Setting up Python virtual environment..."
cd $BACKEND_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary python-dotenv
print_status "Python environment configured"

# Step 8: Create .env file
echo ""
echo "Step 8: Creating environment configuration..."
read -p "Enter your domain or IP address: " DOMAIN

SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

cat > $BACKEND_DIR/.env << EOF
# Django Settings
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1

# Database Settings
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# CORS Settings
CORS_ALLOWED_ORIGINS=http://$DOMAIN,https://$DOMAIN
EOF

print_status "Environment file created"

# Step 9: Run migrations
echo ""
echo "Step 9: Running database migrations..."
python manage.py migrate
print_status "Database migrations completed"

# Step 10: Create superuser
echo ""
echo "Step 10: Creating superuser account..."
python manage.py createsuperuser
print_status "Superuser created"

# Step 11: Collect static files
echo ""
echo "Step 11: Collecting static files..."
python manage.py collectstatic --noinput
print_status "Static files collected"

# Step 12: Build frontend
echo ""
echo "Step 12: Building frontend..."
cd $FRONTEND_DIR

cat > .env << EOF
REACT_APP_API_URL=http://$DOMAIN/api
EOF

npm install
npm run build
print_status "Frontend built"

# Step 13: Configure Nginx
echo ""
echo "Step 13: Configuring Nginx..."
sudo tee /etc/nginx/sites-available/calendar_app > /dev/null << EOF
upstream django_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name $DOMAIN;
    
    client_max_body_size 10M;
    
    location / {
        root $FRONTEND_DIR/build;
        try_files \$uri \$uri/ /index.html;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    location /api/ {
        proxy_pass http://django_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
    
    location /admin/ {
        proxy_pass http://django_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias $BACKEND_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias $BACKEND_DIR/media/;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/calendar_app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
print_status "Nginx configured"

# Step 14: Create systemd service
echo ""
echo "Step 14: Creating systemd service..."
sudo tee /etc/systemd/system/calendar_app.service > /dev/null << EOF
[Unit]
Description=Calendar App Gunicorn Service
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn \\
    --workers 3 \\
    --bind 127.0.0.1:8000 \\
    --timeout 120 \\
    --access-logfile /var/log/calendar_app/access.log \\
    --error-logfile /var/log/calendar_app/error.log \\
    calendar_project.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

sudo mkdir -p /var/log/calendar_app
sudo chown www-data:www-data /var/log/calendar_app
print_status "Systemd service created"

# Step 15: Set permissions
echo ""
echo "Step 15: Setting file permissions..."
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR
print_status "Permissions set"

# Step 16: Start services
echo ""
echo "Step 16: Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable calendar_app
sudo systemctl start calendar_app
sudo systemctl restart nginx
print_status "Services started"

# Step 17: Configure firewall
echo ""
echo "Step 17: Configuring firewall..."
read -p "Configure UFW firewall? (y/n): " CONFIGURE_FW
if [ "$CONFIGURE_FW" = "y" ]; then
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    print_status "Firewall configured"
fi

# Final status check
echo ""
echo "=== Deployment Complete ==="
echo ""
print_status "Application deployed successfully!"
echo ""
echo "Access your application at: http://$DOMAIN"
echo ""
echo "Service status:"
sudo systemctl status calendar_app --no-pager -l
echo ""
echo "Next steps:"
echo "1. Access the application in your browser"
echo "2. Login with your superuser credentials"
echo "3. Create teams and users in the Admin Panel"
echo "4. (Optional) Set up SSL with: sudo certbot --nginx -d $DOMAIN"
echo ""
print_warning "Remember to keep your .env file secure and backed up!"
```

Make it executable:
```bash
chmod +x deploy.sh
```

### Update Script

Create `update.sh` for updating the application:

```bash
#!/bin/bash

# Calendar App Update Script

set -e

APP_DIR="/var/www/calendar_app"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

echo "=== Updating Calendar App ==="

# Pull latest changes (if using git)
cd $APP_DIR
if [ -d ".git" ]; then
    git pull
fi

# Update backend
echo "Updating backend..."
cd $BACKEND_DIR
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Update frontend
echo "Updating frontend..."
cd $FRONTEND_DIR
npm install
npm run build

# Restart services
echo "Restarting services..."
sudo systemctl restart calendar_app
sudo systemctl restart nginx

echo "Update complete!"
sudo systemctl status calendar_app --no-pager
```

Make it executable:
```bash
chmod +x update.sh
```

### Backup Script

Create `backup.sh`:

```bash
#!/bin/bash

# Calendar App Backup Script

BACKUP_DIR="/var/backups/calendar_app"
DATE=$(date +%Y%m%d_%H%M%S)

echo "=== Creating Backup ==="

# Create backup directory
sudo mkdir -p $BACKUP_DIR

# Backup database
echo "Backing up database..."
sudo -u postgres pg_dump calendar_db > $BACKUP_DIR/db_backup_$DATE.sql

# Backup application files
echo "Backing up application files..."
sudo tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /var/www/calendar_app

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup complete: $BACKUP_DIR"
ls -lh $BACKUP_DIR
```

Make it executable:
```bash
chmod +x backup.sh
```

## Quick Start Commands

### Deploy from scratch:
```bash
sudo ./deploy.sh
```

### Update application:
```bash
sudo ./update.sh
```

### Create backup:
```bash
sudo ./backup.sh
```

### Check service status:
```bash
sudo systemctl status calendar_app
sudo systemctl status nginx
sudo systemctl status postgresql
```

### View logs:
```bash
# Application logs
sudo journalctl -u calendar_app -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Application error logs
sudo tail -f /var/log/calendar_app/error.log
```

### Restart services:
```bash
sudo systemctl restart calendar_app
sudo systemctl restart nginx
```

## Post-Deployment Checklist

- [ ] Application accessible at http://your-domain
- [ ] Can login with superuser account
- [ ] Admin panel accessible at /admin
- [ ] Can create teams
- [ ] Can create users
- [ ] Can create time-off requests
- [ ] Can generate on-call rotations
- [ ] Calendar displays correctly
- [ ] Dark mode toggle works
- [ ] Profile page accessible
- [ ] Timezone settings work
- [ ] All API endpoints responding
- [ ] Static files loading correctly
- [ ] No console errors in browser
- [ ] Services start on boot
- [ ] Firewall configured
- [ ] Backups scheduled (optional)
- [ ] SSL certificate installed (optional)

---

**Made with Bob**