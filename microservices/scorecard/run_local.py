#!/usr/bin/env python3
"""
Local development runner for the Scorecard Microservice
Run without Docker for development and testing
"""

import os
import sys
import uvicorn

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Set environment variables for local development
os.environ.setdefault('SCORECARD_API_KEY', 'default_scorecard_key_2024')
os.environ.setdefault('ENVIRONMENT', 'development')

if __name__ == "__main__":
    print("🚀 Starting Scorecard Microservice (Local Development)")
    print("=" * 50)
    print(f"API Key: {os.environ['SCORECARD_API_KEY'][:10]}...")
    print(f"Environment: {os.environ['ENVIRONMENT']}")
    print("=" * 50)
    print()
    print("📊 Service will be available at:")
    print("   Health Check: http://localhost:8001/health")
    print("   API Docs: http://localhost:8001/docs")
    print("   Scoring Endpoint: http://localhost:8001/api/v1/score")
    print()
    print("Press Ctrl+C to stop the service")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting service: {e}")
        sys.exit(1)