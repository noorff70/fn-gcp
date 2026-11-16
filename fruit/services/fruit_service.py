from typing import List
from fruit.repositories.fruit_interfaces import FruitRepository
from fruit.models.fruit import Fruit
from fruit.models.fruit_with_type import FruitWithType

class FruitService:
    def __init__(self, repo: FruitRepository):
        self.repo = repo

    def get_all_fruits(self) -> List[Fruit]:
        return self.repo.get_all_fruits()

    def get_fruits_with_types(self) -> List[FruitWithType]:
        fruits = self.repo.get_fruits_with_types()
        return sorted(fruits, key=lambda f: f.fruit.fruit_name)