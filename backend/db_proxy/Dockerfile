#---------------------------------------------------------------------------
# Dockefile to build Docker Image: backend PlatformSP, fastapi
#---------------------------------------------------------------------------

FROM python:3.13-slim
COPY backend/db_proxy/requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
# CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
CMD ["python", "-m", "uvicorn", "--host", "0.0.0.0", "--port", "8080", "--config-file", "config_volume/.config", "main:app"]
