import sqlite3
from fruit.repositories.fruit_repository import SQLiteFruitRepository
from fruit.models.fruit import Fruit
from fruit.models.fruit_type import FruitType
from fruit.models.fruit_with_type import FruitWithType

def create_test_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE fruit (
            fruit_id INTEGER PRIMARY KEY,
            fruit_name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE fruit_type (
            fruit_type_id INTEGER PRIMARY KEY,
            fruit_type_name TEXT NOT NULL,
            fruit_id INTEGER,
            FOREIGN KEY (fruit_id) REFERENCES fruit(fruit_id)
        )
    """)

    # Insert test data
    cursor.execute("INSERT INTO fruit VALUES (1, 'Apple')")
    cursor.execute("INSERT INTO fruit VALUES (2, 'Banana')")
    cursor.execute("INSERT INTO fruit VALUES (3, 'Orange')")

    cursor.execute("INSERT INTO fruit_type VALUES (1, 'Gala', 1)")
    cursor.execute("INSERT INTO fruit_type VALUES (2, 'Yellow Delicious', 1)")
    cursor.execute("INSERT INTO fruit_type VALUES (3, 'Red Delicious', 1)")
    cursor.execute("INSERT INTO fruit_type VALUES (4, 'Organic', 2)")
    cursor.execute("INSERT INTO fruit_type VALUES (5, 'Non-organic', 2)")

    conn.commit()
    return conn

def test_get_all_fruits():
    conn = create_test_db()
    repo = SQLiteFruitRepository(":memory:", connection=conn)
    repo._connect = lambda: conn  # override connection

    fruits = repo.get_all_fruits()

    assert len(fruits) == 3
    assert fruits[0].fruit_name == "Apple"

def test_get_fruits_with_types():
    conn = create_test_db()
    repo = SQLiteFruitRepository(":memory:", connection=conn)
    repo._connect = lambda: conn  # override connection

    fruits = repo.get_fruits_with_types()

    apple = next(f for f in fruits if f.fruit.fruit_name == "Apple")
    banana = next(f for f in fruits if f.fruit.fruit_name == "Banana")
    orange = next(f for f in fruits if f.fruit.fruit_name == "Orange")

    assert len(apple.types) == 3
    assert len(banana.types) == 2
    assert len(orange.types) == 0


