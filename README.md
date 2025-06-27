# 🏦 Microfinance Customer Onboarding System

A comprehensive customer onboarding platform for microfinance institutions featuring OCR document processing, real-time credit scoring, and complete audit trails.

## ✨ Features

- **5-Step Onboarding Wizard** with progress tracking
- **OCR Document Processing** with auto-fill capabilities  
- **Real-time Credit Scoring** via external API
- **Secure File Upload** with validation and virus scanning
- **Immutable Audit Trails** for complete transparency
- **Role-based Access Control** (Admin, Loan Officer, Customer)
- **Responsive Design** optimized for mobile and desktop

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Tesseract OCR (for document processing)

### Automated Setup
```bash
# Clone and setup everything
./setup.sh

# Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Start frontend (new terminal)
cd frontend
npm run dev
```

### Manual Setup

#### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📍 Access Points

- **Frontend**: http://localhost:4000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Frontend**: Vue.js 3, Pinia, Tailwind CSS, Vite
- **OCR**: Tesseract with custom extraction patterns
- **Authentication**: JWT with role-based access control
- **File Storage**: Local filesystem with S3-ready structure

### Project Structure
```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Authentication & utilities
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   └── alembic/            # Database migrations
├── frontend/               # Vue.js frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── views/          # Page components
│   │   ├── stores/         # Pinia state management
│   │   └── services/       # API integration
└── docs/                   # Additional documentation
```

## 🔧 Configuration

### Environment Variables
Key settings in `backend/.env`:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/microfinance

# Security  
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
SCORECARD_API_URL=http://localhost:8001
SCORECARD_API_KEY=your-api-key

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./uploads

# OCR
TESSERACT_CMD=/usr/bin/tesseract
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## 📝 API Usage

### Create Onboarding Application
```bash
curl -X POST http://localhost:8000/api/v1/onboarding/applications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### Complete Step
```bash
curl -X POST http://localhost:8000/api/v1/onboarding/applications/{app_id}/steps/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "step_number": 1,
    "step_data": {
      "first_name": "John",
      "last_name": "Doe",
      "date_of_birth": "1990-01-15"
    }
  }'
```

### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/onboarding/applications/{app_id}/documents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.jpg" \
  -F "document_type=national_id"
```

## 🛡️ Security Features

- **JWT Authentication** with refresh tokens
- **Role-based permissions** for different user types
- **Rate limiting** to prevent abuse
- **Input validation** on all endpoints
- **File type validation** and virus scanning
- **Audit logging** of all user actions
- **Data encryption** for sensitive information

## 🎯 Onboarding Flow

1. **Personal Information**: Name, DOB, ID number, demographics
2. **Contact Information**: Address, phone, emergency contacts
3. **Financial Profile**: Employment, income, banking details
4. **Document Upload**: ID documents with OCR processing
5. **Consent & Scoring**: Consent collection and credit assessment

## 🎯 External Integrations

### OCR Processing
- Tesseract OCR engine for text extraction
- Support for National ID and Passport documents
- Auto-fill form fields from extracted data
- Confidence scoring for quality assessment

### Credit Scoring
- External scorecard API integration
- Real-time credit assessment
- Grade mapping (AA to D scale)
- Personalized recommendations

### File Storage
- Local filesystem with organized structure
- S3-compatible for cloud deployment
- File integrity verification
- Secure access controls

## 📈 Monitoring & Analytics

- **Application Progress**: Track conversion rates
- **OCR Performance**: Document processing success rates
- **User Behavior**: Step completion analytics
- **System Health**: Performance and error monitoring
- **Audit Reports**: Complete activity trails

## 🚀 Production Deployment

### Docker
```bash
# Backend
docker build -t microfinance-backend backend/
docker run -p 8000:8000 microfinance-backend

# Frontend
docker build -t microfinance-frontend frontend/
docker run -p 4000:4000 microfinance-frontend
```

### Environment Setup
1. Set up PostgreSQL database
2. Configure Redis for caching
3. Install Tesseract OCR
4. Set up external scorecard API
5. Configure email/SMS providers
6. Set up SSL certificates
7. Configure monitoring tools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: See `ONBOARDING_SYSTEM_SUMMARY.md` for detailed documentation
- **API Docs**: Available at `/docs` when running the backend
- **Issues**: Create GitHub issues for bugs and feature requests

## Default Test Users

The following test users are automatically created for development and testing:

| Role         | Email                     | Username      | Password            |
|--------------|---------------------------|--------------|---------------------|
| Customer     | test@example.com          | testuser     | testpassword123     |
| Admin        | admin@example.com         | admin        | adminpassword123    |
| Loan Officer | loan_officer@example.com  | loan_officer | officerpassword123  |

You can use these credentials to log in and test different user roles in the application.

---

Built with ❤️ for financial inclusion and accessibility. 