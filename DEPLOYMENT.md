# Deployment Guide

This guide covers deployment options for the Credit Scorecard Microservice in various environments.

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd onboard

# Run automated setup
python setup.py --mode local

# Or with Docker
python setup.py --mode docker
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start PostgreSQL and update DATABASE_URL in .env

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🐳 Docker Deployment

### Development with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f scorecard-service

# Stop services
docker-compose down
```

### Production Docker Setup
```bash
# Build production image
docker build -t scorecard-service:latest .

# Run with production settings
docker run -d \
  --name scorecard-service \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e DEBUG=false \
  scorecard-service:latest
```

## ☸️ Kubernetes Deployment

### Basic Kubernetes Manifests

**Deployment (deployment.yaml):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scorecard-service
  labels:
    app: scorecard-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: scorecard-service
  template:
    metadata:
      labels:
        app: scorecard-service
    spec:
      containers:
      - name: scorecard-service
        image: scorecard-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: scorecard-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: scorecard-secrets
              key: secret-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**Service (service.yaml):**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: scorecard-service
spec:
  selector:
    app: scorecard-service
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
```

**Secrets (secrets.yaml):**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: scorecard-secrets
type: Opaque
data:
  database-url: <base64-encoded-database-url>
  secret-key: <base64-encoded-secret-key>
```

### Deploy to Kubernetes
```bash
# Apply manifests
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f secrets.yaml

# Check deployment
kubectl get pods -l app=scorecard-service
kubectl logs -l app=scorecard-service

# Expose service (if needed)
kubectl expose service scorecard-service --type=LoadBalancer --name=scorecard-lb
```

## 🌐 Production Configuration

### Environment Variables

**Required:**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/scorecard_db
SECRET_KEY=your-long-random-secret-key-for-production
```

**Optional:**
```bash
# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Credit Scorecard Microservice

# Security
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Scorecard Settings
MAX_SCORECARD_VERSIONS=100
```

### Database Setup

**PostgreSQL Configuration:**
```sql
-- Create database and user
CREATE DATABASE scorecard_db;
CREATE USER scorecard_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE scorecard_db TO scorecard_user;

-- For production, consider additional security settings
ALTER USER scorecard_user SET default_transaction_isolation TO 'read committed';
ALTER USER scorecard_user SET timezone TO 'UTC';
```

**Connection Pool Settings:**
- **Min Pool Size**: 5
- **Max Pool Size**: 20
- **Pool Timeout**: 30s
- **Pool Recycle**: 300s

### Security Considerations

1. **Environment Variables**: Store sensitive data in environment variables or secrets management
2. **HTTPS**: Use HTTPS in production with proper SSL certificates
3. **Authentication**: Implement proper authentication for admin endpoints
4. **CORS**: Configure CORS appropriately for your domain
5. **Rate Limiting**: Implement rate limiting for API endpoints
6. **Input Validation**: All inputs are validated, but monitor for unusual patterns
7. **Logging**: Ensure logs don't contain sensitive information

### Performance Tuning

**Application Settings:**
```python
# In production config
WORKERS = (CPU_CORES * 2) + 1
WORKER_CLASS = "uvicorn.workers.UvicornWorker"
MAX_REQUESTS = 1000
MAX_REQUESTS_JITTER = 100
TIMEOUT = 30
KEEPALIVE = 2
```

**Database Optimization:**
- Use connection pooling
- Implement read replicas for heavy read workloads
- Add database indexes for frequently queried fields
- Regular vacuum and analyze operations

**Caching Strategy:**
- Redis for session storage and temporary data
- Application-level caching for scorecard configurations
- CDN for static content (if applicable)

## 📊 Monitoring and Observability

### Health Checks
```bash
# Basic health check
curl http://your-service/health

# Detailed health check (admin)
curl http://your-service/api/v1/admin/health/detailed

# Evaluation service health
curl http://your-service/api/v1/evaluation/health
```

### Metrics Collection

**Prometheus Integration:**
```yaml
# Add to docker-compose.yml or Kubernetes
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

**Key Metrics to Monitor:**
- Request rate and response times
- Error rates and types
- Database connection pool usage
- Memory and CPU utilization
- Evaluation success/failure rates
- Scorecard usage patterns

### Logging

**Structured Logging Configuration:**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy Scorecard Service

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest tests/ -v

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker image
      run: docker build -t scorecard-service:${{ github.sha }} .
    - name: Push to registry
      run: |
        docker tag scorecard-service:${{ github.sha }} your-registry/scorecard-service:${{ github.sha }}
        docker push your-registry/scorecard-service:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/scorecard-service \
          scorecard-service=your-registry/scorecard-service:${{ github.sha }}
        kubectl rollout status deployment/scorecard-service
```

## 🛠️ Maintenance

### Database Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Backup Strategy
```bash
# Database backup
pg_dump scorecard_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql scorecard_db < backup_file.sql
```

### Version Updates
1. Run tests in staging environment
2. Create database backup
3. Deploy new version
4. Run post-deployment health checks
5. Monitor metrics for anomalies

## 🚨 Troubleshooting

### Common Issues

**Service Won't Start:**
- Check DATABASE_URL format
- Verify PostgreSQL is running
- Check port availability
- Review environment variables

**Database Connection Issues:**
- Verify connection string
- Check firewall settings
- Test network connectivity
- Review database user permissions

**Performance Issues:**
- Monitor database query performance
- Check connection pool settings
- Review application logs
- Analyze resource utilization

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true

# Run with verbose output
uvicorn app.main:app --log-level debug
```

## 📞 Support

For deployment issues:
1. Check service logs: `docker logs <container-id>`
2. Verify health endpoints: `/health`, `/api/v1/evaluation/health`
3. Review configuration settings
4. Monitor system resources

---

**Production deployment requires careful planning and testing. Always test in a staging environment first.**