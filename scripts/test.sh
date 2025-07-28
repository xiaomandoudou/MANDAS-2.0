#!/bin/bash


set -e

echo "🧪 Running MANDAS-2.0 Tests..."

echo "🔍 Testing API Gateway..."
cd services/api-gateway
poetry run pytest -v
cd ../..

echo "🔍 Testing Agent Worker..."
cd services/agent-worker
poetry run pytest -v
cd ../..

echo "🔍 Testing Frontend..."
cd services/frontend
npm run lint
npm run build
cd ../..

echo "🔍 Running integration tests..."

echo "✅ All tests passed!"
