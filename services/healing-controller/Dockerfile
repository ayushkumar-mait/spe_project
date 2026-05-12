FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/libs/platform-common/src:/app/services/healing-controller/src

WORKDIR /app

COPY libs/platform-common ./libs/platform-common
COPY services/healing-controller/requirements.txt ./services/healing-controller/requirements.txt
RUN pip install --no-cache-dir -r services/healing-controller/requirements.txt

COPY services/healing-controller ./services/healing-controller

CMD ["python", "-m", "healing_controller.main"]

