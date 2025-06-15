from fastapi import APIRouter
from crud import get_competitor, get_competitors, create_competitor
from schemas import CompetitorCreate, Competitor

router = APIRouter(prefix="/competitors", tags=["competitors"])

@router.get("/")
async def read_competitors(skip: int=0, limit: int=100):
    return await get_competitors(skip=skip, limit=limit)

@router.get("/{competitor_id}")
async def get_competitor(competitor_id: int):
    return await get_competitor(competitor_id)

@router.post("/", response_model=Competitor)
async def write_competitor(competitor: CompetitorCreate):
    return await create_competitor(competitor)