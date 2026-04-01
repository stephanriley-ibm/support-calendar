#!/usr/bin/env python
"""
Quick script to create a test admin user for local development
Run with: python create_test_user.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, Team

def create_test_data():
    """Create test admin user and team"""
    
    # Check if admin already exists
    if User.objects.filter(username='admin').exists():
        print("❌ Admin user already exists!")
        admin = User.objects.get(username='admin')
        print(f"   Username: admin")
        print(f"   Email: {admin.email}")
        print("\n💡 If you forgot the password, delete db.sqlite3 and run this script again")
        return
    
    # Create test team
    team, created = Team.objects.get_or_create(
        name='Test Team',
        defaults={'description': 'Test team for local development'}
    )
    
    if created:
        print("✅ Created test team: Test Team")
    else:
        print("ℹ️  Test team already exists")
    
    # Create admin user
    admin = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        role='admin',
        team=team
    )
    
    print("\n✅ Test admin user created successfully!")
    print("\n📋 Login Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   Email: admin@example.com")
    print("\n🚀 You can now log in at http://localhost:3000")
    
    # Create a test engineer
    engineer = User.objects.create_user(
        username='engineer',
        email='engineer@example.com',
        password='engineer123',
        first_name='Test',
        last_name='Engineer',
        role='engineer',
        team=team,
        oncall_eligible=True
    )
    
    print("\n✅ Test engineer user created!")
    print("   Username: engineer")
    print("   Password: engineer123")
    
    # Create a test coach
    coach = User.objects.create_user(
        username='coach',
        email='coach@example.com',
        password='coach123',
        first_name='Test',
        last_name='Coach',
        role='coach',
        team=team
    )
    
    # Set coach as team coach
    team.coach = coach
    team.save()
    
    print("\n✅ Test coach user created!")
    print("   Username: coach")
    print("   Password: coach123")

if __name__ == '__main__':
    print("🔧 Creating test users for local development...\n")
    create_test_data()
    print("\n✨ Done!")

# Made with Bob
