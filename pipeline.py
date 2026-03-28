"""
pipeline.py
Data cleaning and preprocessing pipeline for stock price data.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def clean_price_data(hist_df, symbol):
    """
    Clean price data from yfinance.
    
    Args:
        hist_df: DataFrame from yfinance with OHLCV data
        symbol: Stock ticker symbol
    
    Returns:
        Cleaned DataFrame ready for database insertion
    """
    if hist_df.empty:
        logger.warning(f"{symbol}: Empty price history received.")
        return pd.DataFrame()
    
    try:
        df = hist_df.copy()
        
        # Ensure required columns exist
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"{symbol}: Missing required column '{col}'")
                return pd.DataFrame()
        
        # Handle missing values
        df = df.dropna(subset=['Close'])
        
        # Ensure data types
        for col in required_cols:
            if col != 'Volume':
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Remove rows with NaN in price columns
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
        
        # Ensure dates are in correct format
        if df.index.name == 'Date' or not df.index.name:
            df['Date'] = df.index
        
        # Reset index to make Date a column
        if 'Date' not in df.columns:
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'Date'}, inplace=True)
        
        logger.debug(f"{symbol}: Cleaned {len(df)} price records.")
        return df
        
    except Exception as e:
        logger.error(f"{symbol}: Error cleaning price data — {e}")
        return pd.DataFrame()
