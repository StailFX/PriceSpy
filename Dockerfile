# Dockerfile

FROM python:3.10-slim

# 1) Устанавливаем утилиты для добавления Google-Chrome
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      wget \
      gnupg2 \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2) Добавляем ключ и репозиторий Google-Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update

# 3) Устанавливаем сам Google-Chrome (последней версии)  
RUN apt-get install -y --no-install-recommends \
      google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 4) Указываем где ждать бинарник Chrome
ENV CHROME_BIN=/usr/bin/google-chrome-stable

# 5) Рабочая директория
WORKDIR /app

# 6) Устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7) Копируем код
COPY . .

# 8) Экспоним порт
EXPOSE 8000

# 9) Запуск Uvicorn (---reload можно убрать в продакшене)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
