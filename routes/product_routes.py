# price_spy-main/routes/product_routes.py

from fastapi import APIRouter
from typing import List
from ..crud import create_product, read_products
from ..schemas import Product, ProductCreate

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=Product)
async def add_product(product: ProductCreate):
    return await create_product(product)

@router.get("/", response_model=List[Product])
async def list_products():
    return await read_products()
