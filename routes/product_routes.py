from fastapi import APIRouter
from crud import get_product, get_products, create_product
from schemas import ProductCreate, Product

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/")
async def read_products(skip: int=0, limit: int=100):
    return await get_products(skip=skip, limit=limit)

@router.get("/{product_id}")
async def read_product(product_id: int):
    return await get_product(product_id)

@router.post("/", response_model=Product)
async def write_product(product: ProductCreate):
    return await create_product(product)