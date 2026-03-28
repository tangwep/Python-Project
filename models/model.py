"""
model.py
Trains a machine learning model to predict Buy/Sell/Hold signals.
Uses all technical indicators to create a 5-level classification:
- Strong Sell (-2)
- Weak Sell (-1)  
- Hold (0)
- Weak Buy (1)
- Strong Buy (2)
"""
import pandas as pd
import numpy as np
import sqlite3
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
from data import database
import os

def get_training_data():
    """Combines prices and indicators to create a feature dataset with all MAs."""
    conn = database.get_conn()
    
    # Joining tables: using daily_prices and technical_indicators (including MA200)
    query = """
    SELECT 
        p.symbol, p.close, p.open, p.volume,
        i.ma20, i.ma50, i.ma100, i.ma200, i.rsi14
    FROM daily_prices p
    JOIN technical_indicators i ON p.symbol = i.symbol AND p.date = i.date
    WHERE i.ma200 IS NOT NULL
    ORDER BY p.symbol, p.date
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("⚠️ No training data available!")
        return df
    
    # Feature Engineering - Distance from Moving Averages (Normalized)
    df['dist_ma20'] = (df['close'] - df['ma20']) / df['ma20']
    df['dist_ma50'] = (df['close'] - df['ma50']) / df['ma50']
    df['dist_ma100'] = (df['close'] - df['ma100']) / df['ma100']
    df['dist_ma200'] = (df['close'] - df['ma200']) / df['ma200']
    
    # Additional features: price ratios and volume
    df['ma_trend'] = (df['ma20'] - df['ma100']) / df['ma100']
    df['vol_normalized'] = df['volume'] / df['volume'].rolling(20).mean()
    
    # Create 5-level target classification based on multi-indicator scoring
    df['target'] = create_target_labels(df)
    
    return df.dropna()

def create_target_labels(df):
    """
    Creates 5-level target labels based on technical indicator signals:
    -2: Strong Sell (multiple bearish signals)
    -1: Weak Sell (some bearish signals) 
     0: Hold (neutral signals)
     1: Weak Buy (some bullish signals)
     2: Strong Buy (multiple bullish signals)
    """
    targets = []
    
    for idx, row in df.iterrows():
        signal_score = 0
        
        # RSI Signal (0-40)
        if row['rsi14'] < 30:
            signal_score += 2  # Oversold - Bullish
        elif row['rsi14'] < 40:
            signal_score += 1
        elif row['rsi14'] > 70:
            signal_score -= 2  # Overbought - Bearish
        elif row['rsi14'] > 60:
            signal_score -= 1
        
        # Price vs MA20 Signal
        if row['close'] > row['ma20']:
            signal_score += 1
        else:
            signal_score -= 1
        
        # Price vs MA50 Signal
        if row['close'] > row['ma50']:
            signal_score += 1
        else:
            signal_score -= 1
        
        # Price vs MA100 Signal  
        if row['close'] > row['ma100']:
            signal_score += 1
        else:
            signal_score -= 1
        
        # Price vs MA200 Signal (Long-term trend)
        if row['close'] > row['ma200']:
            signal_score += 2
        else:
            signal_score -= 2
        
        # Moving Average Alignment (trend confirmation)
        if row['ma20'] > row['ma50'] > row['ma100'] > row['ma200']:
            signal_score += 2  # Strong uptrend
        elif row['ma20'] < row['ma50'] < row['ma100'] < row['ma200']:
            signal_score -= 2  # Strong downtrend
        
        # Map signal score to 5-level classification
        if signal_score >= 7:
            targets.append(2)  # Strong Buy
        elif signal_score >= 3:
            targets.append(1)  # Weak Buy
        elif signal_score <= -7:
            targets.append(-2)  # Strong Sell
        elif signal_score <= -3:
            targets.append(-1)  # Weak Sell
        else:
            targets.append(0)  # Hold
    
    return targets

def train_model():
    print("🔄 Loading training data with all indicators...")
    data = get_training_data()
    
    if data.empty:
        print("❌ No training data available!")
        return
    
    # Define features - all indicators plus engineered features
    features = ['dist_ma20', 'dist_ma50', 'dist_ma100', 'dist_ma200', 'rsi14', 'ma_trend', 'vol_normalized']
    X = data[features]
    y = data['target']
    
    print(f"📊 Training on {len(data)} data points")
    print(f"🎯 Target distribution:")
    print(y.value_counts().sort_index())
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train Random Forest with optimized parameters for 5-level classification
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'  # Handle class imbalance
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # this is for setting path 
    # 1. Define the path to the log folder (stepping out of 'data' into 'log_files')
    new_dir = os.path.join(os.path.dirname(__file__), '..', 'models')

    # 2. Create the folder if it doesn't exist
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)

    # 3. Define the full path for the log file
    pkl_path = os.path.join(new_dir, "stock_model.pkl")
    
    # Save model
    # Save model, features, and accuracy as a dictionary
    model_data = {
        'model': model,
        'features': features,  # This tells the predictor which columns to use
        'accuracy': accuracy
    }
    
    joblib.dump(model_data, pkl_path)
    
    print(f"\n✅ Model and features saved to {pkl_path}")
    print(f"\n✅ Model trained and saved as stock_model.pkl")
    print(f"📈 Test Accuracy: {accuracy:.4f}")
    print(f"\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Strong Sell', 'Weak Sell', 'Hold', 'Weak Buy', 'Strong Buy']))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n⭐ Feature Importance:")
    print(feature_importance.to_string(index=False))

if __name__ == "__main__":
    train_model()
