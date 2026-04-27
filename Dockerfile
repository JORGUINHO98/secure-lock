FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

# Evitar errores en build
ENV SECRET_KEY=dummy
RUN python manage.py collectstatic --noinput || true

RUN adduser --disabled-password appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "secure_lock.asgi:application", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3"]