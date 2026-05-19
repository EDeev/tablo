import base64
import json
import os
import tempfile
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

TYPE_COLOR_POOL = """
Доступные цвета для типов занятий (выбери наиболее подходящий для каждого типа):
  "blue"    — лекции, теоретические занятия
  "green"   — практики, семинары
  "yellow"  — лабораторные работы, практикумы
  "purple"  — семинары, коллоквиумы
  "orange"  — консультации, факультативы
  "red"     — экзамены, зачёты, контрольные
  "teal"    — проектная работа, курсовые
  "gray"    — прочее, не указано
"""

SYSTEM_PROMPT = """Ты — точный парсер расписания учебных занятий.
Тебе дадут картинку с расписанием. Твоя задача — извлечь ВСЕ занятия и вернуть ТОЛЬКО валидный JSON, без лишнего текста, пояснений и markdown.

═══════════════════════════════════════════════
ВАЖНО: ОДИН ПРЕДМЕТ — ОДИН ОБЪЕКТ В МАССИВЕ
═══════════════════════════════════════════════
Один и тот же предмет может встречаться в расписании много раз:
  — в разные дни недели
  — в разное время
  — с разными типами (Лекция, Практика, Лаб. работа)
  — в разные периоды дат
  — в разных аудиториях
  — у разных преподавателей

ВСЕ вхождения одного предмета должны быть объединены в ОДИН объект!

═══════════════════════════════════════════════
СТРУКТУРА ОТВЕТА
═══════════════════════════════════════════════
[
  {
    "subject": "Название предмета",
    "types": {
      "Тип занятия": {
        "color": "blue",
        "dates": {
          "ДД.ММ-ДД.ММ": [
            ["день", "ЧЧ:ММ-ЧЧ:ММ", "кабинет_или_null", "преподаватель_или_null"]
          ]
        }
      }
    }
  }
]

═══════════════════════════════════════════════
ПРАВИЛА
═══════════════════════════════════════════════
subject       — обязательно, точное название
types         — обязательно, словарь типов

  Ключ типа   — "Лекция", "Практика", "Лаб. работа" и т.п.
                Если тип не указан — "Не указано"

  color       — цвет типа из пула ниже, выбери по смыслу типа
""" + TYPE_COLOR_POOL + """
  Ключ дат    — формат "ДД.ММ-ДД.ММ", например "02.02-05.04"
                Месяцы: янв=01 фев=02 мар=03 апр=04 май=05 июн=06
                        июл=07 авг=08 сен=09 окт=10 ноя=11 дек=12
                Если период не указан — "Весь период"

  Строка слота:
    [0] день          — нижний регистр (понедельник, вторник...)
    [1] время         — "ЧЧ:ММ-ЧЧ:ММ"
    [2] кабинет       — строка или null
    [3] преподаватель — строка (несколько через запятую) или null

ВАЖНО: поле types изменилось — теперь каждый тип содержит объект с полями "color" и "dates" (вместо прямого словаря дат).
"""


def _encode_image(image_bytes: bytes, ext: str) -> tuple[str, str]:
    mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.webp': 'image/webp', '.bmp': 'image/bmp'}
    mime = mime_map.get(ext.lower(), 'image/jpeg')
    return base64.standard_b64encode(image_bytes).decode('utf-8'), mime


def _strip_markdown(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith('```'):
        lines = raw.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == '```' else len(lines)
        raw = '\n'.join(lines[1:end])
    return raw


def scan_image(image_bytes: bytes, ext: str, extra_prompt: str = '') -> list[dict]:
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_BASE_URL') or None,
    )
    model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    image_data, mime_type = _encode_image(image_bytes, ext)

    user_text = 'Извлеки расписание из этого изображения и верни JSON строго по инструкции.'
    if extra_prompt:
        user_text += f'\n\nДополнительные указания от пользователя: {extra_prompt}'

    response = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:{mime_type};base64,{image_data}',
                            'detail': 'high',
                        },
                    },
                    {'type': 'text', 'text': user_text},
                ],
            },
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content
    return json.loads(_strip_markdown(raw))
