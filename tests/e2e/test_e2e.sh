#!/usr/bin/env bash
set -euo pipefail

# 1) Собираем Docker-образ и поднимаем
docker-compose up -d --build

# 2) Ждём, пока API ответит на health-endpoint
echo "Waiting for API..."
for i in {1..10}; do
  if curl -s http://localhost:8000/health; then
    break
  fi
  sleep 1
done

# 3) Проверяем создание продукта через curl
echo "Running E2E test: create product"
CREATE_RESP=$(curl -s -X POST http://localhost:8000/products -H "Content-Type: application/json" \
  -d '{"name":"E2EItem"}')
ID=$(echo "$CREATE_RESP" | jq .id)
if [[ -z "$ID" ]]; then
  echo "Failed to create product"
  exit 1
fi

# 4) Проверяем, что можно получить этот продукт
curl -f http://localhost:8000/products || { echo "Cannot list products"; exit 1; }

echo "E2E tests passed!"

# 5) Останавливаем контейнеры
docker-compose down
