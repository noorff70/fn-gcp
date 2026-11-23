from fruit.services.fruit_service import FruitService
from fruit.models.fruit import Fruit
from fruit.models.fruit_type import FruitType
from fruit.models.fruit_with_type import FruitWithType

class FakeFruitRepository:
    def get_all_fruits(self):
        return [
            Fruit(1, "Banana"),
            Fruit(2, "Apple"),
        ]

    def get_fruits_with_types(self):
        return [
            FruitWithType(
                fruit=Fruit(1, "Banana"),
                types=[FruitType(4, "Organic")]
            ),
            FruitWithType(
                fruit=Fruit(2, "Apple"),
                types=[FruitType(1, "Gala")]
            ),
        ]


def test_service_sorting():
    service = FruitService(FakeFruitRepository())

    fruits = service.get_fruits_with_types()

    assert fruits[0].fruit.fruit_name == "Apple"
    assert fruits[1].fruit.fruit_name == "Banana"

