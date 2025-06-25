from pydantic import BaseModel
from typing import Optional
from datetime import date

class ProductCreate(BaseModel):
    name: str
    sku: Optional[str] = None

class Product(ProductCreate):
    id: int
    class Config:
        from_attributes = True

class CompetitorCreate(BaseModel):
    name: str

class Competitor(CompetitorCreate):
    id: int
    class Config:
        from_attributes = True

class PriceRecordBase(BaseModel):
    product_id: int
    competitor_id: int
    price: float
    url: str                  # ← добавляем
    date: date

class PriceRecordCreate(PriceRecordBase):
    pass

class PriceRecord(BaseModel):
    id: int
    product_id: int
    competitor_id: int
    price: float
    url: str
    date: date
    competitor_name: str  # обязательное
    class Config:
        orm_mode = True