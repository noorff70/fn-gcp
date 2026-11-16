from contextlib import contextmanager
import sqlite3
from typing import List, Optional
from fruit.models.fruit_with_type import FruitWithType
from fruit.models.fruit_type import FruitType
from fruit.models.fruit import Fruit
# from fruit.repositories.fruit_interfaces import FruitRepository
# from fruit.repositories.db_context import db_cursor
import os

class SQLiteFruitRepository:

  
    def __init__(self, db_path:str, connection=None):
        """Pass the connection once when creating the repository."""
        self.db_path = db_path
        self.connection = connection

    def _get_cursor(self):
        if self.connection:
            conn = self.connection
        else:
            conn = sqlite3.connect(self.db_path)
            # This lets you access query results by column name (like a dictionary) instead of just numerical index tuples.
            conn.row_factory = sqlite3.Row

        return conn, conn.cursor()

    def _connect(self):
        return sqlite3.connect(self.db_path)


    def get_all_fruits(self):
        conn, cursor = self._get_cursor()
        cursor.execute("SELECT * FROM fruit")
        rows = cursor.fetchall()
        return [Fruit(fruit_id=row[0], fruit_name=row[1]) for row in rows]


    def get_fruits_with_types(self) -> list[FruitWithType]:
        # print("DB PATH:", os.path.abspath(self.db_path))
        conn, cursor = self._get_cursor()
        cursor.execute(""" 
            SELECT f.fruit_id, f.fruit_name,
                ft.fruit_type_id, ft.fruit_type_name
            FROM fruit f
            LEFT JOIN fruit_type ft
            ON f.fruit_id = ft.fruit_id
        """)
        rows = cursor.fetchall()

        # build dictionary: fruit_id -> FruitWithType
        fruits_map = {}

        for row in rows:
            # fruit_id, fruit_name, type_id, type_name = row
            # print("DEBUG:", dict(row))  # ← TEMPORARY DEBUG
            fruit_id = row["fruit_id"]
            fruit_name = row["fruit_name"]
            type_id = row["fruit_type_id"]
            type_name = row["fruit_type_name"]

            if fruit_id not in fruits_map:
                fruits_map[fruit_id] = FruitWithType (
                    fruit = Fruit(fruit_id= fruit_id, fruit_name=fruit_name),
                    types=[]
                )

            if type_id is not None:
                fruits_map[fruit_id].types.append(
                    FruitType(fruit_type_id=type_id, fruit_type_name=type_name)
                    )


        return list(fruits_map.values())


