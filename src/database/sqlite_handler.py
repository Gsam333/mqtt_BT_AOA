import sqlite3
from contextlib import closing

class SQLiteManager:
    def __init__(self, db_path='data.db'):
        self.conn = sqlite3.connect(db_path)
        
    def create_table(self):
        with closing(self.conn.cursor()) as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                            (id INTEGER PRIMARY KEY, timestamp DATETIME, value REAL)''')