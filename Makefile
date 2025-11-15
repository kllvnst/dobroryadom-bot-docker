.PHONY: up down logs

up:
	cd deploy && true && docker compose up -d --build

down:
	cd deploy && docker compose down -v

logs:
	cd deploy && docker compose logs -f --tail=200
