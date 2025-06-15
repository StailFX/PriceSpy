# main.py

import os
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
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

# Используем файл SQLite рядом с этим скриптом
DATABASE_URL = "sqlite:///./test.db"
database = Database(DATABASE_URL)

# Создаём SQLAlchemy-движок и метаданные
engine = create_engine(
    DATABASE_URL,
    # важно для SQLite + многопоточности
    connect_args={"check_same_thread": False},
)
metadata = MetaData()

# Описание таблицы "products"
products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(length=255), nullable=False),
    Column("sku", String(length=50), unique=True, nullable=False),
)

# Если базы нет — создадим файлик test.db и таблицу products
metadata.create_all(engine)


# ----------------------------
# 2. Pydantic-схемы (v2)
# ----------------------------

class ProductCreate(BaseModel):
    name: str
    sku: str


class Product(BaseModel):
    id: int
    name: str
    sku: str

    model_config = {
        # В Pydantic v2 вместо orm_mode=True используется from_attributes=True
        "from_attributes": True
    }


# ----------------------------
# 3. FastAPI + Lifespan
# ----------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте приложения подключаемся к базе
    await database.connect()
    try:
        yield
    finally:
        # При завершении — отключаемся
        await database.disconnect()

app = FastAPI(lifespan=lifespan)


# ----------------------------
# 4. Эндпоинты
# ----------------------------

@app.get("/", response_class=HTMLResponse)
async def show_form():
    """
    Возвращает простую HTML-страницу с формой для ввода 'name' и 'sku'.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Добавить товар</title>
    </head>
    <body>
        <h1>Добавить новый товар</h1>
        <form action="/" method="post">
            <label for="name">Название товара:</label><br>
            <input type="text" id="name" name="name" required><br><br>

            <label for="sku">SKU:</label><br>
            <input type="text" id="sku" name="sku" required><br><br>

            <button type="submit">Сохранить</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.post("/", response_class=HTMLResponse)
async def handle_form(name: str = Form(...), sku: str = Form(...)):
    """
    При отправке формы сохраняет 'name' и 'sku' в БД и отдаёт страницу с подтверждением.
    """
    # 1) Собираем данные в Pydantic-модель
    product_in = ProductCreate(name=name, sku=sku)

    # 2) Пытаемся добавить новый товар в БД
    query_insert = products.insert().values(
        name=product_in.name,
        sku=product_in.sku
    )
    try:
        new_id = await database.execute(query_insert)
    except Exception:
        # Чаще всего тут уникальный constraint на sku «сломался»
        raise HTTPException(
            status_code=400,
            detail="Невозможно сохранить товар: вероятно, такой SKU уже есть."
        )

    # 3) Получаем из БД только что вставленную запись по её id
    query_select = select(products).where(products.c.id == new_id)
    row = await database.fetch_one(query_select)
    if row is None:
        raise HTTPException(
            status_code=500, detail="Ошибка чтения данных из БД.")

    product = Product(**row)

    # 4) Формируем HTML-ответ с подтверждением
    html_resp = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Товар добавлен</title>
    </head>
    <body>
        <h1>Товар успешно добавлен!</h1>
        <p><strong>ID:</strong> {product.id}</p>
        <p><strong>Название:</strong> {product.name}</p>
        <p><strong>SKU:</strong> {product.sku}</p>
        <br>
        <a href="/">Добавить ещё один товар</a>
    </body>
    </html>
    """
    return HTMLResponse(content=html_resp, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",      # точка запуска: модуль main, переменная app
        host="127.0.0.1",
        port=8000,
        reload=True      # автоматически перезапускать при изменении кода
    )
