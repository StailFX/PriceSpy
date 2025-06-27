# -------- Stage 1: Builder --------
  FROM python:3.10-slim-bookworm AS builder

  # Настройки окружения Python
  ENV PYTHONDONTWRITEBYTECODE=1 \
      PYTHONUNBUFFERED=1
  
  WORKDIR /app
  
  # Установим зависимости сначала отдельно, для кеширования слоя
  COPY requirements.txt /app/
  RUN pip install --no-cache-dir -r requirements.txt
  
  # Копируем весь код и шаблоны
  COPY src/PriceSpy        /app/PriceSpy
  COPY templates           /app/templates
  COPY .env.example        /app/.env.example
  
  # Запустим линтер и тесты в контейнере-сборщике
  # (предполагается, что в requirements.txt линтеры и pytest включены)
  RUN pip install --no-cache-dir black flake8 pytest \
      && black --check /app/PriceSpy \
      && flake8 /app/PriceSpy \
      && pytest --maxfail=1 --disable-warnings -q
  
  # -------- Stage 2: Runner --------
  FROM python:3.10-slim-bookworm
  
  ENV PYTHONDONTWRITEBYTECODE=1 \
      PYTHONUNBUFFERED=1
  
  WORKDIR /app
  
  # Копируем только то, что нужно для запуска
  COPY --from=builder /app/PriceSpy       /app/PriceSpy
  COPY --from=builder /app/templates      /app/templates
  COPY --from=builder /app/.env.example   /app/.env.example
  COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
  
  # Настроим переменные окружения (можно и декларативно через docker-compose)
  ENV REDIS_URL=redis://redis:6379
  # SECRET_KEY should be provided via a .env file or Docker secrets
  
  EXPOSE 8000
  
  # Запуск приложения
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  