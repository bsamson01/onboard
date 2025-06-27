#!/usr/bin/env python3
"""
Script to create a test user for development purposes.
Run this script to create a test user that can be used for login testing.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.database import get_async_db
from app.core.auth import create_user
from app.schemas.auth import UserCreate
from app.models.user import UserRole
from app.config import settings


async def create_test_user():
    """Create test users for development."""
    
    # Create database engine using the async URL
    engine = create_async_engine(settings.ASYNC_DATABASE_URL)
    
    # Test users data
    test_users = [
        {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "role": UserRole.CUSTOMER
        },
        {
            "email": "admin@example.com",
            "username": "admin",
            "password": "adminpassword123",
            "first_name": "Admin",
            "last_name": "User",
            "role": UserRole.ADMIN
        },
        {
            "email": "loan_officer@example.com",
            "username": "loan_officer",
            "password": "officerpassword123",
            "first_name": "Loan",
            "last_name": "Officer",
            "role": UserRole.LOAN_OFFICER
        }
    ]
    
    try:
        async with AsyncSession(engine) as session:
            for user_data in test_users:
                try:
                    test_user_data = UserCreate(**user_data)
                    user = await create_user(session, test_user_data)
                    print(f"✅ {user.role.value.title()} user created successfully!")
                    print(f"   Email: {user.email}")
                    print(f"   Username: {user.username}")
                    print(f"   Password: {user_data['password']}")
                    print(f"   Role: {user.role.value}")
                    print(f"   ID: {user.id}")
                    print()
                except Exception as e:
                    if "already registered" in str(e):
                        print(f"⚠️  {user_data['role'].value.title()} user already exists:")
                        print(f"   Email: {user_data['email']}")
                        print(f"   Password: {user_data['password']}")
                        print()
                    else:
                        print(f"❌ Error creating {user_data['role'].value} user: {e}")
                        print()
            
            print("You can now use these credentials to test the login functionality.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    await engine.dispose()


if __name__ == "__main__":
    print("Creating test users for development...")
    asyncio.run(create_test_user()) 