import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Схема всех типов метрик для AI
METRICS_SCHEMA_PROMPT = """Доступные типы метрик:

1. checkpoints — N независимых точек для отметки (лабы, задания, тесты)
   config: { "total": число, "labels": ["Лаба 1", ...] или null }

2. progress_bar — Накопление баллов/очков до максимума
   config: { "max": число, "unit": "баллов", "step": шаг_или_null }

3. counter — Простой счётчик до цели
   config: { "max": число, "step": 1, "unit": "единица" }

4. stages — Последовательные этапы работы
   config: { "stages": ["Тема", "План", "Черновик", "Защита"] }

5. checklist — Именованный список задач
   config: { "items": ["Задача 1", "Задача 2", ...] }

6. attendance — Отметки посещаемости (был/не был/уважительная)
   config: { "total_classes": число_или_null }

7. grades — Оценки за работы с весами и средним
   config: { "works": [{ "name": "Работа 1", "weight": 1 }], "max_grade": 5 }

8. deadlines — Задачи с датами дедлайнов
   config: { "items": [{ "name": "Задача", "date": "ДД.ММ" }] }

9. streak — Серия непрерывных дней активности
   config: {}

10. effort_hours — Учёт трудозатрат в часах
    config: { "goal_hours": число_или_null }

11. rating_history — История оценок в динамике
    config: { "scale": 5 }
"""


def generate_metric_from_prompt(subject_name: str, user_prompt: str) -> dict:
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_BASE_URL') or None,
    )
    model = os.getenv('OPENAI_MODEL', 'gpt-4o')

    system = (
        'Ты — помощник по созданию метрик успеваемости. '
        'Выбери подходящий тип метрики по описанию пользователя и верни ТОЛЬКО JSON без лишнего текста.\n\n'
        + METRICS_SCHEMA_PROMPT
        + '\nОтвет строго в формате: { "type": "тип", "label": "короткое название", "config": {...} }'
    )

    user_msg = (
        f'Предмет: {subject_name}\n'
        f'Описание от пользователя: {user_prompt}'
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user_msg},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith('```'):
        lines = raw.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == '```' else len(lines)
        raw = '\n'.join(lines[1:end])

    return json.loads(raw)
