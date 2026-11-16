from typing import List
from fruit.repositories.location_interface import LocationRepository
from fruit.models.location import Location

class LocationService:
    def __init__ (self, repo: LocationRepository):
        self.repo = repo

    def get_all_locations(self) -> List[Location]:
        return self.repo.get_all_locations()