#!/bin/bash

# Microfinance Platform Deployment Script
# This script sets up the complete development environment

set -e  # Exit on any error

echo "🚀 Starting Microfinance Platform Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker and try again."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Create environment files
create_env_files() {
    print_status "Creating environment files..."
    
    # Backend .env file
    if [ ! -f "backend/.env" ]; then
        print_status "Creating backend/.env file..."
        cp backend/.env.example backend/.env
        print_success "Backend .env file created from template"
    else
        print_warning "Backend .env file already exists, skipping..."
    fi
    
    # Frontend .env file
    if [ ! -f "frontend/.env" ]; then
        print_status "Creating frontend/.env file..."
        cat > frontend/.env << EOF
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
VITE_APP_NAME=Microfinance Platform
VITE_APP_VERSION=1.0.0
EOF
        print_success "Frontend .env file created"
    else
        print_warning "Frontend .env file already exists, skipping..."
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    directories=(
        "logs"
        "uploads"
        "monitoring"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/datasources"
        "backend/alembic/versions"
        "frontend/src"
        "scorecard-service"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        fi
    done
}

# Create monitoring configuration
create_monitoring_config() {
    print_status "Creating monitoring configuration..."
    
    # Prometheus configuration
    if [ ! -f "monitoring/prometheus.yml" ]; then
        cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'microfinance-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'microfinance-scorecard'
    static_configs:
      - targets: ['scorecard_service:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s
EOF
        print_success "Prometheus configuration created"
    fi
    
    # Grafana datasource configuration
    if [ ! -f "monitoring/grafana/datasources/prometheus.yml" ]; then
        cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
        print_success "Grafana datasource configuration created"
    fi
}

# Create a simple scorecard service
create_scorecard_service() {
    print_status "Creating mock scorecard service..."
    
    if [ ! -f "scorecard-service/main.py" ]; then
        cat > scorecard-service/main.py << 'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import random

app = FastAPI(title="Scorecard Service", version="1.0.0")

class ScoreRequest(BaseModel):
    customer_id: str
    personal_info: Dict[str, Any]
    financial_info: Dict[str, Any]
    employment_info: Dict[str, Any]

class ScoreResponse(BaseModel):
    customer_id: str
    score: int
    credit_band: str
    scorecard_version: str
    breakdown: Dict[str, Any]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "scorecard"}

@app.post("/score", response_model=ScoreResponse)
async def calculate_score(request: ScoreRequest):
    # Mock scoring logic
    base_score = random.randint(300, 850)
    
    # Simple adjustments based on income
    monthly_income = request.financial_info.get("monthly_income", 0)
    if monthly_income > 5000:
        base_score += 50
    elif monthly_income > 2000:
        base_score += 20
    
    # Cap the score
    final_score = min(850, max(300, base_score))
    
    # Determine credit band
    if final_score >= 750:
        credit_band = "AA"
    elif final_score >= 650:
        credit_band = "A"
    elif final_score >= 550:
        credit_band = "B"
    elif final_score >= 450:
        credit_band = "C"
    else:
        credit_band = "D"
    
    return ScoreResponse(
        customer_id=request.customer_id,
        score=final_score,
        credit_band=credit_band,
        scorecard_version="1.0",
        breakdown={
            "base_score": base_score,
            "income_adjustment": final_score - base_score,
            "final_score": final_score
        }
    )
EOF
        print_success "Scorecard service main.py created"
    fi
    
    if [ ! -f "scorecard-service/requirements.txt" ]; then
        cat > scorecard-service/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
EOF
        print_success "Scorecard service requirements.txt created"
    fi
    
    if [ ! -f "scorecard-service/Dockerfile" ]; then
        cat > scorecard-service/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
EOF
        print_success "Scorecard service Dockerfile created"
    fi
}

# Create basic frontend structure
create_frontend_structure() {
    print_status "Creating basic frontend structure..."
    
    if [ ! -f "frontend/package.json" ]; then
        cat > frontend/package.json << 'EOF'
{
  "name": "microfinance-frontend",
  "version": "1.0.0",
  "description": "Microfinance Platform Frontend",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext .vue,.js,.ts --fix"
  },
  "dependencies": {
    "vue": "^3.3.8",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.2",
    "@headlessui/vue": "^1.7.16",
    "@heroicons/vue": "^2.0.18",
    "tailwindcss": "^3.3.6"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.2",
    "vite": "^5.0.8",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "eslint": "^8.55.0",
    "eslint-plugin-vue": "^9.19.2"
  }
}
EOF
        print_success "Frontend package.json created"
    fi
    
    if [ ! -f "frontend/Dockerfile" ]; then
        cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
EOF
        print_success "Frontend Dockerfile created"
    fi
    
    # Create basic Vue app structure
    mkdir -p frontend/src/components
    mkdir -p frontend/src/views
    mkdir -p frontend/src/stores
    mkdir -p frontend/src/router
    
    if [ ! -f "frontend/index.html" ]; then
        cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Microfinance Platform</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
EOF
        print_success "Frontend index.html created"
    fi
}

# Function to build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Build images
    print_status "Building Docker images..."
    docker-compose build
    
    # Start services
    print_status "Starting services..."
    docker-compose up -d
    
    print_success "Services started successfully!"
}

# Function to show service status
show_status() {
    print_status "Checking service status..."
    
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    
    echo ""
    echo "🌐 Service URLs:"
    echo "  • Backend API: http://localhost:8000"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • Frontend: http://localhost:3000"
    echo "  • Scorecard Service: http://localhost:8001"
    echo "  • PostgreSQL: localhost:5432"
    echo "  • Redis: localhost:6379"
    echo "  • pgAdmin: http://localhost:5050"
    echo "  • Redis Commander: http://localhost:8081"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • Grafana: http://localhost:3001"
    
    echo ""
    echo "🔑 Default Credentials:"
    echo "  • pgAdmin: admin@microfinance.com / admin123"
    echo "  • Grafana: admin / admin123"
    echo "  • Database: microfinance_user / microfinance_password"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    docker-compose exec backend alembic upgrade head || {
        print_warning "Migrations failed, creating initial migration..."
        docker-compose exec backend alembic revision --autogenerate -m "Initial migration"
        docker-compose exec backend alembic upgrade head
    }
    
    print_success "Database migrations completed"
}

# Main deployment function
main() {
    echo "🏦 Microfinance Platform Deployment Script"
    echo "=========================================="
    
    check_docker
    create_directories
    create_env_files
    create_monitoring_config
    create_scorecard_service
    create_frontend_structure
    start_services
    
    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 30
    
    run_migrations
    show_status
    
    echo ""
    print_success "🎉 Microfinance Platform deployed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Visit http://localhost:8000/docs to explore the API"
    echo "  2. Access the frontend at http://localhost:3000"
    echo "  3. Check pgAdmin at http://localhost:5050 for database management"
    echo "  4. Monitor services with Grafana at http://localhost:3001"
    echo ""
    echo "🛠️  Development Commands:"
    echo "  • Stop services: docker-compose down"
    echo "  • View logs: docker-compose logs -f [service-name]"
    echo "  • Restart service: docker-compose restart [service-name]"
    echo "  • Run migrations: docker-compose exec backend alembic upgrade head"
    echo ""
}

# Handle command line arguments
case "${1:-}" in
    "start")
        start_services
        show_status
        ;;
    "stop")
        print_status "Stopping services..."
        docker-compose down
        print_success "Services stopped"
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose down
        docker-compose up -d
        print_success "Services restarted"
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose logs -f "${2:-}"
        ;;
    "migrate")
        run_migrations
        ;;
    *)
        main
        ;;
esac