import sqlite3

conn = sqlite3.connect('database.db')

conn.execute('''
CREATE TABLE users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT,
balance INTEGER,
rfid TEXT
)
''')

print("Database Created Successfully")

conn.close()