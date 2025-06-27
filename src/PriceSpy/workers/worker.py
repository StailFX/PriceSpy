# worker.py

import os
import asyncio
from redis.asyncio import Redis
from src.PriceSpy.crud import create_price_record_from_ozon

async def worker():
    # 1) Получаем URL Redis из переменных окружения (docker-compose.yml)
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    redis = Redis.from_url(redis_url)

    print(f"Redis worker запущен, соединение: {redis_url}")
    print("Ожидание задач в очереди 'price_tasks'...")

    try:
        while True:
            # 2) Пытаемся взять ID товара из списка
            task = await redis.lpop("price_tasks")
            if task is None:
                # 3) Если задач нет — ждём немного
                await asyncio.sleep(1)
                continue

            try:
                product_id = int(task)
            except ValueError:
                print(f"Неверный формат задачи в очереди: {task!r}")
                continue

            print(f"Получена задача: обновить цену товара ID={product_id}")
            try:
                # 4) Вызываем ваш CRUD-метод для парсинга и записи цены
                rec = await create_price_record_from_ozon(product_id)
                print(f"Успешно сохранена запись ID={rec.id} для товара {product_id}")
            except Exception as e:
                print(f"Ошибка при обработке товара {product_id}: {e}")
    finally:
        # 5) При завершении корректно закрываем соединение с Redis
        await redis.close()
        await redis.connection_pool.disconnect()

if __name__ == "__main__":
    # Запускаем асинхронно воркер
    asyncio.run(worker())
