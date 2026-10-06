# Развёртывание

## Docker

```bash
cp .env.example .env    # SECRET_KEY и ключ ИИ-провайдера
docker compose up -d
```

Поднимаются приложение и PostgreSQL 16 (данные — в томе `pgdata`), миграции применяются при старте.
Готовый образ собирается GitHub Actions на каждый тег `v*`:

```bash
docker pull ghcr.io/edeev/tablo:latest
docker pull git.deev.su/edeev/tablo:latest
```

Образ большой (около 1,3 ГБ): в нём Chromium для экспорта расписания в PNG.

## Как работает tablo.deev.su

- gunicorn (2 воркера) под systemd за nginx с сертификатом Let's Encrypt;
- PostgreSQL — на отдельном сервере, подключение через `DB_*`;
- ИИ — Timeweb Cloud AI (OpenAI-совместимый endpoint), модель задаётся `OPENAI_MODEL`;
- обновление: выложить код, `pip install -r requirements.txt`, `flask db upgrade`, перезапуск юнита.
