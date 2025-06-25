# Credit Scorecard Microservice

A comprehensive microservice for evaluating applicant data using institution-specific scoring logic with versioning, audit capabilities, and safe expression evaluation.

## 🧠 Overview

The Credit Scorecard Microservice enables Microfinance Institutions (MFIs) to:

- **Create and manage custom scoring rules** tailored to their specific criteria
- **Evaluate applicants** using configurable scorecards with detailed breakdowns
- **Version control scorecards** for traceability and testing
- **Audit all evaluations** with comprehensive logging
- **Scale safely** with secure expression evaluation (no eval() risks)

## ✅ Features

### Core Functionality
- ✅ **Per-MFI Scorecard Customization**: Institution-specific rules, weights, and ratings
- ✅ **Safe Expression Evaluation**: Secure rule processing without eval() security risks
- ✅ **Comprehensive Scoring**: Returns total score, letter grade (AA-D), and eligibility
- ✅ **Detailed Breakdowns**: Human-readable explanations for every score
- ✅ **Version Control**: Full scorecard versioning with rollback capabilities
- ✅ **Audit Trail**: Immutable logging of all evaluations

### Integration Points
- ✅ **RESTful API**: Easy integration with onboarding flows and loan applications
- ✅ **Health Checks**: Service monitoring and graceful failure handling
- ✅ **Admin Interface**: Comprehensive scorecard management API
- ✅ **Extensible**: Ready for data enrichment APIs and external services

### Security & Reliability
- ✅ **Safe Rule Engine**: Uses `simpleeval` for secure expression processing
- ✅ **Input Validation**: Comprehensive request validation with Pydantic
- ✅ **Error Handling**: Graceful failure with detailed error responses
- ✅ **Database Transactions**: ACID compliance for data integrity

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin UI      │    │  Loan App       │    │  Onboarding     │
│                 │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │  Credit Scorecard API     │
                    │  ┌─────────────────────┐  │
                    │  │  FastAPI Router     │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Business Logic     │  │
                    │  │  • ScoringEngine    │  │
                    │  │  • SafeEvaluator   │  │
                    │  │  • LetterGrader    │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Data Layer         │  │
                    │  │  • SQLAlchemy       │  │
                    │  │  • PostgreSQL       │  │
                    │  └─────────────────────┘  │
                    └───────────────────────────┘
```

## 📦 Key Data Objects

- **ScorecardConfig**: Main scorecard configuration per MFI
- **ScorecardVersion**: Versioned scorecard with full configuration
- **ScoringFactor**: Individual factors (income, debt ratio, employment, etc.)
- **ScoreResult**: Evaluation results with scores and breakdowns
- **EvaluationLog**: Detailed audit logs for compliance

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd onboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start with Docker Compose** (recommended)
   ```bash
   docker-compose up -d
   ```

   Or **start manually**:
   ```bash
   # Start PostgreSQL
   # Update DATABASE_URL in .env
   
   # Run the application
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## 📋 API Usage

### 1. Create a Scorecard

```bash
curl -X POST "http://localhost:8000/api/v1/scorecards/" \
  -H "Content-Type: application/json" \
  -d '{
    "mfi_id": "MFI001",
    "name": "Basic Credit Scorecard",
    "description": "Standard scorecard for microfinance loans",
    "min_score": 300,
    "max_score": 850,
    "passing_score": 600
  }'
```

### 2. Create a Scorecard Version with Factors

```bash
curl -X POST "http://localhost:8000/api/v1/scorecards/1/versions" \
  -H "Content-Type: application/json" \
  -d @examples/sample_scorecard.json
```

### 3. Evaluate an Applicant

```bash
curl -X POST "http://localhost:8000/api/v1/evaluation/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "scorecard_uuid": "12345678-1234-5678-9012-123456789012",
    "applicant_id": "APP_001",
    "request_id": "REQ_001",
    "user_id": "loan_officer_123",
    "source_system": "loan_application",
    "applicant_data": {
      "monthly_income": 35000,
      "debt_to_income_ratio": 0.25,
      "employment_status": "full_time",
      "credit_history_months": 42,
      "age": 32,
      "savings_balance": 75000,
      "education_level": "bachelor"
    }
  }'
```

### Example Response

```json
{
  "id": 1,
  "uuid": "87654321-4321-8765-2109-876543210987",
  "total_score": 742,
  "letter_grade": "A",
  "eligibility": true,
  "factor_scores": [
    {
      "code": "monthly_income",
      "name": "Monthly Income",
      "points": 80,
      "max_points": 100,
      "weight": 2.5,
      "value": 35000,
      "reasoning": ["monthly_income=35000 falls in range [30000, 49999], awarded 80 points"]
    }
  ],
  "breakdown": {
    "total_score": 742,
    "letter_grade": "A",
    "eligibility": true,
    "summary": "Credit evaluation using Basic Credit Scorecard: Score 742 (Grade A), applicant is eligible for credit."
  },
  "processing_time_ms": 45,
  "data_completeness": 1.0,
  "confidence_score": 0.95
}
```

