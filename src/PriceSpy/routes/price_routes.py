from fastapi import APIRouter
from crud import get_price_records, create_price_record
from schemas import PriceRecordCreate, PriceRecord

router = APIRouter(prefix="/prices", tags=["prices"])

@router.get("/")
async def read_prices(product_id: int):
    return await get_price_records(product_id)

@router.post("/", response_model=PriceRecord)
async def write_price_record(record: PriceRecordCreate):
    return await create_price_record(record)