FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/libs/platform-common/src:/app/services/worker/src

WORKDIR /app

COPY libs/platform-common ./libs/platform-common
COPY services/worker/requirements.txt ./services/worker/requirements.txt
RUN pip install --no-cache-dir -r services/worker/requirements.txt

COPY services/worker ./services/worker

EXPOSE 8080
CMD ["python", "-m", "worker_service.main"]

