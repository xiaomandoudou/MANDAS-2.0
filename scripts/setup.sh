#!/bin/bash


set -e

echo "🚀 Setting up MANDAS-2.0 Development Environment..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v poetry &> /dev/null; then
    echo "⚠️  Poetry is not installed. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "📝 Creating environment files..."
cp services/api-gateway/.env.example services/api-gateway/.env
cp services/agent-worker/.env.example services/agent-worker/.env
cp services/frontend/.env.example services/frontend/.env

echo "📦 Installing Python dependencies..."
cd services/api-gateway
poetry install
cd ../agent-worker
poetry install
cd ../..

echo "📦 Installing Node.js dependencies..."
cd services/frontend
npm install
cd ../..

echo "🐳 Starting infrastructure services..."
docker-compose -f docker-compose.dev.yml up -d postgres redis chromadb ollama

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "🔍 Checking service health..."
docker-compose -f docker-compose.dev.yml ps

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Start the API Gateway: make dev-api"
echo "2. Start the Agent Worker: make dev-worker"
echo "3. Start the Frontend: make dev-frontend"
echo ""
echo "📚 Or use Docker Compose:"
echo "   docker-compose up -d"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8080/docs"
echo "   Health Check: http://localhost:8080/health"
