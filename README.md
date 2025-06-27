# 🏦 Microfinance Customer Onboarding & Loan Management Platform

A comprehensive, production-ready microfinance platform featuring advanced customer onboarding with OCR document processing, real-time credit scoring, loan application management, and complete audit trails. Built with modern microservices architecture and enterprise-grade security.

## ✨ Key Features

### 🎯 Customer Onboarding
- **5-Step Onboarding Wizard** with progress tracking and validation
- **OCR Document Processing** with Tesseract for automated ID document extraction
- **Real-time Credit Scoring** via external scorecard API integration
- **Secure File Upload** with validation, virus scanning, and integrity checks
- **Consent Management** with cryptographic fingerprinting
- **Mobile-Responsive Design** optimized for all devices

### 💰 Loan Management
- **Complete Loan Application Lifecycle** from submission to disbursement
- **Status Tracking System** with role-based transitions
- **Application Review Dashboard** for loan officers and risk officers
- **One Active Application Rule** per customer enforcement
- **Audit Trail** for all application changes and decisions

### 🛡️ Security & Compliance
- **JWT Authentication** with role-based access control (RBAC)
- **Immutable Audit Logging** for complete transparency
- **Rate Limiting** and anti-spam protection
- **Data Encryption** for sensitive information
- **File Integrity Verification** with SHA-256 hashing
- **Input Validation** and sanitization on all endpoints

### 📊 Admin & Staff Features
- **Admin Dashboard** with comprehensive analytics
- **Application Review Panel** with filtering and search
- **User Management** with role assignment
- **System Health Monitoring** with Prometheus/Grafana
- **Audit Logs Panel** for compliance tracking
- **External Services Configuration** management

## 🚀 Quick Start

### Prerequisites
- **Docker 20.10+** and **Docker Compose 2.0+**
- **Python 3.11+** (for local development)
- **Node.js 18+** (for local development)
- **Tesseract OCR** (for document processing)

### One-Command Deployment
```bash
# Clone and deploy everything
git clone <repository-url>
cd onboard
./deploy.sh
```

### Manual Setup

#### Using Docker (Recommended)
```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create test user
docker-compose exec backend python create_test_user.py
```

#### Local Development
```bash
# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

## 📍 Access Points

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc
- **Grafana Dashboard**: http://localhost:3001 (admin/admin123)
- **Prometheus Metrics**: http://localhost:9090
- **pgAdmin**: http://localhost:5050 (admin@microfinance.com/admin123)

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery
- **Frontend**: Vue.js 3, Pinia, Tailwind CSS, Vite
- **Database**: PostgreSQL with Alembic migrations
- **Cache & Queue**: Redis with Celery workers
- **OCR**: Tesseract with custom extraction patterns
- **Monitoring**: Prometheus, Grafana
- **Authentication**: JWT with role-based access control
- **File Storage**: Local filesystem with S3-ready structure

### Microservices Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │ Scorecard API   │
│   (Vue.js)      │◄──►│   (FastAPI)     │◄──►│   (External)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │   Celery        │
│   (Database)    │    │   (Cache/Queue) │    │   (Workers)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Project Structure
```
onboard/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/endpoints/  # API endpoints
│   │   │   ├── auth.py        # Authentication
│   │   │   ├── onboarding.py  # Onboarding wizard
│   │   │   ├── loans.py       # Loan management
│   │   │   ├── status.py      # Application status
│   │   │   ├── admin.py       # Admin functions
│   │   │   └── alerts.py      # Notifications
│   │   ├── core/              # Core utilities
│   │   │   ├── auth.py        # JWT authentication
│   │   │   └── logging.py     # Logging configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   ├── ocr_service.py      # Document processing
│   │   │   ├── scorecard_service.py # Credit scoring
│   │   │   ├── file_service.py     # File handling
│   │   │   ├── audit_service.py    # Audit logging
│   │   │   └── status_service.py   # Status management
│   │   └── main.py            # FastAPI application
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Test suite
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Vue.js frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   │   ├── onboarding/    # Onboarding steps
│   │   │   ├── admin/         # Admin panels
│   │   │   └── customer/      # Customer views
│   │   ├── views/             # Page components
│   │   ├── stores/            # Pinia state management
│   │   ├── services/          # API integration
│   │   └── router/            # Vue Router
│   └── package.json           # Node.js dependencies
├── docker-compose.yml         # Container orchestration
├── deploy.sh                  # Deployment script
└── setup.sh                   # Development setup
```

## 🔧 Configuration

### Environment Variables
Key settings in `backend/.env`:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/microfinance
ASYNC_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/microfinance

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# External Services
SCORECARD_API_URL=http://localhost:8001
SCORECARD_API_KEY=your-api-key

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./uploads
ALLOWED_EXTENSIONS=["pdf", "jpg", "jpeg", "png", "doc", "docx"]

# OCR
TESSERACT_CMD=/usr/bin/tesseract
OCR_LANGUAGES=eng

# Email & SMS (optional)
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
```

