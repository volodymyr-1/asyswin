# AsysWin

**Система автоматизации рабочих процессов с AI-ассистентом**

AsysWin записывает действия пользователя, анализирует их через Google Gemini и генерирует Python-скрипты для автоматизации повторяющихся задач.

## Возможности

- **Запись действий** — захват нажатий клавиш и кликов мыши
- **AI-анализ** — определение цели и разбиение на подзадачи через Gemini
- **Автогенерация скриптов** — создание готовых Python-скриптов
- **Система предсказаний** — топ-3 наиболее вероятных сценария
- **Анимированный робот-ассистент** — визуальная обратная связь

## Установка

```bash
git clone <repository-url>
cd asyswin
pip install -r requirements.txt
```

## Настройка

### 1. API ключ Google Gemini

```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

Получить ключ: https://makersuite.google.com/app/apikey

### 2. Запуск

```bash
# Базовая версия
python main.py

# Улучшенная версия с анимациями
python main_enhanced.py
```

## Горячие клавиши

| Клавиша | Действие |
|---------|----------|
| F9 | Начать/остановить запись |
| F10 | Отправить на анализ |
| F11 | Показать предсказания |
| ESC | Выход |

## Архитектура

```
asyswin/
├── base_application.py      # Базовый класс приложения
├── base_assistant_widget.py  # Базовый UI виджет
├── action_recorder.py       # Запись действий
├── llm_analyzer.py          # AI провайдеры (Gemini, OpenAI, Groq, LM Studio)
├── script_generator.py       # Генерация скриптов
├── predictor.py              # Система предсказаний
├── script_manager.py         # Управление скриптами
├── robot_widget.py           # Анимированный робот
├── main.py                   # Базовая версия
├── main_enhanced.py          # Улучшенная версия
└── tests/                   # Unit-тесты
```

## AI Провайдеры

Система поддерживает несколько AI провайдеров:

| Провайдер | Описание | Требует |
|-----------|----------|---------|
| Gemini | Google Gemini (основной) | API ключ |
| OpenAI | GPT-4o | API ключ |
| Groq | Llama3 (бесплатный) | API ключ |
| LM Studio | Локальная модель | LM Studio |

## Тестирование

```bash
# Все тесты
pytest tests/

# Конкретный модуль
pytest tests/test_llm_analyzer.py -v
pytest tests/test_predictor.py -v
pytest tests/test_action_recorder.py -v
```

## Разработка

### Структура тестов

```python
# tests/test_llm_analyzer.py - 28 тестов
# tests/test_predictor.py - 14 тестов  
# tests/test_action_recorder.py - 18 тестов
```

### Добавление провайдера

```python
from llm_analyzer import create_provider

provider = create_provider("provider_name", api_key="key")
```

## Лицензия

MIT License

## Автор

AsysWin Team
