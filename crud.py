# price_spy-main/crud.py

from datetime import date
from fastapi import HTTPException

from .database import database
from .models import products, competitors, price_records
from .schemas import (
    ProductCreate, Product,
    CompetitorCreate, Competitor,
    PriceRecordCreate, PriceRecord
)

# ----------------------------
# Products CRUD
# ----------------------------

async def create_product(prod_in: ProductCreate) -> Product:
    ins = products.insert().values(name=prod_in.name)
    prod_id = await database.execute(ins)
    row = await database.fetch_one(products.select().where(products.c.id == prod_id))
    return Product(**row)

async def get_product(product_id: int) -> Product:
    row = await database.fetch_one(products.select().where(products.c.id == product_id))
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**row)

async def list_products() -> list[Product]:
    rows = await database.fetch_all(products.select())
    return [Product(**r) for r in rows]

async def update_product(product_id: int, prod_in: ProductCreate) -> Product:
    # Проверяем, что существует
    await get_product(product_id)
    upd = products.update().where(products.c.id == product_id).values(name=prod_in.name)
    await database.execute(upd)
    return await get_product(product_id)

async def delete_product(product_id: int) -> None:
    # Проверяем, что существует
    await get_product(product_id)
    await database.execute(products.delete().where(products.c.id == product_id))


# ----------------------------
# Competitors CRUD
# ----------------------------

async def create_competitor(comp_in: CompetitorCreate) -> Competitor:
    ins = competitors.insert().values(name=comp_in.name)
    comp_id = await database.execute(ins)
    row = await database.fetch_one(competitors.select().where(competitors.c.id == comp_id))
    return Competitor(**row)

async def get_competitor(comp_id: int) -> Competitor:
    row = await database.fetch_one(competitors.select().where(competitors.c.id == comp_id))
    if not row:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return Competitor(**row)

async def list_competitors() -> list[Competitor]:
    rows = await database.fetch_all(competitors.select())
    return [Competitor(**r) for r in rows]

async def update_competitor(comp_id: int, comp_in: CompetitorCreate) -> Competitor:
    await get_competitor(comp_id)
    upd = competitors.update().where(competitors.c.id == comp_id).values(name=comp_in.name)
    await database.execute(upd)
    return await get_competitor(comp_id)

async def delete_competitor(comp_id: int) -> None:
    await get_competitor(comp_id)
    await database.execute(competitors.delete().where(competitors.c.id == comp_id))


# ----------------------------
# PriceRecords CRUD
# ----------------------------

async def create_price_record(rec_in: PriceRecordCreate) -> PriceRecord:
    # Проверяем, что указанный товар и конкурент существуют
    await get_product(rec_in.product_id)
    await get_competitor(rec_in.competitor_id)

    ins = price_records.insert().values(**rec_in.model_dump())
    rec_id = await database.execute(ins)
    row = await database.fetch_one(price_records.select().where(price_records.c.id == rec_id))
    return PriceRecord(**row)

async def get_price_record(rec_id: int) -> PriceRecord:
    row = await database.fetch_one(price_records.select().where(price_records.c.id == rec_id))
    if not row:
        raise HTTPException(status_code=404, detail="Price record not found")
    return PriceRecord(**row)

async def list_price_records() -> list[PriceRecord]:
    rows = await database.fetch_all(price_records.select())
    return [PriceRecord(**r) for r in rows]

async def update_price_record(rec_id: int, rec_in: PriceRecordCreate) -> PriceRecord:
    # Проверяем существование
    await get_price_record(rec_id)
    # Обновляем
    upd = price_records.update().where(price_records.c.id == rec_id).values(**rec_in.model_dump())
    await database.execute(upd)
    return await get_price_record(rec_id)

async def delete_price_record(rec_id: int) -> None:
    await get_price_record(rec_id)
    await database.execute(price_records.delete().where(price_records.c.id == rec_id))


# ----------------------------
# OZON Integration
# ----------------------------

from .ozon_scraper import search_product_urls, parse_ozon_product

async def create_price_record_from_ozon(product_id: int) -> PriceRecord:
    """
    Автозапись цены с Ozon:
    1) Берём name из БД
    2) Ищем URL через search_product_urls
    3) Парсим через parse_ozon_product
    4) Берём competitor_id для Ozon
    5) Сохраняем в price_records
    """
    # 1) Получаем товар
    prod = await database.fetch_one(products.select().where(products.c.id == product_id))
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    name = prod["name"]

    # 2) Ищем URL
    urls = search_product_urls(name, max_results=1)
    if not urls:
        raise HTTPException(status_code=500, detail="Ozon: item not found")

    # 3) Парсим данные
    info = parse_ozon_product(urls[0])
    price = info.get("price")
    record_date = info.get("date") or date.today()
    if price is None:
        raise HTTPException(status_code=500, detail="Ozon: price parsing failed")

    # 4) Получаем competitor_id для Ozon
    comp = await database.fetch_one(
        competitors.select().where(competitors.c.name == "Ozon")
    )
    if not comp:
        raise HTTPException(status_code=500, detail="Competitor 'Ozon' missing")
    comp_id = comp["id"]

    # 5) Сохраняем запись
    rec_in = PriceRecordCreate(
        product_id=product_id,
        competitor_id=comp_id,
        price=price,
        date=record_date,
    )
    return await create_price_record(rec_in)


async def fetch_all_ozon_prices() -> list[PriceRecord]:
    """
    Создаёт новую запись цены для каждого продукта в базе
    """
    prods = await database.fetch_all(products.select())
    out = []
    for r in prods:
        rec = await create_price_record_from_ozon(r["id"])
        out.append(rec)
    return out
