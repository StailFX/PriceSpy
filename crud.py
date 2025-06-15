# price_spy-main/crud.py

from .database import database
from .models import products, price_records, competitors
from .schemas import ProductCreate, Product, PriceRecordCreate, PriceRecord
from fastapi import HTTPException

async def create_product(prod: ProductCreate) -> Product:
    """
    Создаёт новый продукт с заданным name.
    SKU остаётся NULL, его заполняет при парсинге ozon_scraper.
    """
    ins = products.insert().values(name=prod.name)
    prod_id = await database.execute(ins)
    row     = await database.fetch_one(products.select().where(products.c.id == prod_id))
    return Product(**row)

async def read_products() -> list[Product]:
    rows = await database.fetch_all(products.select())
    return [Product(**r) for r in rows]

# --- импорт ozon-интеграции ---

from .ozon_scraper import search_product_urls, parse_ozon_product

async def create_price_record_from_ozon(product_id: int) -> PriceRecord:
    # 1) Находим товар
    q    = products.select().where(products.c.id == product_id)
    prod = await database.fetch_one(q)
    if not prod:
        raise HTTPException(404, "Product not found")
    name = prod["name"]

    # 2) Ищем ссылку на Ozon
    urls = search_product_urls(name, max_results=1)
    if not urls:
        raise HTTPException(500, "Ozon: item not found")
    # 3) Парсим цену
    info = parse_ozon_product(urls[0])
    if info["price"] is None:
        raise HTTPException(500, "Ozon: price parsing failed")

    # 4) Берём competitor_id для Ozon
    comp = await database.fetch_one(
        competitors.select().where(competitors.c.name == "Ozon")
    )
    if not comp:
        raise HTTPException(500, "Competitor 'Ozon' missing")

    # 5) Сохраняем запись
    rec_in = PriceRecordCreate(
        product_id=product_id,
        competitor_id=comp["id"],
        price=info["price"],
        date=info["date"],
    )
    ins = price_records.insert().values(**rec_in.model_dump())
    rec_id = await database.execute(ins)
    return PriceRecord(id=rec_id, **rec_in.model_dump())

async def fetch_all_ozon_prices() -> list[PriceRecord]:
    rows = await database.fetch_all(products.select())
    out = []
    for r in rows:
        out.append(await create_price_record_from_ozon(r["id"]))
    return out
