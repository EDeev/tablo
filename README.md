# Tablo

**Русский** · [English](README.en.md)

[![CI](https://github.com/EDeev/tablo/actions/workflows/ci.yml/badge.svg)](https://github.com/EDeev/tablo/actions/workflows/ci.yml)
[![Docker](https://github.com/EDeev/tablo/actions/workflows/docker.yml/badge.svg)](https://github.com/EDeev/tablo/actions/workflows/docker.yml)
[![Release](https://img.shields.io/github/v/release/EDeev/tablo)](https://github.com/EDeev/tablo/releases)

Веб-приложение для студентов: по фото расписания ИИ собирает редактируемое расписание, к каждому
предмету можно добавить трекеры успеваемости и поделиться всем по ссылке.

**Статус:** учебный проект (курсовая работа, 2026), завершён · работает на [tablo.deev.su](https://tablo.deev.su)

![Расписание на неделю и трекеры](docs/screenshots/schedule.png)

**Стек:** Python 3.12 · Flask · SQLAlchemy + Alembic · PostgreSQL · OpenAI-совместимый Vision API · Playwright · Jinja2 + vanilla JS

## Возможности

- Распознавание расписания по фото или скану
- Редактирование расписаний, предметов и занятий, периоды с переходом через Новый год
- 11 видов трекеров (посещаемость, оценки, дедлайны, серии дней и др.) на сетке с перетаскиванием
- Генерация трекера по описанию: «8 лабораторных и экзамен»
- Доступ по ссылке: просмотр, редактирование или копия как шаблон
- Объединение нескольких расписаний в одно: занятия одного предмета сводятся вместе
- Экспорт в JSON, CSV, PNG и версию для печати

## Быстрый старт

```bash
git clone https://github.com/EDeev/tablo.git && cd tablo
cp .env.example .env      # задайте SECRET_KEY и ключ ИИ-провайдера
docker compose up -d
```

Откройте `http://localhost:8000`. Compose поднимает приложение и PostgreSQL, миграции применяются
при старте. Готовый образ: `docker pull ghcr.io/edeev/tablo` или `docker pull dcr.deev.su/edeev/tablo`.

## Установка без Docker

Нужны Python 3.11+ и PostgreSQL.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium   # для экспорта в PNG
cp .env.example .env
flask --app run db upgrade
python run.py
```

## Конфигурация

| Переменная | Назначение |
|---|---|
| `SECRET_KEY` | подпись сессий Flask; без неё приложение не запустится |
| `DATABASE_URL` или `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | подключение к PostgreSQL |
| `OPENAI_API_KEY` | ключ ИИ-провайдера |
| `OPENAI_BASE_URL` | адрес OpenAI-совместимого API, если это не OpenAI |
| `OPENAI_MODEL` | модель для распознавания и трекеров, по умолчанию `gpt-4o` |

> [!IMPORTANT]
> Без `OPENAI_API_KEY` не работают распознавание расписаний и генерация трекеров. Всё остальное работает:
> расписание можно завести и править вручную.

## Как выглядит

| Мои расписания | Предмет и трекеры | Телефон |
|---|---|---|
| ![Мои расписания](docs/screenshots/profile.png) | ![Предмет и трекеры](docs/screenshots/subjects.png) | ![Телефон](docs/screenshots/mobile.png) |

## Как устроено

```mermaid
flowchart LR
    B[Браузер] --> F[Flask: auth · schedules · subjects · shares · export]
    F --> S[Сервисы: ai_scan · ai_metrics · merge · export]
    F --> P[(PostgreSQL)]
    S --> A[OpenAI-совместимый API]
    S --> C[Chromium через Playwright]
```

Подробности:

- [docs/architecture.md](docs/architecture.md) — структура, формат расписания, трекеры, права доступа
- [docs/deploy.md](docs/deploy.md) — Docker и устройство боевого сервера
- [docs/explanatory_note.pdf](docs/explanatory_note.pdf) — пояснительная записка к курсовой

## Развёртывание

[tablo.deev.su](https://tablo.deev.su) работает на VPS: gunicorn под systemd за nginx с сертификатом
Let's Encrypt, PostgreSQL — на отдельном сервере, ИИ — Timeweb Cloud AI. Docker-образ собирает GitHub
Actions на каждый тег `v*` и публикует в GitHub Packages и в реестр `dcr.deev.su`.

## Разработка

```bash
pip install -r requirements-dev.txt
export TEST_DATABASE_URL=postgresql://tablo:tablo@localhost:5432/tablo_test
ruff check . && pytest
```

Тесты идут на настоящем PostgreSQL: права доступа и экспорт, ссылки, вход и защита от открытого
редиректа, разбор периодов и времени, слияние расписаний. CI поднимает базу в сервис-контейнере и
выполняет то же самое на каждый push.

## Лицензия

Учебный проект (курсовая работа, Московский Политех, 2025/26). Код открыт для изучения, отдельной
лицензии нет.

## Автор

**Деев Егор Викторович** — [GitHub](https://github.com/EDeev) · [Telegram](https://t.me/DeevEgor) · [egor@deev.space](mailto:egor@deev.space)

---

<div align="center">
  <sub>⭐ Если проект оказался полезным, поставьте звёздочку на GitHub!</sub>
  <p><sub>Сделано с ❤️ — <a href="https://deev.space">deev.space</a></sub></p>
</div>
