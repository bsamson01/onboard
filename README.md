# Modular Microfinance Onboarding & Loan Management Platform

A full-featured microfinance platform designed to support onboarding, credit scoring, loan management, risk alerts, and customer engagement with modular external scorecard engine per institution.

## 🏗️ Architecture

- **Backend-driven**: All logic, scoring, and data processing handled server-side
- **Modular design**: Scorecard engine, notifications, and integrations are swappable components
- **Role-based access**: Admin, risk officer, loan officer, support, customer
- **Real-time communication**: Email, in-app, and SMS alerts
- **Auditability**: Append-only logs, no deletions
- **No caching**: All data is live/fresh

## 🚀 Tech Stack

- **Backend**: FastAPI with async support
- **Database**: PostgreSQL + Redis
- **Queue**: Celery task queue
- **Frontend**: Vue.js with WebSocket support
- **Containerization**: Docker + Kubernetes/ECS
- **Monitoring**: Prometheus, Grafana, ELK
- **CI/CD**: GitHub Actions

## 📋 Core Modules

### 🔐 User Management & Security
- JWT/OAuth2 Authentication
- Role-Based Access Control (RBAC)
- Multi-factor Authentication
- Session Tracking & Login Logs
- Immutable Audit Log

### 👥 Customer Onboarding
- Multi-step form (personal, contact, financial info)
- Document Upload with OCR Processing
- Consent management
- Initial eligibility scoring

### 📊 Credit Scorecard Microservice
- External RESTful service per MFI
- Custom scoring rules, weights, bands (AA-D)
- Safe rule engine parser
- Versioned scorecards
- Admin-configurable UI

### 💰 Loan Application Management
- Full CRUD operations
- Application lifecycle management
- Score + eligibility display
- Escalation notes and overrides

### ⚠️ Delinquency & Alerts
- Alert engine with configurable triggers
- Role-restricted visibility
- Webhook integration
- Alert queue management

### 👤 Customer Portal
- Secure customer login
- Application tracking
- Loan management
- Payment submissions
- Support ticketing

### 📧 Notification System
- Transactional emails
- In-app alerts via WebSocket
- SMS integration
- Templated messages
- Drip campaigns

### 📈 Reporting & Export
- Backend-generated exports (XLSX/CSV)
- Filterable reports
- Delinquency trends
- Export logs

### 🔌 Integrations
- ID verification APIs
- Mobile money platforms
- Credit bureaus
- Accounting tools
- Notification partners

## 🛠️ Development Phases

- **Phase 1**: Core Backend + Onboarding (6-8 weeks) ✅ In Progress
- **Phase 2**: Scorecard Engine (4-6 weeks)
- **Phase 3**: Loan App + Alerts (5-7 weeks)
- **Phase 4**: Customer Portal + Support (6-8 weeks)
- **Phase 5**: Notifications + Emails (4-6 weeks)
- **Phase 6**: Reports & Exports (3-5 weeks)
- **Phase 7**: Integrations + Final Security (5-7 weeks)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Configure your database and Redis settings in .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Docker Setup
```bash
docker-compose up -d
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions, please open an issue or contact the development team. 