## Setup
### Local Dev
#### MacOs & Linux Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
#### Setup venv
```bash
uv sync
```

#### Run tests
```bash
uv run pytest
```


## Docker
### Build 
```bash
cd ../../
docker build -f apps/web_gateway/Dockerfile -t community_platform_web_gateway:latest .
```
### Run service
```bash
docker run -v /path/to/local/config/directory:/config:rw -v /path/to/local/secrets/directory:/secrets:rw community_platform_web_gateway:latest
```

---
## Development
### Add new package
```bash
uv add package-name
```

## Подробнее про конфиги и секреты. Список

### Список конфигов(/config/*) требуемый сервисом:

#### db.json

Конфигурация базы данных. Включает в себя необходимую для коннекта к БД информацию. Шаблон:
```json
{
    "db_host": "",
    "db_port": 0,
    "db_name": "",
    "db_user": "",
    "db_pass": "",
    "db_schema": "alh_community_platform"
}
```

#### emitter_settings.json

Конфигурация хранящая информацию о политике работы event emitter. Шаблон:
```json
{
    "meetings_notification_target": "pubsub",
    "meetings_google_pubsub_notification_topic": "meetings_notifications"
}
```

#### environment

Описывает конфигурацию сервера: `development`/`production`.

#### limits.json

Содержит все настройки связанные с лимитированием действий пользователей. Шаблон:
```json
{
    "max_user_confirmed_meetings_count": 1,
    "max_user_pended_meetings_count": 1
}
```

#### s3.json

Содержит настройки необходимые для подключения к S3. Шаблон:
```json
{
     "bucket": "some_bucket_name"
}
```

#### secret_files.json

Указывает на расположение файлов с секретами(расположены в `/secrets`). Шаблон:
```json
{
    "access_secret_file": "/secrets/filename",
    "bot_token_file": "/secrets/filename"
}
```
