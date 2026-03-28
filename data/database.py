import sqlite3
import pandas as pd
import logging

logger = logging.getLogger(__name__)
DB_PATH = "stock_data.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    # """Creates all tables if they don't already exist."""
    conn = get_conn()
    cur = conn.cursor()

    # Table 1: S&P 500 company metadata
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            symbol       TEXT PRIMARY KEY,
            name         TEXT,
            sector       TEXT
        )
    """)

    # Table 2: Daily OHLCV prices for each company
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_prices (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol    TEXT    NOT NULL,
            date      TEXT    NOT NULL,
            open      REAL,
            high      REAL,
            low       REAL,
            close     REAL,
            adj_close REAL,
            volume    INTEGER,
            UNIQUE(symbol, date)
        )
    """)

    # Table 3: Technical Indicators
    cur.execute("""
        CREATE TABLE IF NOT EXISTS technical_indicators (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol    TEXT    NOT NULL,
            date      TEXT    NOT NULL,
            ma20      REAL,
            ma50      REAL,
            ma100     REAL,
            ma200     REAL,
            rsi14     REAL,
            UNIQUE(symbol, date)
    )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized with 3 tables: companies, daily_prices, technical_indicators.")


def clear_daily_prices():
    """Deletes all existing price records to start fresh."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM daily_prices")
    conn.commit()
    conn.close()
    logger.info("Cleared all existing daily price data.")


def insert_companies(df):
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for _, row in df.iterrows():
        cur.execute("""
            INSERT OR IGNORE INTO companies
                (symbol, name, sector)
            VALUES (?, ?, ?)
        """, (
            row.get("Symbol", ""),
            row.get("Security", ""),
            row.get("GICS Sector", ""),
        ))
        inserted += cur.rowcount
    conn.commit()
    conn.close()
    return inserted


def insert_daily_prices(symbol, hist_df):
    """
    Inserts yfinance history DataFrame rows into daily_prices.
    hist_df index is DatetimeIndex (date), columns: Open, High, Low, Close, Volume.
    """
    conn = get_conn()
    cur = conn.cursor()
    rows_added = 0

    for date, row in hist_df.iterrows():
        date_str = date.strftime("%Y-%m-%d")
        cur.execute("""
            INSERT OR IGNORE INTO daily_prices
                (symbol, date, open, high, low, close, adj_close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            date_str,
            round(float(row.get("Open",  0)), 4),
            round(float(row.get("High",  0)), 4),
            round(float(row.get("Low",   0)), 4),
            round(float(row.get("Close", 0)), 4),
            round(float(row.get("Close", 0)), 4),  # adj_close ≈ close for now
            int(row.get("Volume", 0)),
        ))
        rows_added += cur.rowcount

    conn.commit()
    conn.close()
    return rows_added


def insert_indicators(symbol, indicators_df):
    """
    Inserts calculated indicators into technical_indicators table.
    indicators_df index is date, columns: ma20, ma50, ma100, ma200, rsi14
    """
    conn = get_conn()
    cur = conn.cursor()

    for date, row in indicators_df.iterrows():
        date_str = date.strftime("%Y-%m-%d")
        cur.execute("""
            INSERT OR IGNORE INTO technical_indicators
                (symbol, date, ma20, ma50, ma100, ma200, rsi14)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            date_str,
            row.get("MA20"),
            row.get("MA50"),
            row.get("MA100"),
            row.get("MA200"),
            row.get("RSI14"),
        ))

    conn.commit()
    conn.close()


def get_all_symbols():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT symbol FROM companies ORDER BY symbol")
    symbols = [r[0] for r in cur.fetchall()]
    conn.close()
    return symbols


def get_price_history(symbol):
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM daily_prices WHERE symbol=? ORDER BY date",
        conn, params=(symbol,)
    )
    conn.close()
    return df


def get_last_n_prices(symbol, n=250):
    """
    Get the last N prices for a symbol from the database.
    Returns a DataFrame with columns needed for indicator calculation.
    """
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT date, open, high, low, close, volume FROM daily_prices WHERE symbol=? ORDER BY date DESC LIMIT ? ",
        conn, params=(symbol, n)
    )
    conn.close()
    
    if df.empty:
        return df
    
    # Reverse to get chronological order
    df = df.iloc[::-1].reset_index(drop=True)
    # Rename columns to match indicator calculation expectations (Open, High, Low, Close, Volume)
    df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    
    return df


def get_db_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM companies")
    companies = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM daily_prices")
    prices = cur.fetchone()[0]
    conn.close()
    return {"companies": companies, "daily_prices": prices}

def get_last_n_indicators(symbol, n=1):
    """
    Retrieves the most recent N indicator rows for a specific symbol.
    Used by daily_model_update.py to feed the latest data into the model.
    Returns DataFrame with columns: MA20, MA50, MA100, MA200, RSI14
    """
    conn = get_conn()
    query = """
        SELECT date, ma20, ma50, ma100, ma200, rsi14 
        FROM technical_indicators 
        WHERE symbol = ? 
        ORDER BY date DESC LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(symbol, n))
    conn.close()
    
    if df.empty:
        return df
    
    # Ensure proper data types for model prediction
    for col in ['ma20', 'ma50', 'ma100', 'ma200', 'rsi14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Standardize column names to uppercase for consistency with model.py
    df.columns = ['date', 'MA20', 'MA50', 'MA100', 'MA200', 'RSI14']
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort by date (chronological) and return
    return df.sort_values('date').reset_index(drop=True)


if __name__ == "__main__":
    init_db()
    print("[OK] Database initialized. Tables created.")
    print("Stats:", get_db_stats())

