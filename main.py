# price_spy-main/main.py

import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from databases import Database
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    select,
)
from pydantic import BaseModel
from contextlib import asynccontextmanager

# ----------------------------
# 1. Настройка базы данных
# ----------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
database = Database(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # для SQLite + многопоточности
)
metadata = MetaData()

products = Table(
    "products",
    metadata,
    Column("id",   Integer, primary_key=True),
    Column("name", String(length=255), nullable=False),
    Column("sku",  String(length=50), unique=True, nullable=True),
)

# Создаем таблицы, если их нет (не удаляем существующие данные)
metadata.create_all(engine)

# ----------------------------
# 2. Pydantic-схемы
# ----------------------------

class ProductCreate(BaseModel):
    name: str  # только имя товара

class Product(ProductCreate):
    id:  int
    sku: str | None = None

    model_config = {"from_attributes": True}

# ----------------------------
# 3. FastAPI + Lifespan
# ----------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(
    title="PriceSpy",
    description="Сервис мониторинга цен с Ozon",
    version="1.0.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory="templates")

# ----------------------------
# 4. Эндпоинты
# ----------------------------

@app.get("/", response_class=HTMLResponse, tags=["products"])
async def list_products(request: Request):
    """
    Список товаров с кнопками: добавить, удалить и обновить цены.
    """
    rows = await database.fetch_all(select(products))
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "products": rows}
    )

@app.get("/new", response_class=HTMLResponse, tags=["products"])
async def new_product_form(request: Request):
    """
    Форма создания нового товара (только name).
    """
    return templates.TemplateResponse("new_product.html", {"request": request})

@app.post("/new", response_class=HTMLResponse, tags=["products"])
async def handle_new_product(request: Request, name: str = Form(...)):
    """
    Сохраняет новый товар, только поле name.
    """
    query = products.insert().values(name=name)
    try:
        new_id = await database.execute(query)
    except Exception as exc:
        raise HTTPException(400, f"Ошибка сохранения товара: {exc}")

    row = await database.fetch_one(select(products).where(products.c.id == new_id))
    if not row:
        raise HTTPException(500, "Не удалось прочитать добавленный товар")

    return templates.TemplateResponse("confirm.html", {"request": request, "product": row})

@app.post("/delete/{product_id}", response_class=HTMLResponse, tags=["products"])
async def delete_product(request: Request, product_id: int):
    """
    Удаляет товар по ID и перенаправляет на список.
    """
    row = await database.fetch_one(select(products).where(products.c.id == product_id))
    if not row:
        raise HTTPException(404, "Товар не найден")
    await database.execute(products.delete().where(products.c.id == product_id))
    return RedirectResponse(url="/", status_code=303)

@app.post("/ozon/products/{product_id}/fetch", response_class=HTMLResponse, tags=["ozon"])
async def fetch_ozon_price_html(request: Request, product_id: int):
    from .crud import create_price_record_from_ozon
    try:
        await create_price_record_from_ozon(product_id)
    except HTTPException:
        pass
    return RedirectResponse(url="/", status_code=303)

@app.post("/ozon/products/fetch_all", response_class=HTMLResponse, tags=["ozon"])
async def fetch_ozon_all_html(request: Request):
    from .crud import fetch_all_ozon_prices

    await fetch_all_ozon_prices()
    return RedirectResponse(url="/", status_code=303)

# ----------------------------
# 5. Запуск приложения
# ----------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )
