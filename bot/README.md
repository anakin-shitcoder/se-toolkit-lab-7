# SE Toolkit Telegram Bot

Telegram bot для взаимодействия с LMS (Learning Management System). Позволяет пользователям проверять статус системы, просматривать лабораторные работы и оценки, а также задавать вопросы на естественном языке.

## Возможности

### Команды

- `/start` — приветственное сообщение
- `/help` — список всех доступных команд
- `/health` — проверка статуса backend
- `/labs` — список доступных лабораторных работ
- `/scores <lab>` — проценты сдачи для заданий лаборатории

### Natural Language

Бот понимает запросы на естественном языке благодаря LLM:

- "какие есть лабораторные работы?"
- "покажи оценки для lab-04"
- "какая лаборатория имеет наименьший процент сдачи?"

## Быстрый старт

### Тестовый режим

Запуск без подключения к Telegram (для тестирования):

```bash
cd bot
uv sync
uv run bot.py --test "/start"
uv run bot.py --test "/health"
uv run bot.py --test "/labs"
uv run bot.py --test "/scores lab-04"
uv run bot.py --test "какие есть лабораторные работы?"
```

### Локальный запуск

1. Создайте `.env.bot.secret`:

```bash
cp .env.bot.example .env.bot.secret
# Отредактируйте и заполните реальными значениями
```

2. Запустите бота:

```bash
uv sync
uv run bot.py
```

## Развертывание (Deploy)

### Требования

- Docker и Docker Compose
- Запущенный LMS backend
- Telegram Bot Token (от @BotFather)
- LLM API (опционально, для natural language)

### Настройка переменных окружения

Создайте `.env.docker.secret` в корне проекта:

```bash
# Telegram Bot
BOT_TOKEN=your-telegram-bot-token

# LMS API
LMS_API_KEY=your-lms-api-key

# LLM API (опционально)
LLM_API_KEY=your-llm-api-key
LLM_API_BASE_URL=http://host.docker.internal:42005
LLM_API_MODEL=coder-model
```

### Запуск через Docker Compose

```bash
cd ~/se-toolkit-lab-7
docker compose --env-file .env.docker.secret up --build -d
```

### Проверка статуса

```bash
# Проверка что бот запущен
docker compose --env-file .env.docker.secret ps bot

# Просмотр логов
docker compose --env-file .env.docker.secret logs bot --tail 50
```

### Обновление

```bash
cd ~/se-toolkit-lab-7
git pull
docker compose --env-file .env.docker.secret up --build -d
```

## Архитектура

```
┌──────────────────┐     ┌──────────────────────────────────┐
│  Telegram User   │────▶│  Your Bot                        │
└──────────────────┘     │  (aiogram / python-telegram-bot) │
                         └──────┬───────────────────────────┘
                                │ slash commands + plain text
                                ├───────▶ /start, /help
                                ├───────▶ /health, /labs
                                ├───────▶ intent router ──▶ LLM
                                │                    │
                                │                    ▼
                         ┌──────┴───────┐    tools/actions
                         │  LMS Backend  │◀───── GET /items
                         │  (FastAPI)    │◀───── GET /analytics
                         └───────────────┘
```

## Структура проекта

```
bot/
├── bot.py              # Точка входа (Telegram + --test режим)
├── handlers/           # Обработчики команд (чистые функции)
│   ├── start.py        # /start handler
│   ├── help.py         # /help handler
│   ├── health.py       # /health handler
│   ├── labs.py         # /labs handler
│   ├── scores.py       # /scores handler
│   └── natural_language.py  # LLM routing
├── services/           # API клиенты
│   ├── lms_client.py   # LMS backend API client
│   └── llm_client.py   # LLM API client (9 tools)
├── config.py           # Загрузка конфигурации
├── pyproject.toml      # Зависимости
└── Dockerfile          # Docker образ
```

## Troubleshooting

### Бот не отвечает в Telegram

1. Проверьте логи: `docker compose logs bot`
2. Убедитесь что `BOT_TOKEN` правильный в `.env.docker.secret`
3. Проверьте что нет другого процесса бота: `ps aux | grep bot.py`

### Ошибка подключения к backend

- В Docker используйте `LMS_API_BASE_URL=http://backend:8000` (не localhost!)
- Убедитесь что backend запущен: `docker compose ps backend`

### LLM возвращает ошибку

- Токен Qwen OAuth истекает периодически. Restart: `cd ~/qwen-code-oai-proxy && docker compose restart`
- Проверьте доступность: `curl http://localhost:42005/v1/models`

## Разработка

### Добавление новой команды

1. Создайте handler в `handlers/my_command.py`
2. Добавьте экспорт в `handlers/__init__.py`
3. Зарегистрируйте в `bot.py`

### Тестирование

Используйте `--test` режим для быстрой проверки:

```bash
uv run bot.py --test "/mycommand arg1 arg2"
```

## Лицензия

MIT
