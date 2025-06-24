# syntax=docker/dockerfile:1

# 1) Берём официальный лёгкий образ Python 3.10
FROM python:3.10-slim

# 2) Устанавливаем системные пакеты, нужные для bcrypt и SQLite
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libffi-dev \
      libssl-dev \
      sqlite3 \
 && rm -rf /var/lib/apt/lists/*

# 3) Создаём рабочую директорию
WORKDIR /app

# 4) Копируем зависимости и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) Копируем весь код приложения
COPY . .

# 6) Открываем порт, на котором будет слушать Uvicorn
EXPOSE 8000

# 7) По умолчанию запускаем ваш FastAPI через Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
