from database import database
from fastapi import HTTPException
import logging
from models import products, competitors, price_records
from schemas import ProductCreate, Product, CompetitorCreate, Competitor, PriceRecordCreate, PriceRecord
from typing import List

# --- PRODUCTS ---
async def get_product(product_id: int) -> Product:
    try:
        query = products.select().where(products.c.id == product_id)
        result = await database.fetch_one(query)
        if not result:
            raise HTTPException(status_code=404, detail="Товар не найден")
        return Product(**result)
    except Exception as e:
        logging.error(f"Ошибка при получении товара: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении товара")

async def get_products(skip: int = 0, limit: int = 100) -> List[Product]:
    try:
        query = products.select().offset(skip).limit(limit)
        results = await database.fetch_all(query)
        return [Product(**item) for item in results]
    except Exception as e:
        logging.error(f"Ошибка при получении списка товаров: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении списка товаров")

async def create_product(product: ProductCreate) -> Product:
    try:
        query = products.insert().values(**product.model_dump())
        last_record_id = await database.execute(query)
        return Product(**product.model_dump(), id=last_record_id)
    except Exception as e:
        logging.error(f"Ошибка при создании товара: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании товара")

# --- COMPETITORS ---
async def get_competitor(competitor_id: int) -> Competitor:
    try:
        query = competitors.select().where(competitors.c.id == competitor_id)
        result = await database.fetch_one(query)
        if not result:
            raise HTTPException(status_code=404, detail="Конкурент не найден")
        return Competitor(**result)
    except Exception as e:
        logging.error(f"Ошибка при получении конкурента: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении конкурента")

async def get_competitors(skip: int = 0, limit: int = 100) -> List[Competitor]:
    try:
        query = competitors.select().offset(skip).limit(limit)
        results = await database.fetch_all(query)
        return [Competitor(**item) for item in results]
    except Exception as e:
        logging.error(f"Ошибка при получении списка конкурентов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении списка конкурентов")

async def create_competitor(competitor: CompetitorCreate) -> Competitor:
    try:
        query = competitors.insert().values(**competitor.model_dump())
        last_record_id = await database.execute(query)
        return Competitor(**competitor.model_dump(), id=last_record_id)
    except Exception as e:
        logging.error(f"Ошибка при создании конкурента: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании конкурента")        

# --- PRICE RECORDS ---
async def get_price_records(product_id: int) -> List[PriceRecord]:
    try:
        query = price_records.select().where(price_records.c.product_id == product_id)
        results = await database.fetch_all(query)
        if not results:
            raise HTTPException(status_code=404, detail="Цены для этого товара не найдены")
        return [PriceRecord(**item) for item in results]
    except Exception as e:
        logging.error(f"Ошибка при получении истории цен: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении истории цен")

async def create_price_record(record: PriceRecordCreate) -> PriceRecord:
    try:
        query = price_records.insert().values(**record.model_dump())
        last_record_id = await database.execute(query)
        return PriceRecord(**record.model_dump(), id=last_record_id)
    except Exception as e:
        logging.error(f"Ошибка при сохранении цены: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении цены")    