# price_spy-main/schemas.py

from pydantic import BaseModel
from datetime import date
from typing import Optional

# === продукты ===

class ProductBase(BaseModel):
    name: str

class ProductCreate(ProductBase):
    pass   # больше не просим sku у пользователя

class Product(ProductBase):
    id:  int
    sku: Optional[str] = None

    class Config:
        orm_mode = True

# === конкуренты ===

class Competitor(BaseModel):
    id:   int
    name: str

    class Config:
        orm_mode = True

# === цены ===

class PriceRecordCreate(BaseModel):
    product_id:    int
    competitor_id: int
    price:         float
    date:          date

class PriceRecord(PriceRecordCreate):
    id: int

    class Config:
        orm_mode = True
