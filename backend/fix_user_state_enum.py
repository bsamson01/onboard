#!/usr/bin/env python3
"""
Script to fix user_state enum values in the database
"""
import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import update

async def fix_user_state_enum():
    """Update user_state values from lowercase to uppercase."""
    async with AsyncSessionLocal() as session:
        try:
            print("🔍 Fixing user_state enum values...")
            
            # Update all user_state values to uppercase
            stmt = update(User).where(User.user_state == "registered").values(user_state="REGISTERED")
            result = await session.execute(stmt)
            print(f"✅ Updated {result.rowcount} users from 'registered' to 'REGISTERED'")
            
            stmt = update(User).where(User.user_state == "onboarded").values(user_state="ONBOARDED")
            result = await session.execute(stmt)
            print(f"✅ Updated {result.rowcount} users from 'onboarded' to 'ONBOARDED'")
            
            stmt = update(User).where(User.user_state == "outdated").values(user_state="OUTDATED")
            result = await session.execute(stmt)
            print(f"✅ Updated {result.rowcount} users from 'outdated' to 'OUTDATED'")
            
            # Commit the changes
            await session.commit()
            print("✅ Database updated successfully!")
            
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(fix_user_state_enum()) 