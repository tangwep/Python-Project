import pandas as pd
import logging
from data import database

#Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def fetch_sp500_list():
    """Scrape the full S&P 500 company list from Wikipedia."""
    logger.info("Fetching S&P 500 company list from Wikipedia...")
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    
    # Provide a User-Agent to avoid Wikipedia returning a 403 Forbidden error
    storage_options = {'User-Agent': 'Mozilla/5.0'}
    tables = pd.read_html(url, storage_options=storage_options)
    
    df = tables[0]   # first table = current S&P 500 constituents
    df = df.rename(columns={"Ticker": "Symbol"})  # normalize column name
    logger.info(f"Found {len(df)} companies in S&P 500.")
    return df


def main():
    print("=" * 60)
    print("  S&P 500 Companies Extractor")
    print("  Storage: SQLite (stock_data.db)")
    print("=" * 60)

    # Step 1: Initialize DB
    database.init_db()

    # Step 2: Fetch & store company list
    sp500_df = fetch_sp500_list()
    inserted = database.insert_companies(sp500_df)
    
    print(f"\n✅ Companies successfully stored in DB: {inserted} new entries")
    print(f"   Total companies now in DB: {database.get_db_stats()['companies']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
