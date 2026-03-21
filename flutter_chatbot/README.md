# Flutter Web Chatbot (Optional)

Эта задача является опциональной. Для её выполнения требуется установленный Flutter SDK.

## План реализации

### 1. Установка Flutter

```bash
# Скачать Flutter
cd /opt
git clone https://github.com/flutter/flutter.git -b stable
export PATH="$PATH:/opt/flutter/bin"

# Или через snap
sudo snap install flutter --classic
```

### 2. Создание проекта

```bash
cd ~/se-toolkit-lab-7
flutter create --platforms=web flutter_chatbot
cd flutter_chatbot
```

### 3. Структура проекта

```
flutter_chatbot/
├── lib/
│   ├── main.dart           # Точка входа
│   ├── chat_screen.dart    # UI чата
│   ├── llm_service.dart    # LLM API клиент
│   └── lms_service.dart    # LMS backend API клиент
├── web/
│   └── index.html
├── pubspec.yaml
└── ...
```

### 4. Зависимости (pubspec.yaml)

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  provider: ^6.0.0
  flutter_markdown: ^0.6.0
```

### 5. Интеграция с Caddy

Обновить `caddy/Caddyfile`:

```
handle_path /flutter* {
    root * /srv/flutter
    try_files {path} /index.html
    file_server
}
```

### 6. Сборка

```bash
cd flutter_chatbot
flutter build web --base-href /flutter/
```

### 7. Docker Compose

Добавить volume в сервис caddy:

```yaml
caddy:
  volumes:
    - ./caddy/Caddyfile:/etc/caddy/Caddyfile
    - ./flutter_chatbot/build/web:/srv/flutter
```

## Альтернатива без Flutter

Если Flutter недоступен, можно реализовать веб-чат на чистом HTML/JS:

1. Создать `frontend/chat.html` с простым UI
2. Добавить маршрут в Caddyfile
3. Использовать fetch() для API запросов

Это требует меньше зависимостей и проще в развертывании.
