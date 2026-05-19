# Tablo

Веб-приложение для работы с учебным расписанием: распознавание расписания из изображения с помощью ИИ, персональные трекеры успеваемости и совместный доступ по ссылке.

Сайт: [tablo.deev.su](https://tablo.deev.su)

## Функциональность

- Загрузка фотографии или скана расписания и автоматическое извлечение структурированных данных через AI Vision API
- Полный CRUD для расписаний, предметов и слотов занятий
- 11 типов виджетов трекеров успеваемости (посещаемость, оценки, дедлайны, серии дней и др.)
- Дашборд с перетаскиваемыми виджетами на сетке 12 колонок
- Совместный доступ по токен-ссылке с тремя режимами: просмотр, редактирование, клонирование как шаблон
- Объединение нескольких расписаний с разрешением конфликтов по предметам

## Технологический стек

- **Backend:** Python, Flask, SQLAlchemy, Flask-Migrate, Flask-Login
- **База данных:** PostgreSQL (JSONB для хранения структуры расписания)
- **ИИ:** Gemini 3.1 Flash через OpenAI-совместимый API (Timeweb Cloud AI)
- **Frontend:** Jinja2, Bootstrap 5.3, Vanilla JS, Fetch API

## Установка

**Требования:** Python 3.11+, PostgreSQL

```bash
git clone https://github.com/EDeev/tablo.git
cd tablo
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:password@localhost:5432/tablo
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.your-provider.com/v1
```

Примените миграции и запустите приложение:

```bash
flask db upgrade
python run.py
```

Приложение будет доступно по адресу `http://localhost:5000`.

## Структура проекта

```
tablo/
├── app/
│   ├── models/       # Модели SQLAlchemy
│   ├── routes/       # Блюпринты (auth, schedules, subjects, shares)
│   ├── services/     # Бизнес-логика (AI-распознавание, AI-генерация метрик)
│   └── templates/    # HTML-шаблоны Jinja2
├── migrations/       # Файлы миграций Flask-Migrate
├── requirements.txt
└── run.py
```

## Лицензия

Этот проект является некоммерческим и распространяется под лицензией MIT.

## Автор

**Деев Егор Викторович** - Backend Developer  
- GitHub: [@EDeev](https://github.com/EDeev)
- Email: egor@deev.space
- Telegram: [@Egor_Deev](https://t.me/Egor_Deev)

---

<div align="center">
  <sub>⭐ Если проект оказался полезным, поставьте звездочку на GitHub!</sub>
  <p><sub>Создано с ❤️ от вашего дорогого - deev.space ©</sub></p>
</div>
