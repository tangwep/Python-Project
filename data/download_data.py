"""
download_data.py
One-time script to:
  1. Fetch the full S&P 500 company list from Wikipedia
  2. Store company metadata in the database
  3. Download 10 years of historical prices for every stock
  4. Download 10 years of S&P 500 index (^GSPC) data
  5. Store everything in SQLite
"""
import yfinance as yf
import pandas as pd
import time
import logging
import database
import pipeline
import indicators
import os
from company_names import fetch_sp500_list

# this is for setting path 
# 1. Define the path to the log folder (stepping out of 'data' into 'log_files')
log_dir = os.path.join(os.path.dirname(__file__), '..', 'log_files')

# 2. Create the folder if it doesn't exist
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 3. Define the full path for the log file
log_path = os.path.join(log_dir, "download.log")


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

PERIOD = "10y"
DELAY  = 0.4   # seconds between API calls 


def download_index():
    """Download S&P 500 index (^GSPC) historical prices."""
    logger.info("Downloading S&P 500 Index (^GSPC)...")
    try:
        hist = yf.Ticker("^GSPC").history(period=PERIOD)
        if hist.empty:
            logger.warning("Index data is empty!")
            return
        rows = database.insert_daily_prices("^GSPC", hist)
        logger.info(f"Index: inserted {rows} rows ({len(hist)} trading days).")
    except Exception as e:
        logger.error(f"Failed to download index: {e}")


def download_all_stocks(symbols):
    """Loop through every symbol and download 10 years of daily price data."""
    total   = len(symbols)
    success = 0
    failed  = []

    for i, symbol in enumerate(symbols, 1):
        try:
            hist = yf.Ticker(symbol).history(period=PERIOD)

            if hist.empty:
                logger.warning(f"[{i}/{total}] {symbol}: empty response, skipping.")
                failed.append(symbol)
                continue

            # Apply cleaning pipeline
            cleaned_hist = pipeline.clean_price_data(hist, symbol)
            if cleaned_hist.empty:
                logger.warning(f"[{i}/{total}] {symbol}: empty after pipeline, skipping.")
                continue

            # Insert daily prices
            database.insert_daily_prices(symbol, cleaned_hist)

            # Calculate and store indicators
            indicators_df = indicators.calculate_indicators(cleaned_hist)
            database.insert_indicators(symbol, indicators_df)
            logger.info(f"[{i}/{total}] {symbol}: {len(cleaned_hist)} days → inserted data + indicators.")
            success += 1

        except Exception as e:
            logger.error(f"[{i}/{total}] {symbol}: FAILED — {e}")
            failed.append(symbol)

        time.sleep(DELAY)

    return success, failed


def main():
    print("=" * 60)
    print("  S&P 500 Historical Data Downloader")
    print("  Period: 10 years | Storage: SQLite (stock_data.db)")
    print("=" * 60)

    # Step 1: Initialize DB (just in case)
    database.init_db()

    # Step 1.5: Fetch and store S&P 500 company list
    print("\n[COMPANIES] Fetching S&P 500 company list from Wikipedia...")
    try:
        sp500_df = fetch_sp500_list()
        inserted = database.insert_companies(sp500_df)
        print(f"[OK] {inserted} companies stored in database.")
    except Exception as e:
        logger.error(f"Failed to fetch company list: {e}")
        print(f"[ERROR] Could not fetch companies: {e}")
        return

    # Step 2: Download index data
    print("\n[INDEX] Downloading S&P 500 Index data...")
    download_index()

    # Step 3: Download individual stocks
    symbols = database.get_all_symbols()
    print(f"\n[DOWNLOAD] Downloading price history for {len(symbols)} stocks...")
    print("   (This will take ~10-15 minutes for full S&P 500. Progress logged below)\n")

    success, failed = download_all_stocks(symbols)

    # Step 4: Summary
    stats = database.get_db_stats()
    print("\n" + "=" * 60)
    print("  Download Complete!")
    print(f"  [OK] Stocks downloaded : {success}/{len(symbols)}")
    print(f"  [FAILED] Failed            : {len(failed)} {failed if failed else ''}")
    print(f"  [TOTAL] Total price rows  : {stats['daily_prices']:,}")
    print("=" * 60)


if __name__ == "__main__":
    main()

