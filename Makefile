# NEXUS ATLAS — Makefile
# ─────────────────────────────────────────────────────────────
.PHONY: all up down build logs clean setup-env install-backend install-frontend dev-backend dev-frontend

# Start all services
up:
	docker-compose up -d

# Start with logs in foreground
up-logs:
	docker-compose up

# Stop all services
down:
	docker-compose down

# Rebuild images
build:
	docker-compose build --no-cache

# View logs
logs:
	docker-compose logs -f

backend-logs:
	docker-compose logs -f backend

frontend-logs:
	docker-compose logs -f frontend

# Setup environment
setup-env:
	@if not exist .env (copy .env.example .env && echo "✓ .env created — edit it before running")
	@if not exist frontend\.env (copy frontend\.env.example frontend\.env && echo "✓ frontend/.env created")

# Local dev (no Docker)
install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# Database
db-migrate:
	cd backend && alembic upgrade head

db-shell:
	docker-compose exec postgres psql -U nexus -d nexus_atlas

# Clean
clean:
	docker-compose down -v --remove-orphans
	rd /s /q scans reports logs 2>nul || true

# Status
status:
	docker-compose ps
