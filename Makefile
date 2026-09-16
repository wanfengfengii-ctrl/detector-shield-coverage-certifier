.PHONY: help up build verify down logs clean test-backend test-frontend test-e2e

help:
	@echo "目标："
	@echo "  make build      构建 api / web / verify 三个镜像"
	@echo "  make up         构建并启动 web 与 api（http://localhost:8080）"
	@echo "  make verify     运行 verify：pytest + Vitest + Playwright（一次性容器）"
	@echo "  make down       停止并清理"
	@echo "  make logs       跟踪日志"

build:
	docker compose build api web verify

up:
	docker compose up --build web api

verify:
	docker compose run --build --rm verify

down:
	docker compose down -v

logs:
	docker compose logs -f

clean:
	docker compose down -v --rmi local

# ---- 本地（无 Docker）----
test-backend:
	cd backend && python3 -m pytest

test-frontend:
	cd frontend && npx vitest run

test-e2e:
	cd frontend && BASE_URL=http://localhost:4173 npx playwright test
