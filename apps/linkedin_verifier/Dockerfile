# Используем официальный образ Python 3.12.7 slim как базовый
FROM python:3.12.7-slim

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копируем утилиту uv из официального образа
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Копируем общие пакеты из директории packages/ в контейнер
COPY packages/ /build/packages/

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /build/apps/linkedin_verifier/

# Копируем только файлы с зависимостями
COPY apps/linkedin_verifier/pyproject.toml apps/linkedin_verifier/uv.lock /build/apps/linkedin_verifier/

COPY config/ /build/config/

# Копируем все файлы приложения
COPY apps/linkedin_verifier/ /build/apps/linkedin_verifier/

# Устанавливаем зависимости с помощью uv sync
RUN uv sync --frozen

# # Устанавливаем переменные окружения
# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1

# Открываем порт 8000 для доступа к API
EXPOSE 8000

# Команда для запуска приложения
CMD ["/build/apps/linkedin_verifier/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 