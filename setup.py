#!/usr/bin/env python3
"""
Setup script for Credit Scorecard Microservice.
Handles installation, database setup, and initial configuration.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    return run_command("pip install -r requirements.txt", "Dependencies installation")


def setup_environment():
    """Setup environment configuration."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("🔧 Setting up environment configuration...")
        try:
            with open(env_example, 'r') as src:
                content = src.read()
            
            with open(env_file, 'w') as dst:
                dst.write(content)
            
            print("✅ Environment file created from .env.example")
            print("⚠️  Please edit .env with your actual configuration")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("ℹ️  Environment file already exists or .env.example not found")
        return True


def setup_database():
    """Setup database tables."""
    print("🗄️  Setting up database...")
    
    # Check if we can import the app
    try:
        sys.path.insert(0, os.getcwd())
        from app.database import create_tables
        create_tables()
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("💡 Make sure PostgreSQL is running and connection details are correct in .env")
        return False


def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    return run_command("python -m pytest tests/ -v", "Test execution")


def start_service():
    """Start the service."""
    print("🚀 Starting Credit Scorecard Microservice...")
    print("📍 Service will be available at: http://localhost:8000")
    print("📖 API documentation: http://localhost:8000/docs")
    print("🛠️  To stop the service, press Ctrl+C")
    
    try:
        subprocess.run([
            "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Service stopped")


def docker_setup():
    """Setup using Docker Compose."""
    print("🐳 Setting up with Docker Compose...")
    
    # Check if docker-compose.yml exists
    if not Path("docker-compose.yml").exists():
        print("❌ docker-compose.yml not found")
        return False
    
    # Start services
    result = run_command("docker-compose up -d", "Docker Compose startup")
    if result is not None:
        print("✅ Services started with Docker Compose")
        print("📍 Service available at: http://localhost:8000")
        print("🗄️  PostgreSQL available at: localhost:5432")
        print("🔧 To view logs: docker-compose logs -f")
        print("🛑 To stop: docker-compose down")
        return True
    
    return False


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Credit Scorecard Microservice Setup")
    parser.add_argument("--mode", choices=["local", "docker"], default="local",
                       help="Setup mode: local or docker (default: local)")
    parser.add_argument("--skip-tests", action="store_true",
                       help="Skip running tests during setup")
    parser.add_argument("--no-start", action="store_true",
                       help="Don't start the service after setup")
    
    args = parser.parse_args()
    
    print("🧠 Credit Scorecard Microservice Setup")
    print("=" * 50)
    
    if args.mode == "docker":
        # Docker setup
        success = docker_setup()
        if not success:
            print("❌ Docker setup failed")
            sys.exit(1)
    else:
        # Local setup
        print("🔧 Setting up for local development...")
        
        # Install dependencies
        if not install_dependencies():
            print("❌ Setup failed at dependency installation")
            sys.exit(1)
        
        # Setup environment
        if not setup_environment():
            print("❌ Setup failed at environment configuration")
            sys.exit(1)
        
        # Setup database
        if not setup_database():
            print("❌ Setup failed at database setup")
            print("💡 You may need to:")
            print("   1. Start PostgreSQL")
            print("   2. Update DATABASE_URL in .env")
            print("   3. Run setup again")
            sys.exit(1)
        
        # Run tests (optional)
        if not args.skip_tests:
            test_result = run_tests()
            if not test_result:
                print("⚠️  Some tests failed, but continuing...")
        
        print("\n✅ Setup completed successfully!")
        
        # Start service (optional)
        if not args.no_start:
            print("\n" + "=" * 50)
            start_service()
        else:
            print("\n💡 To start the service manually:")
            print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")


if __name__ == "__main__":
    main()