## 🔧 Scoring Rules

The service supports three types of scoring rules:

### 1. Threshold Rules
```json
{
  "rules": {
    "thresholds": {
      "field": "monthly_income",
      "ranges": [
        {"min": 30000, "max": 49999, "points": 80},
        {"min": 10000, "max": 29999, "points": 60}
      ]
    }
  }
}
```

### 2. Condition Rules
```json
{
  "rules": {
    "conditions": [
      {"condition": "employment_status == 'full_time'", "points": 100},
      {"condition": "age >= 25 and age <= 65", "points": 80}
    ]
  }
}
```

### 3. Expression Rules
```json
{
  "rules": {
    "expression": "min(100, max(0, (savings_balance / 10000) * 50 + 50))"
  }
}
```

## 👥 Role-Based Usage

### Admin
- Configure scorecards and scoring factors
- Manage scoring rules and weights
- Control scorecard versioning
- Monitor evaluation metrics

### Risk Officer
- View evaluation results and breakdowns
- Access audit trails and logs
- Analyze scoring patterns
- Generate compliance reports

### System Integration
- Evaluate applicants via API
- Retrieve historical results
- Monitor service health
- Handle graceful failures

## 🖥️ Admin Operations

### Version Management
```bash
# List all versions
GET /api/v1/scorecards/{id}/versions

# Activate a version
POST /api/v1/scorecards/{id}/versions/{version_id}/activate

# Clone a version
POST /api/v1/scorecards/{id}/versions/{version_id}/clone

# Clean up old versions
POST /api/v1/scorecards/{id}/cleanup
```

### Monitoring
```bash
# Service health
GET /health

# Evaluation service health
GET /api/v1/evaluation/health

# Basic metrics
GET /metrics
```

## 🔒 Security Features

- **Safe Expression Evaluation**: Uses `simpleeval` to prevent code injection
- **Input Validation**: Comprehensive request validation with Pydantic schemas
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **Error Handling**: Detailed logging without exposing sensitive data
- **Rate Limiting**: Ready for implementation with middleware

## 🏗️ Development

### Project Structure
```
app/
├── api/              # FastAPI routers
├── core/             # Business logic (scoring engine, evaluators)
├── models/           # SQLAlchemy database models
├── schemas/          # Pydantic request/response schemas
├── services/         # Business services layer
└── main.py           # FastAPI application

examples/             # Sample configurations and requests
tests/               # Test suite
config.py            # Application configuration
requirements.txt     # Python dependencies
```

### Running Tests
```bash
pytest tests/ -v
```

### Database Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## 🔄 Integration Examples

### Onboarding Flow
```python
# Initial eligibility check
response = await client.post("/api/v1/evaluation/evaluate", json={
    "scorecard_uuid": scorecard_uuid,
    "applicant_id": applicant_id,
    "applicant_data": basic_data,
    "source_system": "onboarding"
})

if response.json()["eligibility"]:
    # Proceed with full application
    continue_onboarding()
else:
    # Provide feedback and alternative options
    provide_feedback(response.json()["breakdown"])
```

### Loan Application
```python
# Final pre-approval evaluation
response = await client.post("/api/v1/evaluation/evaluate", json={
    "scorecard_uuid": scorecard_uuid,
    "applicant_id": applicant_id,
    "applicant_data": complete_data,
    "source_system": "loan_application",
    "user_id": loan_officer_id
})

# Log for audit
evaluation_id = response.json()["uuid"]
log_loan_decision(evaluation_id, response.json()["eligibility"])
```

## 📊 Monitoring & Observability

### Health Checks
- **Service Health**: `/health` - Basic service status
- **Evaluation Health**: `/api/v1/evaluation/health` - Full system check
- **Database Connectivity**: Automatic connection testing

### Logging
- **Structured Logging**: JSON format for easy parsing
- **Audit Trail**: Complete evaluation history
- **Error Tracking**: Detailed error context without sensitive data
- **Performance Metrics**: Request timing and processing stats

### Metrics (Extensible)
- Evaluation request rate
- Success/failure ratios
- Average processing times
- Score distribution patterns

## 🔧 Configuration

### Environment Variables
See `.env.example` for all configuration options:

- **Database**: Connection string and pool settings
- **Security**: Secret keys and token expiration
- **Service**: Host, port, and debug settings
- **Scorecard**: Version limits and score ranges

### Deployment
- **Docker**: Production-ready container with health checks
- **Kubernetes**: Ready for orchestration with proper probes
- **Load Balancing**: Stateless design for horizontal scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For support and questions:
- Check the `/docs` endpoint for API documentation
- Review example requests in the `examples/` directory
- Examine the health check endpoints for diagnostics

---

**Built with ❤️ for secure, scalable credit evaluation** 