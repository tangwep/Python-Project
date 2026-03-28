#  Stock Analysis AI Dashboard

A real-time stock analysis system with AI-powered trading signal predictions for S&P 500 companies.

---

## 🎯 What Is This Project?

This is an **automated stock analysis platform** that:

1. **Downloads** daily stock data for 500+ S&P 500 companies
2. **Calculates** technical indicators (moving averages, RSI, volume trends)
3. **Predicts** AI trading signals using a trained Random Forest classifier
4. **Displays** everything in an interactive Streamlit dashboard
5. **Updates automatically** every day at 4 AM

## Quick Start

### 1. Setup (First Time Only - ~20 minutes)

```bash
# Open PowerShell, navigate to project

# Activate environment
.\pythonproject\Scripts\Activate.ps1

# Install dependencies (if needed)
pip install -r requirements.txt

# Initialize database
python data/database.py
python data/company_names.py

# Download 10 years of stock data (takes 15-20 min)
python data/download_data.py

#Train model for first time only
python -m models.model

#Run the dashboard
streamlit run dashboard.py
```

Setup complete!

---




### Automatic (4 AM Daily)
```bash
python scheduler.py
```

---

## Documentation

For detailed information:

- **[WORKFLOW.md](md_files/WORKFLOW.md)** - How the system works
- **[MODEL.md](md_files/MODEL.md)** - AI model details & features  
- **[SCHEDULER.md](md_files/SCHEDULER.md)** - Automation setup

---


**Status**: Production Ready | **Last Updated**: March 28, 2026

