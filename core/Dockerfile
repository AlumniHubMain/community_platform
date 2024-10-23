FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /comm_platform

RUN apt update && \
    apt install -y --no-install-recommends \
        postgresql \
        libpq-dev \
        build-essential \
        gcc \
        curl \
        && \
    rm -rf /var/lib/apt/lists/*;

COPY requirements.txt ./

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY app/ app/

EXPOSE 9000

RUN adduser --disabled-password apicore
USER apicore

CMD ["flask", "--app", "app", "run", "-p", "9000", "--host", "0.0.0.0"]
