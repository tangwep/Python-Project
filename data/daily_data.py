"""
daily_data.py
Strictly fetches 1-day of data and uses local DB for indicator calculations.
"""
import yfinance as yf
import pandas as pd
import time
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports when run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

# --- Imports with fallback for both module and script execution ---
try:
    # Try relative imports (when imported as module)
    from . import database
    from . import indicators
except ImportError:
    # Fall back to direct imports (when run as script)
    import database
    import indicators

import pipeline 

# ─── Path Setup ──────────────────────────────────────────────────
log_dir = os.path.join(os.path.dirname(__file__), '..', 'log_files')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_path = os.path.join(log_dir, "daily_sync.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
PERIOD = "1d"  # Strictly 1 day from Yahoo Finance
LOOKBACK_REQUIRED = 250 # Days needed from LOCAL DB for MA200/RSI
DELAY = 0.5

def sync_symbol(symbol):
    try:
        # 1. Download ONLY 1 day from the internet
        hist = yf.Ticker(symbol).history(period=PERIOD)
        if hist.empty:
            return False

        # 2. Clean and Insert Price
        cleaned_today = pipeline.clean_price_data(hist, symbol)
        if cleaned_today.empty:
            return False
        
        database.insert_daily_prices(symbol, cleaned_today)

        # 3. Fetch LOOKBACK from LOCAL DATABASE (No internet used here)
        # We need previous data to calculate moving averages for today
        local_history = database.get_last_n_prices(symbol, LOOKBACK_REQUIRED)
        
        if len(local_history) < 200:
            logger.warning(f"{symbol}: Not enough local history for MA200.")
            return True # Price was saved, but indicators can't be calculated yet

        # 4. Calculate Indicators locally
        indicators_df = indicators.calculate_indicators(local_history)
        
        # 5. Insert only the latest indicator row
        latest_indicators = indicators_df.tail(1)
        database.insert_indicators(symbol, latest_indicators)

        return True

    except Exception as e:
        logger.error(f"{symbol}: Error — {e}")
        return False

def main():
    logger.info("Starting 1-Day Incremental Sync...")
    
    # Sync Index
    sync_symbol("^GSPC")

    # Sync Stocks
    symbols = database.get_all_symbols()
    for i, symbol in enumerate(symbols, 1):
        if sync_symbol(symbol):
            logger.info(f"[{i}/{len(symbols)}] {symbol}: Updated.")
        time.sleep(DELAY)

if __name__ == "__main__":
    main()