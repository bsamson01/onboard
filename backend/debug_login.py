#!/usr/bin/env python3
"""
Debug script to test login functionality step by step
"""
import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.core.auth import authenticate_user, create_access_token
from app.models.user import User
from sqlalchemy import select
from datetime import timedelta
from app.config import settings

async def debug_login():
    """Debug the login process step by step."""
    async with AsyncSessionLocal() as session:
        try:
            print("🔍 Step 1: Testing database connection...")
            # Test basic database connection
            result = await session.execute(select(User).limit(1))
            users = result.scalars().all()
            print(f"✅ Database connection successful. Found {len(users)} users")
            
            print("\n🔍 Step 2: Testing user lookup...")
            # Test user lookup
            stmt = select(User).where(User.email == "brandon.samsonjnr@gmail.com")
            result = await session.execute(stmt)
            user = result.scalar()
            
            if user:
                print(f"✅ User found: {user.email} (ID: {user.id})")
                print(f"   - Role: {user.role}")
                print(f"   - Active: {user.is_active}")
                print(f"   - Locked: {user.is_locked}")
                print(f"   - User State: {user.user_state}")
                print(f"   - Last Login: {user.last_login}")
            else:
                print("❌ User not found")
                return
            
            print("\n🔍 Step 3: Testing password verification...")
            # Test password verification
            from app.core.auth import verify_password
            is_valid = verify_password("testpassword123", user.hashed_password)
            print(f"✅ Password verification: {'SUCCESS' if is_valid else 'FAILED'}")
            
            if not is_valid:
                print("❌ Password verification failed - this is the issue!")
                return
            
            print("\n🔍 Step 4: Testing authentication function...")
            # Test the authenticate_user function
            auth_user = await authenticate_user(session, "brandon.samsonjnr@gmail.com", "testpassword123")
            
            if auth_user:
                print("✅ Authentication successful")
                print(f"   - Failed attempts reset: {auth_user.failed_login_attempts}")
                print(f"   - Last login updated: {auth_user.last_login}")
            else:
                print("❌ Authentication failed")
                return
            
            print("\n🔍 Step 5: Testing token creation...")
            # Test token creation
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": auth_user.email, "user_id": str(auth_user.id)},
                expires_delta=access_token_expires
            )
            print(f"✅ Token created successfully: {access_token[:20]}...")
            
            print("\n🔍 Step 6: Testing user serialization...")
            # Test user serialization
            from app.schemas.auth import UserResponse
            try:
                user_response = UserResponse.model_validate(auth_user).model_dump()
                print("✅ User serialization successful")
                print(f"   - Serialized fields: {list(user_response.keys())}")
            except Exception as e:
                print(f"❌ User serialization failed: {e}")
                return
            
            print("\n🔍 Step 7: Testing database commit...")
            # Test database commit
            try:
                await session.commit()
                print("✅ Database commit successful")
            except Exception as e:
                print(f"❌ Database commit failed: {e}")
                await session.rollback()
                return
            
            print("\n🎉 All tests passed! Login should work now.")
            
        except Exception as e:
            print(f"❌ Error during debug: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(debug_login()) 