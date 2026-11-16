from fastapi import APIRouter, Depends
from fruit.repositories.fruit_repository import SQLiteFruitRepository
from fruit.services.fruit_service import FruitService
import os
from fruit.config.settings import settings


router = APIRouter()

# DB_PATH = os.getenv(
#     "DB_PATH",
#     "./data/inventory.db"
# )

# def get_service():
#     repo = SQLiteFruitRepository(DATABASE_URL)
#     return FruitService(repo)

def get_service():
    repo = SQLiteFruitRepository(
        settings.DATABASE_URL
    )
    return FruitService(repo)

@router.get("/fruits")
def get_fruits(repo = Depends(get_service)):
    return repo.get_all_fruits()

@router.get("/fruits-with-types")
def get_fruits_with_types(repo = Depends(get_service)):
    return repo.get_fruits_with_types()
