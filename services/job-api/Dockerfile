FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/libs/platform-common/src:/app/services/job-api/src

WORKDIR /app

COPY libs/platform-common ./libs/platform-common
COPY services/job-api/requirements.txt ./services/job-api/requirements.txt
RUN pip install --no-cache-dir -r services/job-api/requirements.txt

COPY services/job-api ./services/job-api

EXPOSE 8000
CMD ["uvicorn", "job_api_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

