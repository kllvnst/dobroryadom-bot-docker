# ДоброРядом · Backend & Bot (Docker) + Frontend

Этот репозиторий содержит **бэкенд (FastAPI)** и **чат-бота (MAX)** для мини-приложения «ДоброРядом».  
Фронтенд развёрнут отдельно (Vercel), но в этом репозитории показан для демонстрации кода. 
Бэкенд написан и развёрнут через Docker и YC Serverless для доступа по внешним ссылкам и запросам. Контейнер  YC Serverless включает в себя доступ к базе данных PostgreSQL (не локальный).

## Состав репозитория

- `backend/` — код FastAPI, для обращения к данным из мини-приложения.
- `bot/` — код MAX-бота.
- `deploy/` — инфраструктура локального запуска MAX-бота:
  - `docker-compose.yml` — единая точка запуска,
  - `.env.example` — пример переменных окружения.
- `frontend_` - код мини-приложения (Next.js).
- `Dockerfile` — для сборки только bot.
- `requirements.txt` — общий список Python-зависимостей.
- `.gitignore`, `.dockerignore`.

## Требования

- Docker, Docker Desktop и Docker Compose.
- Git.
- Токен бота MAX (`BOT_MAX_TOKEN`).

## Быстрый старт

1) Клонируйте репозиторий и подготовьте окружение:
```bash
git clone --recurse-submodules https://github.com/kllvnst/dobroryadom-bot-docker.git
cd dobroryadom-bot-docker/deploy
cp .env.example .env
```

2) Откройте dobroryadom-bot-docker/deploy/.env и вставьте BOT_MAX_TOKEN.

3) Соберите и запустите бота из директории dobroryadom-bot-docker/deploy в терминале:
``` bash
docker compose build --no-cache bot
docker compose up -d bot
```
4) Просмотр логов о запуске:
``` bash
docker compose logs -f bot
```

5) Откройте чат-бот внутри MAX и начните общение.
