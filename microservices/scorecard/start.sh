#!/bin/bash

# Scorecard Microservice Startup Script

set -e

echo "🚀 Starting Scorecard Microservice..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if microfinance network exists, create if not
if ! docker network ls | grep -q microfinance_network; then
    echo "📡 Creating microfinance_network..."
    docker network create microfinance_network
fi

# Set default environment variables if not set
export SCORECARD_API_KEY=${SCORECARD_API_KEY:-"default_scorecard_key_2024"}
export ENVIRONMENT=${ENVIRONMENT:-"development"}

echo "🔧 Configuration:"
echo "   API Key: ${SCORECARD_API_KEY:0:10}..."
echo "   Environment: $ENVIRONMENT"

# Build and start the service
echo "🏗️  Building scorecard service..."
docker-compose build

echo "▶️  Starting scorecard service..."
docker-compose up -d

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 5

# Health check
echo "🏥 Performing health check..."
for i in {1..10}; do
    if curl -s http://localhost:8001/health > /dev/null; then
        echo "✅ Scorecard service is healthy!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Service health check failed after 10 attempts"
        docker-compose logs
        exit 1
    fi
    echo "   Attempt $i/10..."
    sleep 2
done

echo ""
echo "🎉 Scorecard Microservice is running!"
echo ""
echo "📊 Service Information:"
echo "   Health Check: http://localhost:8001/health"
echo "   API Docs: http://localhost:8001/docs"
echo "   Scoring Endpoint: http://localhost:8001/api/v1/score"
echo ""
echo "🧪 Run tests with:"
echo "   python test_api.py"
echo ""
echo "📋 View logs with:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop service with:"
echo "   docker-compose down"