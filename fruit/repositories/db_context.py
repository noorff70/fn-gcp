from contextlib import contextmanager
import sqlite3
# from fruit.models.fruit_with_type import FruitWithType
# from fruit.models.fruit_type import FruitType
# from fruit.models.fruit import Fruit
from fruit.repositories.interfaces import FruitRepository



@contextmanager
def db_cursor(db_path: str):
    pass
    # conn = sqlite3.connect(db_path)
    # conn.row_factory = sqlite3.Row
    # cursor = conn.cursor()
    # try:
    #     yield cursor
    #     conn.commit()
    # except Exception:
    #     conn.rollback()
    #     raise
    # finally:
    #     cursor.close()
    #     conn.close()