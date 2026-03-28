"""
migrate_db.py
Adds the ma200 column to the technical_indicators table if it doesn't exist
"""
import sqlite3
import logging
import database

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = "stock_data.db"

def add_ma200_column():
    """Add MA200 column to technical_indicators if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        # Try to add the column
        cur.execute("ALTER TABLE technical_indicators ADD COLUMN ma200 REAL")
        conn.commit()
        logger.info("✅ Successfully added ma200 column to technical_indicators table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("ℹ️ ma200 column already exists")
        else:
            logger.error(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_ma200_column()
