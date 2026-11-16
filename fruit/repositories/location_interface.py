from fruit.models.location import Location
from typing import Protocol


class LocationRepository(Protocol):

    def get_all_locations (self) -> list[Location]:
        ...