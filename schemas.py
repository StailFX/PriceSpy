from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    sku: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True

class CompetitorBase(BaseModel):
    name: str
    base_url: str

class CompetitorCreate(CompetitorBase):
    pass

class Competitor(CompetitorBase):
    id: int

    class Config:
        orm_mode = True

class PriceRecordBase(BaseModel):
    product_id: int
    competitor_id: int
    price: float
    date: str

class PriceRecordCreate(PriceRecordBase):
    pass

class PriceRecord(PriceRecordBase):
    id: int

    class Config:
        orm_mode = True