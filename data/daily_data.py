"""
daily_data.py
Script to be run daily by a task scheduler (e.g., cron or Windows Task Scheduler).
It fetches just 1 day of historical data for the S&P 500 Index and all tracked companies,
passes the data through pipeline.py to clean it (e.g., removing nan and 0 volume), 
and safely appends it to stock_data.db.
"""
import yfinance as yf
import pandas as pd
import time
import logging
import database
import pipeline
import indicators
import os

# this is for setting path 
# 1. Define the path to the log folder (stepping out of 'data' into 'log_files')
log_dir = os.path.join(os.path.dirname(__file__), '..', 'log_files')

# 2. Create the folder if it doesn't exist
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 3. Define the full path for the log file
log_path = os.path.join(log_dir, "daily_sync.log")

# ─── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PERIOD = "1d"  # Only the last 1 day of trading
DELAY = 0.4    # Pause between API requests

def download_index():
    """Download S&P 500 index (^GSPC) 1-day prices."""
    logger.info("Downloading S&P 500 Index (^GSPC) for today...")
    try:
        hist = yf.Ticker("^GSPC").history(period=PERIOD)
        if hist.empty:
            logger.warning("Index data is empty!")
            return
            
        hist = pipeline.clean_price_data(hist, "^GSPC")
        rows = database.insert_daily_prices("^GSPC", hist)
        logger.info(f"Index: inserted {rows} rows.")
    except Exception as e:
        logger.error(f"Failed to download index: {e}")

def update_all_stocks(symbols):
    """Loop through every symbol and pull the latest day."""
    total = len(symbols)
    success = 0
    failed = []

    for i, symbol in enumerate(symbols, 1):
        try:
            hist = yf.Ticker(symbol).history(period=PERIOD)

            if hist.empty:
                logger.warning(f"[{i}/{total}] {symbol}: empty response, skipping.")
                failed.append(symbol)
                continue

            # Pass raw data through the cleaning pipeline
            cleaned_hist = pipeline.clean_price_data(hist, symbol)
            
            # If the pipeline threw out everything (e.g. today was a holiday with 0 volume)
            if cleaned_hist.empty:
                logger.debug(f"[{i}/{total}] {symbol}: dropped by pipeline (0 volume/NaNs).")
                continue

            # Insert daily prices
            rows = database.insert_daily_prices(symbol, cleaned_hist)

            # Calculate and store indicators
            # NOTE: We need enough history for moving averages, so we might pull
            # more than just 1d when calculating indicators.
            # For now, let's pull 150 days to ensure enough data for MA100
            full_hist = yf.Ticker(symbol).history(period="150d")
            cleaned_full = pipeline.clean_price_data(full_hist, symbol)

            indicators_df = indicators.calculate_indicators(cleaned_full)
            # Only insert the latest record
            latest_indicators = indicators_df.tail(1)
            database.insert_indicators(symbol, latest_indicators)

            if rows > 0:
                logger.info(f"[{i}/{total}] {symbol}: inserted {rows} new rows + indicators.")
            success += 1

        except Exception as e:
            logger.error(f"[{i}/{total}] {symbol}: FAILED — {e}")
            failed.append(symbol)

        time.sleep(DELAY)

    return success, failed


def main():
    print("=" * 60)
    print("       S&P 500 Daily Data Sync Endpoint       ")
    print("=" * 60)

    # Note: We DO NOT clear the database. This script simply appends data today.
    
    # 1. Download index
    download_index()

    # 2. Extract Stock Targets from Database
    symbols = database.get_all_symbols()
    print(f"\n📥 Syncing latest day pricing for {len(symbols)} stocks...")
    
    # 3. Download & Clean & Database insert
    success, failed = update_all_stocks(symbols)

    print("\n" + "=" * 60)
    print("  Daily Sync Complete!")
    print(f"  ✅ Stocks updated    : {success}/{len(symbols)}")
    if failed:
        print(f"  ❌ Failed (or Empty) : {len(failed)}")
    print("=" * 60)


if __name__ == "__main__":
    main()

