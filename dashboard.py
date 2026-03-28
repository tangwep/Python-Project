import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data import database
import logging
import joblib
import numpy as np
from datetime import datetime

# Set page config for a wider, dark-themed layout
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional dark theme CSS styling - Enhanced for 5-level predictions
st.markdown("""
    <style>
    /* Main app styling */
    .main { background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%); color: #e1e8ed; }
    .stApp { background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%); }
    
    /* Input elements */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > input {
        background-color: #192734 !important;
        color: #e1e8ed !important;
        border: 2px solid #38444d !important;
        border-radius: 8px !important;
    }
    
    .stSelectbox > div > label,
    .stCheckbox > label {
        color: #e1e8ed !important;
        font-weight: 600 !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #1da1f2 0%, #1a8cdc 100%) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 24px !important;
        padding: 10px 30px !important;
        box-shadow: 0 4px 15px rgba(29, 161, 242, 0.3) !important;
    }
    
    .stButton > button:hover {
        box-shadow: 0 6px 20px rgba(29, 161, 242, 0.5) !important;
    }
    
    /* Headers and titles */
    h1, h2, h3 { color: #f7f9fa !important; font-weight: 800 !important; }
    h4, h5, h6 { color: #e1e8ed !important; font-weight: 700 !important; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #192734 0%, #1f2d3d 100%) !important;
        border-right: 2px solid #38444d !important;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #1da1f2 !important;
        border-bottom: 3px solid #1da1f2 !important;
        padding-bottom: 12px !important;
    }
    
    /* Professional metrics display */
    .metric-container {
        background: linear-gradient(135deg, #192734 0%, #22303c 100%);
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #38444d;
        text-align: center;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .metric-container:hover {
        border-color: #1da1f2;
        box-shadow: 0 8px 20px rgba(29, 161, 242, 0.3);
        transform: translateY(-2px);
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #8899a6;
        font-weight: 600;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 1.8rem;
        color: #f7f9fa;
        font-weight: 800;
    }
    
    /* Sentiment boxes - 5 level colors */
    .sentiment-box {
        background: linear-gradient(135deg, #192734 0%, #22303c 100%);
        border: 3px solid #38444d;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        margin: 16px 0;
        transition: all 0.3s ease;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }
    
    .sentiment-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
    }
    
    .sentiment-strong-buy {
        border-color: #00d084 !important;
        background: linear-gradient(135deg, rgba(0, 208, 132, 0.15) 0%, rgba(0, 208, 132, 0.05) 100%) !important;
    }
    
    .sentiment-weak-buy {
        border-color: #17bf63 !important;
        background: linear-gradient(135deg, rgba(23, 191, 99, 0.15) 0%, rgba(23, 191, 99, 0.05) 100%) !important;
    }
    
    .sentiment-hold {
        border-color: #f39c12 !important;
        background: linear-gradient(135deg, rgba(243, 156, 18, 0.15) 0%, rgba(243, 156, 18, 0.05) 100%) !important;
    }
    
    .sentiment-weak-sell {
        border-color: #ff6b6b !important;
        background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, rgba(255, 107, 107, 0.05) 100%) !important;
    }
    
    .sentiment-strong-sell {
        border-color: #e74c3c !important;
        background: linear-gradient(135deg, rgba(231, 76, 60, 0.15) 0%, rgba(231, 76, 60, 0.05) 100%) !important;
    }
    
    .sentiment-title {
        color: #8899a6;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .sentiment-text {
        font-size: 2.2rem;
        font-weight: 900;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .sentiment-strong-buy .sentiment-text { color: #00d084; }
    .sentiment-weak-buy .sentiment-text { color: #17bf63; }
    .sentiment-hold .sentiment-text { color: #f39c12; }
    .sentiment-weak-sell .sentiment-text { color: #ff6b6b; }
    .sentiment-strong-sell .sentiment-text { color: #e74c3c; }
    
    .prediction-badge {
        font-size: 0.9rem;
        font-weight: 700;
        margin-top: 12px;
        padding: 8px 16px;
        border-radius: 16px;
        display: inline-block;
    }
    
    /* 5-Level Signal badges */
    .signal-strong-buy { 
        background: linear-gradient(135deg, #00d084, #00b872) !important; 
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(0, 208, 132, 0.4);
    }
    .signal-weak-buy { 
        background: linear-gradient(135deg, #17bf63, #13a852) !important; 
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(23, 191, 99, 0.3);
    }
    .signal-hold { 
        background: linear-gradient(135deg, #f39c12, #d68a10) !important; 
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(243, 156, 18, 0.3);
    }
    .signal-weak-sell { 
        background: linear-gradient(135deg, #ff6b6b, #e85050) !important; 
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
    }
    .signal-strong-sell { 
        background: linear-gradient(135deg, #e74c3c, #c73829) !important; 
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(231, 76, 60, 0.4);
    }
    
    /* Divider */
    .divider {
        border-top: 2px solid #38444d;
        margin: 28px 0;
    }
    
    /* Company header section */
    .company-header {
        background: linear-gradient(135deg, #1da1f2 0%, #1a8cdc 100%);
        padding: 28px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(29, 161, 242, 0.3);
    }
    
    .company-header h1 {
        margin: 0 !important;
        color: #ffffff !important;
        font-size: 2.5rem !important;
    }
    
    .company-sector {
        color: #bde3ff;
        font-size: 1rem;
        margin-top: 8px;
        font-weight: 500;
    }
    
    /* Model Prediction Section */
    .model-section {
        background: linear-gradient(135deg, #192734 0%, #22303c 100%);
        border: 2px solid #1da1f2;
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 8px 24px rgba(29, 161, 242, 0.2);
    }
    
    .model-section h3 {
        color: #1da1f2 !important;
        text-align: center;
        margin-bottom: 16px;
    }
    
    /* Prediction cards */
    .pred-card {
        background: linear-gradient(135deg, #1a2332 0%, #252d3a 100%);
        border: 2px solid #38444d;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin: 8px;
        transition: all 0.3s ease;
    }
    
    .pred-card:hover {
        transform: translateY(-4px);
        border-width: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_data(symbol):
    """Fetch price and indicator data from database"""
    conn = database.get_conn()
    price_df = pd.read_sql_query(
        "SELECT * FROM daily_prices WHERE symbol=? ORDER BY date DESC LIMIT 500",
        conn, params=(symbol,)
    )
    ind_df = pd.read_sql_query(
        "SELECT * FROM technical_indicators WHERE symbol=? ORDER BY date DESC LIMIT 500",
        conn, params=(symbol,)
    )
    company_info = pd.read_sql_query("SELECT * FROM companies WHERE symbol=? LIMIT 1", conn, params=(symbol,))
    conn.close()

    if not price_df.empty:
        price_df['date'] = pd.to_datetime(price_df['date'])
        price_df = price_df.sort_values('date')

    if not ind_df.empty:
        ind_df['date'] = pd.to_datetime(ind_df['date'])
        ind_df = ind_df.sort_values('date')

    return price_df, ind_df, company_info.iloc[0] if not company_info.empty else None

def get_all_companies_for_search():
    """Get list of all companies for search dropdown"""
    conn = database.get_conn()
    companies_df = pd.read_sql_query("SELECT symbol, name FROM companies ORDER BY name", conn)
    conn.close()
    return companies_df

def get_model_prediction(price, ma20, ma50, ma100, ma200, rsi, volume, volume_ma):
    """Get 5-level prediction from trained model"""
    try:
        # Use absolute path based on script location
        import os
        from pathlib import Path
        script_dir = Path(__file__).parent
        model_path = script_dir / "models" / "stock_model.pkl"
        
        if not model_path.exists():
            logger.error(f"Model file not found at: {model_path}")
            return "Model Not Found", "signal-hold", "signal-hold", "N/A", "N/A", False
        
        # Load model - it returns a dict with 'model', 'features', 'accuracy'
        model_data = joblib.load(str(model_path))
        model = model_data['model']  # Extract the actual model
        
        # Prepare features as used in model training
        dist_ma20 = (price - ma20) / ma20 if ma20 != 0 else 0
        dist_ma50 = (price - ma50) / ma50 if ma50 != 0 else 0
        dist_ma100 = (price - ma100) / ma100 if ma100 != 0 else 0
        dist_ma200 = (price - ma200) / ma200 if ma200 != 0 else 0
        ma_trend = (ma20 - ma100) / ma100 if ma100 != 0 else 0
        vol_normalized = volume / volume_ma if volume_ma != 0 else 0
        
        features = np.array([[dist_ma20, dist_ma50, dist_ma100, dist_ma200, rsi, ma_trend, vol_normalized]])
        
        # Get prediction
        prediction = model.predict(features)[0]
        probs = model.predict_proba(features)[0]
        max_prob = np.max(probs)
        
        # Map prediction to signal
        signal_map = {
            -2: ("STRONG SELL", "sentiment-strong-sell", "signal-strong-sell", "Strong Sell"),
            -1: ("WEAK SELL", "sentiment-weak-sell", "signal-weak-sell", "Weak Sell"),
            0: ("HOLD", "sentiment-hold", "signal-hold", "Hold"),
            1: ("WEAK BUY", "sentiment-weak-buy", "signal-weak-buy", "Weak Buy"),
            2: ("STRONG BUY", "sentiment-strong-buy", "signal-strong-buy", "Strong Buy")
        }
        
        emoji_signal, sentiment_class, badge_class, signal_text = signal_map.get(prediction, ("UNKNOWN", "signal-hold", "signal-hold", "Hold"))
        confidence = f"{max_prob*100:.1f}%"
        
        return emoji_signal, sentiment_class, badge_class, signal_text, confidence, True
    except Exception as e:
        logger.error(f"Model prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return "Model Error", "signal-hold", "signal-hold", "N/A", "N/A", False

# ==================== SIDEBAR ====================
st.sidebar.title("⚙️ Dashboard Settings")

# Stock Selection Section
st.sidebar.header("📊 Stock Selection")
all_companies_df = get_all_companies_for_search()
search_options = [f"{row['name']} ({row['symbol']})" for index, row in all_companies_df.iterrows()]

default_search_index = 0
if "Apple Inc. (AAPL)" in search_options:
    default_search_index = search_options.index("Apple Inc. (AAPL)")

selected_company_str = st.sidebar.selectbox("Search by Name or Symbol", search_options, index=default_search_index)
selected_symbol = selected_company_str.split("(")[-1].replace(")", "")

# Chart Settings Section
st.sidebar.header("📈 Chart Settings")
show_ma20 = st.sidebar.checkbox("Show MA20", value=True)
show_ma50 = st.sidebar.checkbox("Show MA50", value=True)
show_ma100 = st.sidebar.checkbox("Show MA100", value=True)
show_ma200 = st.sidebar.checkbox("Show MA200", value=True)
show_volume = st.sidebar.checkbox("Show Volume", value=True)
show_rsi = st.sidebar.checkbox("Show RSI (14)", value=True)

# Fetch data
prices, inds, company_info = get_data(selected_symbol)

if prices.empty or company_info is None or inds.empty:
    st.error("⚠️ No sufficient data found for this symbol. Please ensure data has been downloaded using download_data.py")
    st.stop()

# ==================== DATA PROCESSING ====================
curr = prices.iloc[-1]
last_ind = inds.iloc[-1]

rsi = last_ind['rsi14']
price = curr['close']
ma20 = last_ind['ma20']
ma50 = last_ind['ma50']
ma100 = last_ind['ma100']
ma200 = last_ind['ma200']
volume = curr['volume']
volume_ma = prices['volume'].tail(20).mean() if len(prices) >= 20 else volume

# Calculate price change
if len(prices) > 1:
    prev_price = prices.iloc[-2]['close']
    price_change = price - prev_price
    price_change_pct = (price_change / prev_price) * 100
else:
    price_change = 0
    price_change_pct = 0

# ==================== GET MODEL PREDICTION ====================
emoji_signal, sentiment_class, badge_class, signal_text, confidence, model_loaded = get_model_prediction(
    price, ma20, ma50, ma100, ma200, rsi, volume, volume_ma
)

# ==================== MAIN CONTENT ====================

# Company Header
st.markdown(f"""
    <div class='company-header'>
        <h1>{company_info['name']}</h1>
        <div class='company-sector'>🏢 {company_info['sector']} • {selected_symbol}</div>
    </div>
    """, unsafe_allow_html=True)

# Main Prediction Box with 5 levels
st.markdown(f"""
    <div class='model-section'>
        <h3>🤖 AI Model Prediction</h3>
        <div class='sentiment-box {sentiment_class}'>
            <div class='sentiment-title'>Prediction Signal</div>
            <p class='sentiment-text'>{emoji_signal}</p>
            <div class='prediction-badge {badge_class}'>{signal_text} • Confidence: {confidence}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Key Metrics Row
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("### 📊 Key Metrics")

# Metrics Panel with Model Prediction
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.markdown(f"<div class='metric-container'><span class='metric-label'>Current Price</span><br><span class='metric-value'>${price:.2f}</span></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-container'><span class='metric-label'>RSI (14)</span><br><span class='metric-value'>{rsi:.2f}</span></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-container'><span class='metric-label'>MA 50</span><br><span class='metric-value'>${ma50:.2f}</span></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='metric-container'><span class='metric-label'>MA 100</span><br><span class='metric-value'>${ma100:.2f}</span></div>", unsafe_allow_html=True)
with col5:
    st.markdown(f"<div class='metric-container'><span class='metric-label'>MA 200</span><br><span class='metric-value'>${ma200:.2f}</span></div>", unsafe_allow_html=True)
with col6:
    change_color = "#00d084" if price_change >= 0 else "#e74c3c"
    st.markdown(f"<div class='metric-container'><span class='metric-label'>24H Change</span><br><span class='metric-value' style='color: {change_color};'>{price_change:+.2f} ({price_change_pct:+.2f}%)</span></div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ==================== CHART VISUALIZATION ====================
st.markdown("### 📉 Price Chart & Technical Analysis")

# Build subplot figure
num_rows = 1
row_heights_list = [0.6]
current_row = 1

if show_volume:
    num_rows += 1
    row_heights_list.append(0.2)
if show_rsi:
    num_rows += 1
    row_heights_list.append(0.2)

fig = make_subplots(
    rows=num_rows, 
    cols=1, 
    shared_xaxes=True,
    vertical_spacing=0.08,
    row_heights=row_heights_list
)

# Candlestick chart
fig.add_trace(go.Candlestick(
    x=prices['date'],
    open=prices['open'],
    high=prices['high'],
    low=prices['low'],
    close=prices['close'],
    name="Price",
    increasing_line_color='#00d084',
    increasing_fillcolor='#00d084',
    decreasing_line_color='#e74c3c',
    decreasing_fillcolor='#e74c3c',
    hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Open: $%{open:.2f}<br>High: $%{high:.2f}<br>Low: $%{low:.2f}<br>Close: $%{close:.2f}<extra></extra>",
), row=current_row, col=1)

# Moving Averages with enhanced colors
if show_ma20:
    fig.add_trace(go.Scatter(
        x=inds['date'],
        y=inds['ma20'],
        name="MA 20",
        line=dict(color='#ff9800', width=2),
        hovertemplate="MA 20: $%{y:.2f}<extra></extra>",
    ), row=current_row, col=1)

if show_ma50:
    fig.add_trace(go.Scatter(
        x=inds['date'],
        y=inds['ma50'],
        name="MA 50",
        line=dict(color='#2196f3', width=2),
        hovertemplate="MA 50: $%{y:.2f}<extra></extra>",
    ), row=current_row, col=1)

if show_ma100:
    fig.add_trace(go.Scatter(
        x=inds['date'],
        y=inds['ma100'],
        name="MA 100",
        line=dict(color='#9c27b0', width=2),
        hovertemplate="MA 100: $%{y:.2f}<extra></extra>",
    ), row=current_row, col=1)

if show_ma200:
    fig.add_trace(go.Scatter(
        x=inds['date'],
        y=inds['ma200'],
        name="MA 200",
        line=dict(color='#f44336', width=2),
        hovertemplate="MA 200: $%{y:.2f}<extra></extra>",
    ), row=current_row, col=1)

fig.update_yaxes(title_text="<b>Price</b>", row=current_row, col=1, showgrid=True, gridwidth=1, gridcolor='#38444d')

current_row += 1

# Volume chart
if show_volume:
    volume_colors = ['#00d084' if prices['close'].iloc[i] > prices['open'].iloc[i] else '#e74c3c' for i in range(len(prices))]
    fig.add_trace(go.Bar(
        x=prices['date'],
        y=prices['volume'],
        name="Volume",
        marker_color=volume_colors,
        opacity=0.6,
        hovertemplate="Volume: %{y:,.0f}<extra></extra>",
    ), row=current_row, col=1)
    
    fig.update_yaxes(title_text="<b>Volume</b>", row=current_row, col=1, showgrid=True, gridwidth=1, gridcolor='#38444d', showticklabels=False)
    current_row += 1

# RSI chart
if show_rsi:
    fig.add_trace(go.Scatter(
        x=inds['date'],
        y=inds['rsi14'],
        name="RSI (14)",
        line=dict(color='#ffc107', width=2),
        hovertemplate="RSI: %{y:.1f}<extra></extra>",
    ), row=current_row, col=1)
    
    # RSI reference lines
    fig.add_hline(y=30, line_dash="dash", line_color="#00d084", line_width=1, row=current_row, col=1, annotation_text="Oversold")
    fig.add_hline(y=70, line_dash="dash", line_color="#e74c3c", line_width=1, row=current_row, col=1, annotation_text="Overbought")
    fig.add_hline(y=50, line_dash="dot", line_color="#8899a6", line_width=1, row=current_row, col=1)
    
    fig.update_yaxes(title_text="<b>RSI</b>", row=current_row, col=1, range=[0, 100], showgrid=True, gridwidth=1, gridcolor='#38444d')
    current_row += 1

# Update layout with enhanced styling
fig.update_layout(
    template="plotly_dark",
    xaxis_rangeslider_visible=False,
    height=900,
    margin=dict(l=60, r=60, t=40, b=40),
    paper_bgcolor='#0a0e27',
    plot_bgcolor='#1a1f3a',
    font=dict(color='#e1e8ed', family='Arial, sans-serif', size=11),
    hovermode="x unified",
    legend=dict(
        x=0.01,
        y=0.99,
        bgcolor='rgba(25, 39, 52, 0.9)',
        bordercolor='#1da1f2',
        borderwidth=2,
        font=dict(size=10)
    ),
    xaxis=dict(
        showgrid=True,
        gridwidth=1,
        gridcolor='#38444d',
        showline=True,
        linewidth=2,
        linecolor='#38444d',
    ),
)

st.plotly_chart(fig, use_container_width=True)

# ==================== ANALYSIS DETAILS ====================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("### 📈 Technical Analysis Details")

# Create a detailed metrics table
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='metric-container'>
        <span class='metric-label'>Price Position</span>
        <br>
        <span class='metric-value'>${price:.2f}</span>
        <br>
        <span style='color: #8899a6; font-size: 0.85rem; margin-top: 8px; display: block;'>
            vs MA20: {((price/ma20 - 1)*100):+.2f}%<br>
            vs MA200: {((price/ma200 - 1)*100):+.2f}%
        </span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    rsi_status = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
    rsi_color = "#00d084" if rsi < 30 else "#e74c3c" if rsi > 70 else "#f39c12"
    st.markdown(f"""
    <div class='metric-container'>
        <span class='metric-label'>RSI Status</span>
        <br>
        <span class='metric-value'>{rsi:.2f}</span>
        <br>
        <span style='color: {rsi_color}; font-weight: 700; font-size: 0.9rem; margin-top: 8px; display: block;'>{rsi_status}</span>
    </div>
    """, unsafe_allow_html=True)

with col3:
    trend = "Uptrend" if price > ma200 else "Downtrend"
    trend_color = "#00d084" if trend == "Uptrend" else "#e74c3c"
    st.markdown(f"""
    <div class='metric-container'>
        <span class='metric-label'>Long-Term Trend</span>
        <br>
        <span style='color: {trend_color}; font-weight: 700; font-size: 1.3rem;'>{trend}</span>
        <br>
        <span style='color: #8899a6; font-size: 0.85rem; margin-top: 8px; display: block;'>MA200: ${ma200:.2f}</span>
    </div>
    """, unsafe_allow_html=True)

with col4:
    ma_alignment = "✓ Aligned" if (ma20 > ma50 > ma100 > ma200) or (ma20 < ma50 < ma100 < ma200) else "✗ Mixed"
    align_color = "#00d084" if ma_alignment == "✓ Aligned" else "#f39c12"
    st.markdown(f"""
    <div class='metric-container'>
        <span class='metric-label'>MA Alignment</span>
        <br>
        <span style='color: {align_color}; font-weight: 700; font-size: 1.5rem;'>{ma_alignment}</span>
        <br>
        <span style='color: #8899a6; font-size: 0.85rem; margin-top: 8px; display: block;'>Trend Strength</span>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center; color: #8899a6; font-size: 0.85rem; margin-top: 30px;'>
        <p>💡 <strong>Disclaimer:</strong> This dashboard is for educational and informational purposes only. 
        It is not financial advice. Always consult with a financial advisor before making investment decisions.</p>
        <p style='font-size: 0.8rem; margin-top: 15px;'>Last Updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC") + """</p>
    </div>
    """, unsafe_allow_html=True)

