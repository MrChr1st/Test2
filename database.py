import sqlite3


class Database:

    def __init__(self, path):
        self.path = path
        self.init()

    def init(self):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT
        )
        """)

        conn.commit()
        conn.close()