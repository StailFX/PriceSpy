# price_spy-main/routes/ozon_routes.py

from fastapi import APIRouter
from typing import List
from ..crud import create_price_record_from_ozon, fetch_all_ozon_prices
from ..schemas import PriceRecord

router = APIRouter(prefix="/ozon", tags=["ozon"])

@router.post("/products/{product_id}/fetch", response_model=PriceRecord)
async def fetch_ozon_price(product_id: int):
    return await create_price_record_from_ozon(product_id)

@router.post("/products/fetch_all", response_model=List[PriceRecord])
async def fetch_ozon_all():
    return await fetch_all_ozon_prices()
