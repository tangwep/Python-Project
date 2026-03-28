"""Diagnose model file"""
import joblib
from pathlib import Path
import traceback

model_path = Path('models/stock_model.pkl')
print(f'Model exists: {model_path.exists()}')
print(f'File size: {model_path.stat().st_size} bytes')

try:
    model_data = joblib.load(model_path)
    print(f'Model loaded: {type(model_data)}')
    
    if isinstance(model_data, dict):
        print(f'Keys in model: {list(model_data.keys())}')
        if 'model' in model_data:
            print(f'Model type: {type(model_data["model"]).__name__}')
        if 'features' in model_data:
            print(f'Features: {model_data["features"]}')
    else:
        print(f'WARNING: Model is not a dict, it is: {type(model_data).__name__}')
        
except Exception as e:
    print(f'ERROR loading model: {e}')
    traceback.print_exc()
