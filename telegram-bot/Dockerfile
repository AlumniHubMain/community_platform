FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV BOT_TOKEN="placeholder_do_not_use_real_token_here"
# Use docker run -d --name your_bot_container -e BOT_TOKEN="your_real_token" your_bot_image 
# to run locally

WORKDIR /bot

COPY pyproject.toml poetry.lock ./
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ src/

EXPOSE 8000

CMD ["python", "src/main.py"]
