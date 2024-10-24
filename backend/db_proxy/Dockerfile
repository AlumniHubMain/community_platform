#---------------------------------------------------------------------------
# Dockefile to build Docker Image: backend PlatformSP, fastapi
#---------------------------------------------------------------------------

FROM python:3.13-slim

# COPY backend/db_proxy/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# WORKDIR "backend/db_proxy"
# CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
# RUN cd backend/db_proxy
CMD ["python", "-m", "uvicorn", "--host", "0.0.0.0", "--port", "8080", "main:app"]
