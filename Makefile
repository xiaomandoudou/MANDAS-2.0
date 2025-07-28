.PHONY: help build up down logs clean test lint format

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs for all services
	docker-compose logs -f

clean: ## Clean up Docker containers, images, and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f

test: ## Run tests
	@echo "Running tests..."
	cd services/api-gateway && poetry run pytest
	cd services/agent-worker && poetry run pytest

lint: ## Run linting
	@echo "Running linting..."
	cd services/api-gateway && poetry run black . && poetry run isort . && poetry run flake8 .
	cd services/agent-worker && poetry run black . && poetry run isort . && poetry run flake8 .
	cd services/frontend && npm run lint

format: ## Format code
	@echo "Formatting code..."
	cd services/api-gateway && poetry run black . && poetry run isort .
	cd services/agent-worker && poetry run black . && poetry run isort .
	cd services/frontend && npm run format

dev-setup: ## Set up development environment
	@echo "Setting up development environment..."
	cp services/api-gateway/.env.example services/api-gateway/.env
	cp services/agent-worker/.env.example services/agent-worker/.env
	cp services/frontend/.env.example services/frontend/.env
	cd services/api-gateway && poetry install
	cd services/agent-worker && poetry install
	cd services/frontend && npm install

dev-api: ## Start API Gateway in development mode
	cd services/api-gateway && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

dev-worker: ## Start Agent Worker in development mode
	cd services/agent-worker && poetry run python -m app.main

dev-frontend: ## Start Frontend in development mode
	cd services/frontend && npm run dev

health: ## Check health of all services
	@echo "Checking service health..."
	curl -f http://localhost:8080/health || echo "API Gateway: DOWN"
	curl -f http://localhost:3000 || echo "Frontend: DOWN"
	docker-compose ps
