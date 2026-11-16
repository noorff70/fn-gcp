from fastapi import APIRouter, Depends
from fruit.repositories.location_repository import SQLiteLocationRepository
from fruit.services.location_service import LocationService


router = APIRouter()

def get_service():
    repo = SQLiteLocationRepository("data/inventory.db")
    return LocationService(repo)

@router.get("/locations")
def get_locations(repo = Depends(get_service)):
    return repo.get_all_locations()

