from dataclasses import dataclass
from typing import List
from fruit.models.fruit import Fruit
from fruit.models.fruit_type import FruitType

@dataclass
class FruitWithType:
    fruit: Fruit
    types: List[FruitType]