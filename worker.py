# worker.py
import asyncio
import redis.asyncio as redis
from crud import create_price_record_from_ozon
from database import database

REDIS_URL = "redis://localhost:6379"

async def worker():
    r = redis.Redis.from_url(REDIS_URL)
    print("Redis worker запущен. Ожидаем задач...")

    while True:
        product_id = await r.lpop("price_tasks")  # Ждём задачу
        if product_id is None:
            await asyncio.sleep(1)  # Если нет задач — ждём
            continue

        print(f"Получена задача: product_id={product_id.decode()}")
        try:
            await database.connect()
            await create_price_record_from_ozon(int(product_id))
            print(f"✅ Обработано: product_id={product_id.decode()}")
        except Exception as e:
            print(f"❌ Ошибка при обработке {product_id.decode()}: {e}")
        finally:
            await database.disconnect()

if __name__ == "__main__":
    asyncio.run(worker())