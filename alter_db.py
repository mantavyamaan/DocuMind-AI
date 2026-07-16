import sqlite3

try:
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE history ADD COLUMN context TEXT")
    conn.commit()
    print("Column added successfully")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
