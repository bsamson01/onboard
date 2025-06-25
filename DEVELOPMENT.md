# Microfinance Platform Development Guide

## 🏗️ Architecture Overview

The Microfinance Platform is built using a **modular, microservices architecture** with the following key components:

### Backend Services
- **FastAPI Application**: Main API server with async support
- **PostgreSQL**: Primary database for all application data
- **Redis**: Caching, session storage, and Celery message broker
- **Celery Workers**: Background task processing
- **External Scorecard Service**: Modular credit scoring microservice

### Frontend
- **Vue.js 3**: Modern reactive frontend framework
- **Vite**: Fast development build tool
- **Tailwind CSS**: Utility-first CSS framework
- **Pinia**: State management

### Monitoring & Tools
- **Prometheus**: Metrics collection
- **Grafana**: Data visualization and dashboards
- **pgAdmin**: Database administration
- **Redis Commander**: Redis management

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Git

### One-Command Setup
```bash
./deploy.sh
```

This script will:
1. Check Docker installation
2. Create necessary directories and configuration files
3. Set up environment variables
4. Build and start all services
5. Run database migrations
6. Display service URLs and credentials

### Manual Setup

1. **Clone and Setup Environment**
```bash
git clone <repository-url>
cd microfinance-platform
cp backend/.env.example backend/.env
```

2. **Start Services**
```bash
docker-compose up -d
```

3. **Run Database Migrations**
```bash
docker-compose exec backend alembic upgrade head
```

## 🔧 Development Workflow

### Backend Development

1. **Start Development Environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your local database settings
```

3. **Run Locally (for development)**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

1. **Setup Frontend**
```bash
cd frontend
npm install
```

2. **Start Development Server**
```bash
npm run dev
```

3. **Build for Production**
```bash
npm run build
```

### Database Management

#### Creating Migrations
```bash
# Auto-generate migration from model changes
docker-compose exec backend alembic revision --autogenerate -m "Description of changes"

# Create empty migration
docker-compose exec backend alembic revision -m "Description"
```

#### Running Migrations
```bash
# Upgrade to latest
docker-compose exec backend alembic upgrade head

# Upgrade to specific revision
docker-compose exec backend alembic upgrade <revision_id>

# Downgrade
docker-compose exec backend alembic downgrade -1
```

#### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U microfinance_user -d microfinance_db

# Or use pgAdmin at http://localhost:5050
```

### Task Queue Management

#### Celery Commands
```bash
# Start worker (if not using docker-compose)
celery -A app.core.celery worker --loglevel=info

# Start beat scheduler
celery -A app.core.celery beat --loglevel=info

# Monitor tasks
celery -A app.core.celery flower
```

## 📊 Monitoring & Debugging

### Service Health Checks
```bash
# Check all services
./deploy.sh status

# Check specific service logs
./deploy.sh logs backend
./deploy.sh logs frontend
```

### Health Endpoints
- Backend: `http://localhost:8000/health`
- Scorecard: `http://localhost:8001/health`

### Monitoring Dashboards
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **pgAdmin**: http://localhost:5050 (admin@microfinance.com/admin123)
- **Redis Commander**: http://localhost:8081

### Log Locations
```bash
# Application logs
docker-compose logs -f backend

# Specific log files (when running locally)
tail -f logs/app.log
tail -f logs/errors.log
tail -f logs/security.log
tail -f logs/audit.log
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/ -v
pytest tests/test_auth.py -v
pytest --cov=app tests/
```

### Frontend Testing
```bash
cd frontend
npm run test
npm run test:coverage
```

### Integration Testing
```bash
# Run full test suite
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## 📁 Project Structure

```
microfinance-platform/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   ├── api/               # API routes
│   │   │   ├── core/              # Core functionality (auth, security, etc.)
│   │   │   ├── models/            # Database models
│   │   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── services/          # Business logic
│   │   │   └── utils/             # Utilities
│   │   └── requirements.txt
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend tests
│   └── requirements.txt
├── frontend/                   # Vue.js frontend
│   ├── src/
│   │   ├── components/        # Vue components
│   │   ├── views/             # Page views
│   │   ├── stores/            # Pinia stores
│   │   └── router/            # Vue Router config
│   └── package.json
├── scorecard-service/          # External scorecard microservice
├── monitoring/                 # Monitoring configuration
├── logs/                      # Application logs
├── uploads/                   # File uploads
└── docker-compose.yml
```

## 🔐 Security Considerations

### Authentication & Authorization
- JWT tokens with configurable expiration
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Session management with Redis
- MFA support (optional)

### Data Protection
- All API endpoints require authentication
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy ORM
- File upload restrictions and validation
- Comprehensive audit logging

### Infrastructure Security
- Non-root containers
- Health checks for all services
- Network isolation with Docker networks
- Environment variable management
- HTTPS/TLS support in production

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
```bash
# Set production environment variables
export ENVIRONMENT=production
export DEBUG=False
export SECRET_KEY=your-production-secret-key
```

2. **Database Setup**
```bash
# Run migrations on production database
alembic upgrade head
```

3. **Container Deployment**
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

### Environment Variables

#### Required Backend Variables
```env
DATABASE_URL=postgresql://user:pass@host:5432/db
ASYNC_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
SECRET_KEY=your-secret-key
```

#### Optional Variables
```env
# Email Configuration
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-password
MAIL_SERVER=smtp.gmail.com

