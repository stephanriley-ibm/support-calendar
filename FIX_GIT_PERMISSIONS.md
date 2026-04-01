# Fixing Git Permission Issues on UAT

## Problem
Getting permission errors when trying to `git pull` because the repository files are owned by a different user than the one you're logged in as.

## Quick Fix (Recommended)

Run these commands on your UAT server to fix permissions:

```bash
# Navigate to project directory
cd /var/www/support_calendar

# Change ownership to your user (replace 'your-username' with your actual username)
sudo chown -R your-username:www-data .

# Set proper directory permissions (755 = rwxr-xr-x)
sudo find . -type d -exec chmod 755 {} \;

# Set proper file permissions (644 = rw-r--r--)
sudo find . -type f -exec chmod 644 {} \;

# Protect .env file (600 = rw-------)
sudo chmod 600 backend/.env

# Make manage.py executable
sudo chmod +x backend/manage.py

# Configure git to trust this directory
git config --global --add safe.directory $(pwd)

# Now you can pull
git pull origin main
```

## Understanding the Solution

### Ownership
- **your-username**: You own the files (can git pull, edit, deploy)
- **www-data group**: Web server can read files (serve the application)

### Permissions
- **755 for directories**: Owner can read/write/execute, others can read/execute
- **644 for files**: Owner can read/write, others can only read
- **600 for .env**: Only owner can read/write (security - contains passwords)

## If You Still Get Errors

### Error: "fatal: detected dubious ownership"
```bash
git config --global --add safe.directory /var/www/support_calendar
```

### Error: "Permission denied" when pulling
```bash
# Check who owns the files
ls -la /var/www/support_calendar

# Fix ownership (replace 'your-username')
sudo chown -R your-username:www-data /var/www/support_calendar
```

### Error: Web server can't access files
```bash
# Ensure www-data group has read access
sudo chmod -R g+r /var/www/support_calendar
```

## Automated Deployment Script

Create this script to handle permissions automatically during deployment:

```bash
#!/bin/bash
# /var/www/support_calendar/deploy.sh

set -e

echo "🚀 Starting deployment..."

cd /var/www/support_calendar

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Fix permissions after pull
echo "🔒 Setting permissions..."
sudo chown -R $(whoami):www-data .
sudo find . -type d -exec chmod 755 {} \;
sudo find . -type f -exec chmod 644 {} \;
sudo chmod 600 backend/.env
sudo chmod +x backend/manage.py

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
./deploy.sh
```

## Why This Happens

When you initially deployed as one user (or root), that user became the owner of all files. Git tracks file ownership and won't let other users modify the repository without proper permissions.

## Best Practice for Future

Always deploy as the same user, or use the deployment script above which automatically fixes permissions after each pull.