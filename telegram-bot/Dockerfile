FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /bot

COPY pyproject.toml poetry.lock ./
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ src/

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