## 🎯 Onboarding Flow

### 5-Step Wizard Process
1. **Personal Information**: Name, DOB, ID number, demographics
2. **Contact Information**: Address, phone, emergency contacts
3. **Financial Profile**: Employment, income, banking details
4. **Document Upload**: ID documents with OCR processing
5. **Consent & Scoring**: Consent collection and credit assessment

### OCR Document Processing
- **Supported Documents**: National ID, Passport, Driver's License
- **Auto-fill Capabilities**: Extract and populate form fields
- **Quality Validation**: Confidence scoring for extracted data
- **Error Handling**: Graceful fallback for processing failures

### Credit Scoring Integration
- **Real-time Assessment**: External scorecard API integration
- **Grade Mapping**: AA, A, B, C, D scale with eligibility determination
- **Personalized Recommendations**: Actionable insights for improvement
- **Fallback Handling**: Graceful degradation when service unavailable

## 💰 Loan Application Management

### Status Lifecycle
```
IN_PROGRESS → SUBMITTED → UNDER_REVIEW → APPROVED → AWAITING_DISBURSEMENT → DONE
     ↓              ↓              ↓
CANCELLED      CANCELLED      REJECTED
```

### Role-Based Permissions
- **Customers**: Submit, cancel, view own applications
- **Loan Officers**: Review, approve/reject, manage disbursement
- **Risk Officers**: Risk assessment and approval
- **Admins**: Full system access and overrides

### Features
- **One Active Application Rule**: Prevents multiple concurrent applications
- **Status Timeline**: Complete history of all status changes
- **Audit Logging**: Immutable records of all actions
- **Notification System**: Email/SMS alerts for status changes

## 🛡️ Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access Control**: Granular permissions per user type
- **Session Management**: Secure session handling with refresh tokens
- **Account Lockout**: Brute force protection

### Data Protection
- **Encryption**: Sensitive data encrypted at rest and in transit
- **Audit Trails**: Complete logging of all user actions
- **Data Sanitization**: PII masking in logs and responses
- **Consent Fingerprinting**: Cryptographic consent verification

### File Security
- **MIME Type Validation**: File content verification
- **Size Limits**: Prevent resource exhaustion attacks
- **Virus Scanning**: File integrity checks
- **Secure Storage**: Organized file system with access controls

## 📊 Monitoring & Analytics

### Health Monitoring
- **Service Health Checks**: `/health`, `/healthz`, `/ready` endpoints
- **Prometheus Metrics**: Application and business metrics
- **Grafana Dashboards**: Real-time monitoring and alerting
- **Log Aggregation**: Structured logging with correlation IDs

### Admin Analytics
- **Application Statistics**: Success rates, processing times
- **User Activity Tracking**: Login patterns, feature usage
- **System Performance**: Response times, error rates
- **Business Intelligence**: Conversion rates, approval statistics

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/ -v                    # Run all tests
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests only
pytest --cov=app tests/            # With coverage
```

### Frontend Testing
```bash
cd frontend
npm run test                        # Run tests
npm run test:coverage              # With coverage
npm run lint                       # Code linting
```

## 📝 API Usage Examples

### Create Onboarding Application
```bash
curl -X POST http://localhost:8000/api/v1/onboarding/applications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### Complete Onboarding Step
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

### Upload Document with OCR
```bash
curl -X POST http://localhost:8000/api/v1/onboarding/applications/{app_id}/documents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.jpg" \
  -F "document_type=national_id"
```

### Check Application Status
```bash
curl -X GET http://localhost:8000/api/v1/status/applications/{app_id}/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🚀 Deployment

### Production Deployment
```bash
# Set production environment variables
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@prod-db/microfinance
export SECRET_KEY=your-production-secret-key

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n microfinance
kubectl get services -n microfinance
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the test suite**: `pytest tests/`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint for API documentation
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions and ideas

## 🏆 Features Summary

- ✅ **Complete Onboarding System** with 5-step wizard
- ✅ **OCR Document Processing** with Tesseract integration
- ✅ **Real-time Credit Scoring** via external API
- ✅ **Loan Application Management** with status tracking
- ✅ **Role-based Access Control** for all user types
- ✅ **Comprehensive Audit Logging** for compliance
- ✅ **Mobile-responsive Frontend** with Vue.js 3
- ✅ **Microservices Architecture** with Docker support
- ✅ **Production-ready Security** with JWT and encryption
- ✅ **Monitoring & Analytics** with Prometheus/Grafana
- ✅ **Complete Test Suite** with high coverage
- ✅ **Docker Deployment** with one-command setup

---

**Built with ❤️ for modern microfinance institutions** 