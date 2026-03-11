up:
	docker compose up -d

build:
	docker compose build

build-up: build up

down:
	docker compose down

down-volumes:
	docker compose down -v

init:
	docker compose up airflow-init

logs:
	docker compose logs -f

flower-up:
	docker compose --profile flower up -d

debug:
	docker compose --profile debug run --rm airflow-cli

ps:
	docker compose ps
