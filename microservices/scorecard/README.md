# Scorecard Microservice

A standalone FastAPI microservice for credit scoring and risk assessment in the microfinance platform.

## Overview

The Scorecard Microservice provides comprehensive credit scoring functionality, calculating credit scores on a 0-1000 scale, assigning credit grades (AA-D), determining loan eligibility, and providing personalized recommendations for credit improvement.

## Features

- **Credit Score Calculation**: Sophisticated scoring algorithm considering multiple factors
- **Risk Assessment**: Comprehensive evaluation of financial and employment stability
- **Grade Classification**: Credit grades from AA (excellent) to D (poor)
- **Eligibility Determination**: Loan eligibility based on score thresholds
- **Personalized Recommendations**: Actionable advice for credit improvement
- **Health Monitoring**: Built-in health check endpoint
- **API Key Authentication**: Secure access control
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status.

### Credit Score Calculation
```
POST /api/v1/score
```
**Headers:**
- `Authorization: Bearer {api_key}`
- `Content-Type: application/json`
- `X-API-Version: v1`

**Request Body:**
```json
{
  "customer_profile": {
    "age": 35,
    "gender": "male",
    "marital_status": "married",
    "nationality": "US",
    "location": {
      "city": "New York",
      "state": "NY",
      "country": "US"
    }
  },
  "financial_profile": {
    "employment_status": "employed",
    "monthly_income": 5000.0,
    "employment_duration_months": 24,
    "has_bank_account": true,
    "bank_account_type": "checking",
    "has_other_loans": false,
    "other_loans_count": 0,
    "total_other_loans_amount": 0.0
  },
  "risk_factors": {
    "income_stability": "high",
    "debt_to_income_ratio": 0.15,
    "employment_stability": "stable"
  },
  "request_metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "scorecard_version": "v1.0",
    "request_id": "score_20240115_103000"
  }
}
```

**Response:**
```json
{
  "score": 720,
  "grade": "A",
  "eligibility": "eligible",
  "message": "Very good credit profile! Your score of 720 qualifies you for competitive rates.",
  "breakdown": {
    "base_score": 700,
    "income_adjustment": 20,
    "final_score": 720,
    "risk_factors": {
      "income_stability": "high",
      "debt_to_income_ratio": 0.15,
      "employment_stability": "stable"
    }
  },
  "recommendations": [
    "Maintain consistent employment history",
    "Consider providing additional income documentation"
  ]
}
```

## Scoring Algorithm

### Score Ranges and Grades
- **AA (900-1000)**: Excellent credit profile
- **A (800-899)**: Very good credit profile  
- **B (700-799)**: Good credit profile
- **C (600-699)**: Fair credit profile
- **D (0-599)**: Poor credit profile

### Eligibility Thresholds
- **Minimum Eligible Score**: 600
- **Auto Approval Score**: 800+

### Scoring Factors

1. **Base Score Calculation (500 starting point)**
   - Age factor (optimal 25-55): +50
   - Employment status: +100 (employed), +75 (self-employed), -100 (unemployed)
   - Employment duration: +75 (24+ months), +50 (12-23 months), +25 (6-11 months)
   - Banking relationship: +50 (has account), +25 (checking account)
   - Existing loans: -25 to -100 (based on count), +25 (no loans)

2. **Income Adjustments**
   - $10,000+: +100
   - $7,500-$9,999: +75
   - $5,000-$7,499: +50
   - $3,000-$4,999: +25
   - $2,000-$2,999: 0
   - $1,000-$1,999: -25
   - <$1,000: -50

3. **Risk Factor Adjustments**
   - Income stability: +50 (high), +25 (medium), -50 (low)
   - Debt-to-income ratio: +50 (<0.2), +25 (0.2-0.3), 0 (0.3-0.4), -25 (0.4-0.5), -75 (>0.5)
   - Employment stability: +50 (stable), +25 (moderate), -50 (unstable)

## Configuration

### Environment Variables
- `SCORECARD_API_KEY`: API key for authentication (required)
- `ENVIRONMENT`: Application environment (development/production)
- `SERVICE_PORT`: Service port (default: 8001)
- `LOG_LEVEL`: Logging level (default: INFO)

### Docker Configuration
The service is containerized with:
- Health checks every 30 seconds
- Non-root user for security
- Proper logging configuration
- Resource limits for production

## Quick Start

### Using Docker Compose
1. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

