from contextlib import contextmanager
import sqlite3
from fruit.models.location import Location

class SQLiteLocationRepository:

    def __init__ (self, db_path:str, connection=None):
        self.db_path = db_path
        self.connection = connection


    def _get_cursor(self):
        if self.connection:
            conn = self.connection
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

        return conn, conn.cursor()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_all_locations(self):
        conn, cursor = self._get_cursor()
        cursor.execute('SELECT * FROM location')
        rows = cursor.fetchall()
        return [Location(location_id= row[0], location_name=row[1]) for row in rows]