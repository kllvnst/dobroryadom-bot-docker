# ДоброРядом · Backend & Bot (Docker)

Этот репозиторий содержит **бэкенд (FastAPI)** и **чат-бота (MAX)** для мини-приложения «ДоброРядом».  
Фронтенд развёрнут отдельно (Vercel) и в этот репозиторий не входит. 
Бэкенд написан и развёрнут через Docker и YC Serverless для доступа по внешним ссылкам и запросам. Контейнер  YC Serverless включает в себя доступ к базе данных PostgreSQL (не локальный).

## Состав репозитория

- `backend/` — код FastAPI, для обращения к данным из мини-приложения.
- `bot/` — код MAX-бота.
- `deploy/` — инфраструктура локального запуска MAX-бота:
  - `docker-compose.yml` — единая точка запуска,
  - `nginx.conf` — прокси к бэкенду (используется для локального бэкенда, но наш уже развернут внешне),
  - `.env.example` — пример переменных окружения.
- `frontend` - код мини-приложения (Next.js).
- `Dockerfile` — для сборки только bot.
- `requirements.txt` — общий список Python-зависимостей.
- `.gitignore`, `.dockerignore`.

## Требования

- Docker Desktop и Docker Compose.
- Токен бота MAX (`BOT_MAX_TOKEN`).

## Быстрый старт

1) Клонируйте репозиторий и подготовьте окружение:
```bash
git clone https://github.com/<YOUR_GH_USERNAME>/dobroryadom-bot-docker.git
cd max-bot/deploy
cp .env.example .env
```
2) Откройте max-bot/deploy/.env и вставьте BOT_MAX_TOKEN.

3) Соберите и запустите бота из директории max-bot/deploy в терминале:
``` bash
docker compose build --no-cache bot
docker compose up -d bot
```

4) Просмотр логов о запуске:
``` bash
docker compose logs -f bot
```

5) Откройте чат-бот внутри MAX и начните общение.
