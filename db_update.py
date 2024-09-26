import sqlite3


def db_update():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к столбцам по имен
    conn.execute('ALTER TABLE room')