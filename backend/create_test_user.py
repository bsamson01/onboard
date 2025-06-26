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
    """Create a test user for development."""
    
    # Create database engine using the async URL
    engine = create_async_engine(settings.ASYNC_DATABASE_URL)
    
    # Create test user data
    test_user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpassword123",
        first_name="Test",
        last_name="User",
        role=UserRole.CUSTOMER
    )
    
    try:
        # Create user
        async with AsyncSession(engine) as session:
            user = await create_user(session, test_user_data)
            print(f"✅ Test user created successfully!")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Password: {test_user_data.password}")
            print(f"   Role: {user.role.value}")
            print(f"   ID: {user.id}")
            print("\nYou can now use these credentials to test the login functionality.")
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        if "already registered" in str(e):
            print("   The test user already exists. You can use the existing credentials:")
            print("   Email: test@example.com")
            print("   Password: testpassword123")
    
    await engine.dispose()


if __name__ == "__main__":
    print("Creating test user for development...")
    asyncio.run(create_test_user()) 