# SMS Configuration
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token

# External Services
SCORECARD_API_URL=http://scorecard-service:8001
```

## 📋 API Documentation

### Available Endpoints

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Current user info

#### Users
- `GET /api/v1/users/` - List users (admin)
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

#### Customers
- `GET /api/v1/customers/` - List customers
- `POST /api/v1/customers/` - Create customer
- `GET /api/v1/customers/{id}` - Get customer
- `PUT /api/v1/customers/{id}` - Update customer

#### Onboarding
- `GET /api/v1/onboarding/applications` - List applications
- `POST /api/v1/onboarding/applications` - Create application
- `GET /api/v1/onboarding/applications/{id}` - Get application

#### Loans
- `GET /api/v1/loans/applications` - List loan applications
- `POST /api/v1/loans/applications` - Create loan application
- `GET /api/v1/loans/applications/{id}` - Get loan application

#### Alerts
- `GET /api/v1/alerts/` - List alerts
- `POST /api/v1/alerts/` - Create alert
- `PUT /api/v1/alerts/{id}/acknowledge` - Acknowledge alert

### API Documentation URLs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔄 Phase Implementation Status

### ✅ Phase 1: Core Backend + Onboarding (In Progress)
- [x] Backend structure with FastAPI
- [x] Database models and migrations
- [x] Authentication system
- [x] Basic API endpoints
- [x] Docker containerization
- [ ] Complete onboarding flow
- [ ] Document upload & OCR

### 🔜 Phase 2: Scorecard Engine
- [ ] External scoring service integration
- [ ] Configurable admin UI
- [ ] Versioning system
- [ ] Rule engine implementation

### 🔜 Phase 3: Loan App + Alerts
- [ ] Complete loan workflow
- [ ] Alert engine implementation
- [ ] Admin dashboards
- [ ] Risk officer interfaces

### 🔜 Phase 4: Customer Portal
- [ ] Customer-facing UI
- [ ] Loan tracking
- [ ] Payment submissions
- [ ] Support ticketing

### 🔜 Phase 5: Notifications
- [ ] Email templates
- [ ] SMS integration
- [ ] Drip campaigns
- [ ] Delivery tracking

### 🔜 Phase 6: Reports & Exports
- [ ] Report generation
- [ ] Data export functionality
- [ ] Admin reporting UI
- [ ] Scheduled reports

### 🔜 Phase 7: Integrations
- [ ] Third-party API integrations
- [ ] System hardening
- [ ] Compliance features
- [ ] Performance optimization

## 🆘 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database status
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

#### Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432

# Stop conflicting services
sudo service postgresql stop
```

#### Migration Errors
```bash
# Reset migrations (development only)
docker-compose exec backend alembic downgrade base
docker-compose exec backend alembic upgrade head

# Check migration status
docker-compose exec backend alembic current
docker-compose exec backend alembic history
```

#### Memory Issues
```bash
# Increase Docker memory limits
# Docker Desktop: Settings > Resources > Memory

# Check resource usage
docker stats
```

### Getting Help

1. Check the logs: `./deploy.sh logs [service-name]`
2. Verify service status: `./deploy.sh status`
3. Review the API documentation: http://localhost:8000/docs
4. Check database connections via pgAdmin: http://localhost:5050
5. Monitor system health via Grafana: http://localhost:3001

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests
5. Run the test suite: `pytest`
6. Commit your changes: `git commit -am 'Add my feature'`
7. Push to the branch: `git push origin feature/my-feature`
8. Submit a pull request

### Code Style
- Backend: Black, isort, flake8
- Frontend: ESLint, Prettier
- Pre-commit hooks for code formatting

### Review Process
- All changes require code review
- Tests must pass
- Documentation must be updated
- Security review for sensitive changes