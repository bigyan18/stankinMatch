import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

def migrate():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # Check current columns
    cursor.execute('PRAGMA table_info(users)')
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'language' not in columns:
        logging.info("Adding 'language' column to 'users' table...")
        cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en'")
        conn.commit()
        logging.info("Column added successfully.")
    else:
        logging.info("'language' column already exists.")
        
    conn.close()

if __name__ == "__main__":
    migrate()
