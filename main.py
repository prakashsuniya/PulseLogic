import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from smartmoneyconcepts import smc
from streamlit_autorefresh import st_autorefresh
import requests

# --- 1. SETTINGS ---
st.set_page_config(page_title="PulseLogic AI", layout="wide", page_icon="🏹")
st_autorefresh(interval=60000, key="market_check")

# --- 2. SIDEBAR & RISK ---
st.sidebar.title("🛡️ Risk Management")
total_capital = 100000 
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)
max_loss = total_capital * (risk_pct / 100)

st.sidebar.divider()
st.sidebar.title("🏹 Market Selection")
stock = st.sidebar.selectbox("Select Asset", ["TATAPOWER.NS", "POLICYBZR.NS", "JIOFIN.NS", "SOL-USD", "BTC-USD"])
tf = st.sidebar.selectbox("Timeframe", ["15m", "1h", "4h", "1d"], index=1)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_analysis(ticker, timeframe):
    df = yf.download(ticker, period="60d" if "h" in timeframe else "2y", interval=timeframe)
    df.columns = [c.lower() for c in df.columns]
    structure = smc.swing_highs_lows(df, swing_length=5)
    fvgs = smc.fvg(df)
    return df, structure, fvgs

try:
    df, structure, fvgs = fetch_analysis(stock, tf)
    curr_price = df['close'].iloc[-1]
    
    # --- 4. DASHBOARD ---
    st.header(f"Live Analysis: {stock}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Live Price", f"₹{curr_price:.2f}")
    c2.metric("Structure", "Bullish" if structure.iloc[-1]['HighLow'] == 1 else "Bearish")
    
    # Risk Calc
    last_low = df['low'].tail(5).min()
    risk_per_share = curr_price - last_low
    qty = int(max_loss / risk_per_share) if risk_per_share > 0 else 0
    c3.metric("Rec. Quantity", qty)

    # --- 5. CHART ---
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
    
    # Draw FVG Zones
    bull_fvg = fvgs[fvgs['fvg'] == 1].tail(2)
    for i, row in bull_fvg.iterrows():
        fig.add_shape(type="rect", x0=i, y0=row['bottom'], x1=df.index[-1], y1=row['top'],
                      fillcolor="rgba(0, 255, 0, 0.1)", line_width=0)

    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Waiting for Data... {e}")
