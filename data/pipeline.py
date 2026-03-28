import pandas as pd
import logging

logger = logging.getLogger(__name__)

def clean_price_data(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Cleans raw yfinance historical data before saving to the database.
    
    Rules enforced:
    1. Removes any rows containing NaN (blank) values.
    2. Removes any rows where the trading Volume was 0 (market holiday/halt).
    """
    if df.empty:
        return df

    original_len = len(df)

    # Rule 1: Drop rows with NaN (missing data)
    df = df.dropna()

    # Rule 2: Drop days where Volume is 0 (except for the index, since sometimes index volume isn't tracked perfectly)
    if symbol != "^GSPC" and "Volume" in df.columns:
        df = df[df["Volume"] > 0]

    # Rule 3: Ensure data types and round to 4 decimals just in case
    for col in ["Open", "High", "Low", "Close"]:
        if col in df.columns:
            df[col] = df[col].astype(float).round(4)

    new_len = len(df)
    if new_len < original_len:
        logger.debug(f"{symbol}: Pipeline removed {original_len - new_len} invalid rows (NaNs or 0 Volume).")

    return df
