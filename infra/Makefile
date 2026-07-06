.PHONY: up down build restart logs ps clean shell-backend shell-chatbot shell-comparison setup

setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from template — fill in your secrets then run: make up"; \
	else \
		echo ".env already exists"; \
	fi

up:
	docker compose up -d
	@echo ""
	@echo "All services starting..."
	@echo "  Frontend:    http://localhost"
	@echo "  Backend:     http://localhost:8000/docs"
	@echo "  Chatbot:     http://localhost:8001/docs"
	@echo "  Comparison:  http://localhost:8002/docs"
	@echo "  Prometheus:  http://localhost:9090"
	@echo "  Grafana:     http://localhost:3001 (admin/admin)"

up-logs:
	docker compose up

build:
	docker compose up -d --build

rebuild:
	docker compose up -d --build $(svc)

down:
	docker compose down

restart:
	docker compose restart $(svc)

ps:
	docker compose ps

logs:
	docker compose logs -f $(svc)

shell-backend:
	docker compose exec backend bash

shell-chatbot:
	docker compose exec chatbot bash

shell-comparison:
	docker compose exec comparison bash

shell-frontend:
	docker compose exec frontend sh

clean:
	docker compose down -v

nuke:
	docker compose down -v --rmi all --remove-orphans
	@echo "Everything removed"
