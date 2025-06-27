#!/usr/bin/env python3
"""
Simple test script to verify login functionality
"""
import asyncio
import httpx
import json

async def test_login():
    """Test the login endpoint."""
    async with httpx.AsyncClient() as client:
        # Test data
        login_data = {
            "email": "brandon.samsonjnr@gmail.com",
            "password": "testpassword123"
        }
        
        try:
            # Test login
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login-json",
                json=login_data,
                timeout=10.0
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Login successful!")
                print(f"Access Token: {data.get('access_token', 'N/A')[:20]}...")
                print(f"User: {data.get('user', {}).get('email', 'N/A')}")
            else:
                print(f"❌ Login failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error during login test: {e}")

if __name__ == "__main__":
    asyncio.run(test_login()) 