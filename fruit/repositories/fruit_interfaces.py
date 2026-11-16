from typing import Protocol
from fruit.models.fruit_with_type import FruitWithType
from fruit.models.fruit import Fruit


# class FruitRepository(Protocol): This declares FruitRepository as an abstract interface. Any class that implements a get_all_fruits method with the matching signature is automatically considered a child of this protocol, without needing to explicitly inherit from it.
class FruitRepository(Protocol):
    # This specifies that the interface expects a method named get_all_fruits that takes no arguments (besides self) and returns a list of Fruit objects.
    def get_all_fruits(self) -> list[Fruit]:
        ...

    def get_fruits_with_types(self) -> list[FruitWithType]:
        ...
    # def get_fruit_by_id(self, fruit_id: int) -> dict | None:
    #     ...