2. Update the API key in `.env`:
   ```
   SCORECARD_API_KEY=your_secure_api_key_here
   ```

3. Start the service:
   ```bash
   docker-compose up -d
   ```

4. Verify the service is running:
   ```bash
   curl http://localhost:8001/health
   ```

### Local Development
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export SCORECARD_API_KEY=your_api_key
   export ENVIRONMENT=development
   ```

3. Run the service:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

## Testing the API

### Health Check
```bash
curl -X GET http://localhost:8001/health
```

### Score Calculation
```bash
curl -X POST http://localhost:8001/api/v1/score \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -H "X-API-Version: v1" \
  -d '{
    "customer_profile": {
      "age": 35,
      "gender": "male",
      "marital_status": "married",
      "nationality": "US",
      "location": {"city": "New York", "state": "NY", "country": "US"}
    },
    "financial_profile": {
      "employment_status": "employed",
      "monthly_income": 5000.0,
      "employment_duration_months": 24,
      "has_bank_account": true,
      "bank_account_type": "checking",
      "has_other_loans": false,
      "other_loans_count": 0,
      "total_other_loans_amount": 0.0
    },
    "risk_factors": {
      "income_stability": "high",
      "debt_to_income_ratio": 0.15,
      "employment_stability": "stable"
    },
    "request_metadata": {
      "timestamp": "2024-01-15T10:30:00Z",
      "scorecard_version": "v1.0",
      "request_id": "test_request_001"
    }
  }'
```

## Monitoring and Observability

### Health Monitoring
- Health check endpoint: `/health`
- Docker health checks configured
- Response time monitoring
- Error rate tracking

### Logging
- Structured JSON logging
- Request/response logging
- Error logging with stack traces
- Performance metrics logging

### Metrics
- Request count and response times
- Error rates by endpoint
- Authentication failures
- Service availability

## Security

### Authentication
- API key-based authentication
- Bearer token format required
- Key rotation support

### Data Protection
- No sensitive data stored
- Secure data transmission
- Input validation and sanitization
- Non-root container execution

## Error Handling

### HTTP Status Codes
- `200`: Successful score calculation
- `401`: Authentication failure
- `422`: Invalid input data
- `500`: Internal server error

### Error Response Format
```json
{
  "detail": "Error description",
  "status_code": 422
}
```

### Fallback Mechanism
If scoring fails, the service returns a neutral response with:
- Score: 500 (neutral)
- Grade: C
- Eligibility: pending
- Generic recommendations

## Production Deployment

### Resource Requirements
- **CPU**: 0.5 cores minimum, 1 core recommended
- **Memory**: 512MB minimum, 1GB recommended
- **Storage**: Minimal (stateless service)

### Scaling Considerations
- Stateless design enables horizontal scaling
- Load balancer compatible
- Database-free for maximum scalability

### High Availability
- Multiple container instances
- Health check-based routing
- Graceful shutdown handling
- Circuit breaker pattern for external dependencies

## Integration

### Main Application Integration
The scorecard service integrates with the main application through:
- HTTP API calls from the onboarding service
- Configuration management in admin panel
- Health status monitoring
- Audit logging integration

### Network Configuration
- Docker network: `microfinance_network`
- Internal communication on port 8001
- External access through load balancer/proxy

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API key is set correctly
   - Check Authorization header format
   - Ensure Bearer token prefix

2. **Validation Errors**
   - Check required fields are provided
   - Verify data types and ranges
   - Review field constraints

3. **Service Unavailable**
   - Check container health status
   - Verify network connectivity
   - Review service logs

### Log Analysis
```bash
# View service logs
docker logs microfinance_scorecard

# Follow logs in real-time
docker logs -f microfinance_scorecard

# View health check logs
docker inspect microfinance_scorecard | grep Health
```

## Development

### Code Structure
```
app/
├── __init__.py          # Package initialization
├── main.py              # FastAPI application
├── models.py            # Pydantic data models
├── scoring_engine.py    # Core scoring algorithm
└── auth.py              # Authentication logic
```

### Adding New Features
1. Update models in `models.py`
2. Implement logic in `scoring_engine.py`
3. Add endpoints in `main.py`
4. Update documentation

### Testing
- Unit tests for scoring engine logic
- Integration tests for API endpoints
- Load testing for performance validation
- Security testing for authentication

## License

This microservice is part of the microfinance platform and follows the same licensing terms.