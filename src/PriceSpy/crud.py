# crud.py
from datetime import datetime
from typing import List
from sqlalchemy import select
from fastapi import HTTPException
from database import database
from models import products, competitors, price_records
from schemas import ProductCreate, Product, CompetitorCreate, Competitor, PriceRecordCreate, PriceRecord


# ----------------------------
# CRUD для Products
# ----------------------------

async def create_product(prod_in: ProductCreate) -> Product:
    query = products.insert().values(**prod_in.model_dump())
    product_id = await database.execute(query)
    row = await database.fetch_one(products.select().where(products.c.id == product_id))
    return Product(**row)


async def get_product(product_id: int) -> Product:
    row = await database.fetch_one(products.select().where(products.c.id == product_id))
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**row)


async def get_products(skip: int = 0, limit: int = 100) -> list[Product]:
    rows = await database.fetch_all(products.select().offset(skip).limit(limit))
    return [Product(**r) for r in rows]


# ----------------------------
# CRUD для Competitors
# ----------------------------

async def create_competitor(comp_in: CompetitorCreate) -> Competitor:
    query = competitors.insert().values(**comp_in.model_dump())
    competitor_id = await database.execute(query)
    row = await database.fetch_one(competitors.select().where(competitors.c.id == competitor_id))
    return Competitor(**row)


async def get_competitor(competitor_id: int) -> Competitor:
    row = await database.fetch_one(competitors.select().where(competitors.c.id == competitor_id))
    if not row:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return Competitor(**row)


async def get_competitors(skip: int = 0, limit: int = 100) -> list[Competitor]:
    rows = await database.fetch_all(competitors.select().offset(skip).limit(limit))
    return [Competitor(**r) for r in rows]


# ----------------------------
# CRUD для PriceRecords
# ----------------------------

async def create_price_record(record_in: PriceRecordCreate) -> PriceRecord:
    # Проверяем существование товара и конкурента
    await get_product(record_in.product_id)
    await get_competitor(record_in.competitor_id)

    query = price_records.insert().values(**record_in.model_dump())
    record_id = await database.execute(query)
    row = await database.fetch_one(price_records.select().where(price_records.c.id == record_id))
    return PriceRecord(**row)


async def get_price_record(record_id: int) -> PriceRecord:
    row = await database.fetch_one(price_records.select().where(price_records.c.id == record_id))
    if not row:
        raise HTTPException(status_code=404, detail="Price record not found")
    return PriceRecord(**row)


async def get_price_records_by_product(product_id: int) -> List[PriceRecord]:
    # 1) Достаём все записи из price_records по продукту, сортируя по дате
    query = (
        select(price_records)
        .where(price_records.c.product_id == product_id)
        .order_by(price_records.c.date)
    )
    rows = await database.fetch_all(query)

    result: List[PriceRecord] = []
    for r in rows:
        # r — RowMapping, всегда содержит 'url'
        rdict = dict(r)

        # 2) Подтягиваем имя конкурента
        comp_row = await database.fetch_one(
            select(competitors.c.name).where(competitors.c.id == rdict["competitor_id"])
        )
        rdict["competitor_name"] = comp_row["name"]

        # 3) Превращаем в Pydantic-модель
        result.append(PriceRecord(**rdict))

    return result

# ----------------------------
# Интеграция с Ozon
# ----------------------------

def search_product_urls(query):
    from parsers.ozon_parser import init_driver, search_and_get_links
    driver = init_driver()
    try:
        result = search_and_get_links(driver, query)
        driver.quit()
        return result
    except Exception as e:
        driver.quit()
        raise e


def parse_ozon_product(url: str):
    from parsers.ozon_parser import init_driver, parse_product
    driver = init_driver()
    try:
        result = parse_product(driver, url)
        driver.quit()
        return result
    except Exception as e:
        driver.quit()
        raise e


async def create_price_record_from_ozon(product_id: int) -> PriceRecord:
    # 1) Берём товар
    prod = await database.fetch_one(
        products.select().where(products.c.id == product_id)
    )
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    name = prod["name"]

    # 2) Ищем URL и парсим страницу Оzon
    urls = search_product_urls(name)
    if not urls:
        raise HTTPException(status_code=500, detail="Ozon: item not found")
    product_url = urls[0]
    info = parse_ozon_product(product_url)
    price_str = info[3]
    price = float("".join(c for c in price_str if c.isdigit() or c == "."))

    # 3) Находим конкурента Ozon
    comp_row = await database.fetch_one(
        competitors.select().where(competitors.c.name == "Ozon")
    )
    if not comp_row:
        raise HTTPException(status_code=500, detail="Competitor 'Ozon' missing")
    competitor_id = comp_row["id"]
    competitor_name = comp_row["name"]

    # 4) Готовим новую запись
    rec_in = PriceRecordCreate(
        product_id=product_id,
        competitor_id=competitor_id,
        price=price,
        url=product_url,
        date=datetime.utcnow().date()
    )

    # 5) Вставляем в БД и возвращаем Pydantic-модель со всеми полями
    new_id = await database.execute(
        price_records.insert().values(**rec_in.model_dump())
    )

    return PriceRecord(
        id=new_id,
        **rec_in.model_dump(),
        competitor_name=competitor_name
    )


async def fetch_all_ozon_prices() -> list[PriceRecord]:
    prods = await database.fetch_all(products.select())
    return [await create_price_record_from_ozon(p["id"]) for p in prods]