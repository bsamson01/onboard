#!/bin/bash

echo "🏦 Setting up Microfinance Onboarding System"
echo "============================================="

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

echo "✅ Node.js check passed"

# Setup backend
echo ""
echo "🔧 Setting up Backend..."
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=sqlite:///./microfinance.db
ASYNC_DATABASE_URL=sqlite+aiosqlite:///./microfinance.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security Configuration
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# Application Configuration
DEBUG=true
API_V1_STR=/api/v1
PROJECT_NAME=Microfinance Platform
VERSION=1.0.0
DESCRIPTION=Modular Microfinance Onboarding & Loan Management Platform

# File Upload Configuration
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads
ALLOWED_EXTENSIONS=["pdf", "jpg", "jpeg", "png", "doc", "docx"]

# OCR Configuration
TESSERACT_CMD=/usr/bin/tesseract
OCR_LANGUAGES=eng

# External Services
SCORECARD_API_URL=http://localhost:8001
SCORECARD_API_KEY=demo-api-key

# Email Configuration (optional)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=noreply@microfinance.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=Microfinance Platform

# SMS Configuration (optional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Logging Configuration
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
EOF
    echo "✅ Created .env file with default configuration"
fi

# Create upload directory
mkdir -p uploads

# Initialize database (if using Alembic)
if [ -f alembic.ini ]; then
    echo "🗄️ Initializing database..."
    alembic upgrade head
fi

echo "✅ Backend setup complete"

# Setup frontend
echo ""
echo "🎨 Setting up Frontend..."
cd ../frontend

# Install dependencies
npm install

echo "✅ Frontend setup complete"

# Back to root
cd ..

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "To start the application:"
echo ""
echo "1. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "2. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📚 Additional Setup Notes:"
echo ""
echo "- Install Tesseract OCR for document processing:"
echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
echo "  macOS: brew install tesseract"
echo ""
echo "- For production, update the SECRET_KEY in backend/.env"
echo "- Configure external scorecard API endpoint"
echo "- Set up PostgreSQL for production database"
echo "- Configure email/SMS providers for notifications"
echo ""
echo "🔐 Default Test User (create via API):"
echo "   Email: admin@microfinance.com"
echo "   Role: admin"
echo ""
echo "Happy coding! 🚀"