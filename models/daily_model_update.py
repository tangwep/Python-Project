import pandas as pd
import joblib
import logging
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data import database

# ─── Logging Setup ──────────────────────────────────────────────────
log_dir = os.path.join(os.path.dirname(__file__), '..', 'log_files')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_path = os.path.join(log_dir, "model_update.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

MODEL_PATH = "models/stock_model.pkl"


def generate_daily_predictions():
    """
    Load the trained model and generate predictions for all symbols.
    """
    try:
        # 1. Load the trained model
        if not os.path.exists(MODEL_PATH):
            logger.error(f"Model file not found: {MODEL_PATH}")
            return False
            
        model_data = joblib.load(MODEL_PATH)
        model = model_data['model']
        features = model_data['features']
        logger.info(f"Loaded model with features: {features}")
    except Exception as e:
        logger.error(f"Could not load model: {e}")
        return False

    # 2. Get all symbols we track
    symbols = database.get_all_symbols()
    if not symbols:
        logger.warning("No symbols found in database.")
        return False
    
    logger.info(f"Generating predictions for {len(symbols)} symbols...")
    
    predictions_count = 0
    failed_count = 0
    
    for symbol in symbols:
        try:
            # 3. Get the latest price and indicators
            price_data = database.get_last_n_prices(symbol, 20)  # Get 20-day window for vol calculation
            indicators_data = database.get_last_n_indicators(symbol, 1)
            
            if price_data.empty or indicators_data.empty:
                logger.warning(f"{symbol}: Missing price or indicator data.")
                failed_count += 1
                continue
            
            # Get the latest price row
            latest_price = price_data.iloc[-1]
            latest_indicators = indicators_data.iloc[-1]
            
            # 4. Calculate derived features (same as model training)
            close = latest_price['Close']
            open_ = latest_price['Open']
            volume = latest_price['Volume']
            
            ma20 = latest_indicators['MA20']
            ma50 = latest_indicators['MA50']
            ma100 = latest_indicators['MA100']
            ma200 = latest_indicators['MA200']
            rsi14 = latest_indicators['RSI14']
            
            # Handle NaN values
            if pd.isna([close, ma20, ma50, ma100, ma200, rsi14, volume]).any():
                logger.warning(f"{symbol}: Missing values in price/indicators.")
                failed_count += 1
                continue
            
            # Calculate distance from moving averages (normalized)
            dist_ma20 = (close - ma20) / ma20 if ma20 != 0 else 0
            dist_ma50 = (close - ma50) / ma50 if ma50 != 0 else 0
            dist_ma100 = (close - ma100) / ma100 if ma100 != 0 else 0
            dist_ma200 = (close - ma200) / ma200 if ma200 != 0 else 0
            
            # MA trend (short-term vs medium-term)
            ma_trend = (ma20 - ma100) / ma100 if ma100 != 0 else 0
            
            # Normalized volume (20-day average)
            avg_volume = price_data['Volume'].mean()
            vol_normalized = volume / avg_volume if avg_volume > 0 else 1
            
            # 5. Prepare features DataFrame for model prediction
            feature_dict = {
                'dist_ma20': dist_ma20,
                'dist_ma50': dist_ma50,
                'dist_ma100': dist_ma100,
                'dist_ma200': dist_ma200,
                'rsi14': rsi14,
                'ma_trend': ma_trend,
                'vol_normalized': vol_normalized
            }
            
            X = pd.DataFrame([feature_dict])[features]
            
            # 6. Make the prediction
            prediction = model.predict(X)[0]
            confidence = float(max(model.predict_proba(X)[0]) * 100)
            
            # 7. Log prediction (predictions computed on-demand, not stored)
            logger.info(f"{symbol}: Prediction={prediction}, Confidence={confidence:.1f}%")
            predictions_count += 1
            
        except Exception as e:
            logger.error(f"{symbol}: Error generating prediction - {e}")
            failed_count += 1
            continue
    
    logger.info(f"=" * 60)
    logger.info(f"Predictions completed:")
    logger.info(f"  [OK] Generated: {predictions_count}/{len(symbols)}")
    logger.info(f"  [ERROR] Failed: {failed_count}")
    logger.info(f"=" * 60)
    
    return predictions_count > 0


if __name__ == "__main__":
    generate_daily_predictions()