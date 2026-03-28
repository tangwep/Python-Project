import schedule
import time
import subprocess
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# ─── Logging Setup ──────────────────────────────────────────────────
log_dir = os.path.join(os.path.dirname(__file__), 'log_files')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "schedular_log.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
VENV_PYTHON = str(PROJECT_ROOT / "pythonproject" / "Scripts" / "python.exe")

def run_daily_pipeline():

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("=" * 60)
    logger.info(f"[START] Daily Pipeline at {now}...")
    logger.info("=" * 60)

    try:
        # STEP 1: Sync Data (1-day incremental update)
        logger.info("step-1. fetch market data ....")
        sync_process = subprocess.run(
            [VENV_PYTHON, str(PROJECT_ROOT / "data" / "daily_data.py")],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        if sync_process.returncode != 0:
            logger.error(f"[ERROR] Data Sync Failed:\n{sync_process.stderr}")
            return  # Stop here if data is missing

        logger.info("[OK] Data update completed.")
        
        # STEP 2: Generate Predictions (Using existing model)
        logger.info("step-2: Generating trading signals...")
        predict_process = subprocess.run(
            [VENV_PYTHON, "-m", "models.daily_model_update"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if predict_process.returncode == 0:
            logger.info("[OK] Full Pipeline completed successfully.")
            # Print a snippet of the output to the console
            if predict_process.stdout:
                logger.info(f"Output: {predict_process.stdout[-300:]}")
        else:
            logger.error(f"[ERROR] Prediction Step Failed:\n{predict_process.stderr}")

    except subprocess.TimeoutExpired as e:
        logger.error(f"[ERROR] Pipeline timed out: {e}")
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error in pipeline: {e}")


# Run at 4 AM every day
TARGET_TIME = "04:00"

schedule.every().day.at(TARGET_TIME).do(run_daily_pipeline)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info(f"[INFO] SYSTEM ACTIVE: Waiting for {TARGET_TIME} daily.")
    # logger.info("[INFO] Keep this window open to automate your trading system.")
    logger.info("[INFO] Tasks scheduled:")
    logger.info("[INFO]   - 04:00 AM: Update daily stock data")
    logger.info("[INFO]   - 04:05 AM: Update ML model with new data")
    logger.info("=" * 60)

    # Simple countdown logic so you know it's not frozen
    while True:
        schedule.run_pending()
        # Check every 60 seconds to save CPU energy
        time.sleep(60)