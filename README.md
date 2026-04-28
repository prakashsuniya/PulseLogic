import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from smartmoneyconcepts import smc
from streamlit_autorefresh import st_autorefresh

# --- 1. APP SETUP ---
st.set_page_config(page_title="PulseLogic AI", layout="wide")
st_autorefresh(interval=60000, key="market_check")

# --- 2. SIDEBAR ---
st.sidebar.title("🛡️ Risk Management")
total_capital = 100000 
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

st.sidebar.divider()
st.sidebar.title("🏹 Market Selection")
stock = st.sidebar.selectbox("Select Asset", ["TATAPOWER.NS", "POLICYBZR.NS", "JIOFIN.NS", "SOL-USD", "BTC-USD"])
tf = st.sidebar.selectbox("Timeframe", ["15m", "1h", "4h", "1d"], index=1)

# --- 3. DATA ENGINE (NEW LOGIC) ---
@st.cache_data(ttl=60)
def fetch_analysis(ticker, timeframe):
    # Fix: We now use a single-ticker Ticker object which avoids the Multi-Index error
    t = yf.Ticker(ticker)
    df = t.history(period="60d" if "h" in timeframe else "2y", interval=timeframe)
    
    # Standardize column names
    df.columns = [str(c).lower() for c in df.columns]
    
    # Ensure we only have the columns the library needs
    df = df[['open', 'high', 'low', 'close', 'volume']]
    df = df.dropna()
    
    # Calculate SMC
    structure = smc.swing_highs_lows(df, swing_length=5)
    fvgs = smc.fvg(df)
    return df, structure, fvgs

try:
    df, structure, fvgs = fetch_analysis(stock, tf)
    curr_price = float(df['close'].iloc[-1])
    
    # --- 4. DASHBOARD ---
    st.header(f"Live Analysis: {stock}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Live Price", f"₹{curr_price:.2f}")
    
    is_bullish = structure.iloc[-1]['HighLow'] == 1
    c2.metric("Structure", "BULLISH" if is_bullish else "BEARISH")
    
    # Risk Calc
    last_low = float(df['low'].tail(10).min())
    risk_val = curr_price - last_low
    max_loss = total_capital * (risk_pct / 100)
    qty = int(max_loss / risk_val) if risk_val > 0 else 0
    c3.metric("Rec. Quantity", qty)

    # --- 5. CHART ---
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], 
        low=df['low'], close=df['close'], name="Price"
    )])
    
    # Highlight FVG Zones
    bull_fvg = fvgs[fvgs['fvg'] == 1].tail(2)
    for _, row in bull_fvg.iterrows():
        fig.add_shape(type="rect", x0=df.index[0], y0=row['bottom'], x1=df.index[-1], y1=row['top'],
                      fillcolor="rgba(0, 255, 0, 0.1)", line_width=0)

    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Waiting for Data Sync... (Note: {e})")
    # --- 5. ENHANCED CHART ---
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], 
        low=df['low'], close=df['close'], name="Price"
    )])

    # ADD THIS: Visual markers for Structure
    # Green Up-Arrow for Bullish, Red Down-Arrow for Bearish
    bull_signals = structure[structure['HighLow'] == 1]
    bear_signals = structure[structure['HighLow'] == -1]

    fig.add_trace(go.Scatter(
        x=bull_signals.index, y=bull_signals['low'] * 0.99,
        mode='markers', marker=dict(symbol='triangle-up', size=12, color='lime'),
        name='Bullish Structure'
    ))

    fig.add_trace(go.Scatter(
        x=bear_signals.index, y=bear_signals['high'] * 1.01,
        mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'),
        name='Bearish Structure'
    ))

    fig.update_layout(
        template="plotly_dark", 
        height=600, 
        xaxis_rangeslider_visible=True, # Adding this back helps mobile zooming!
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)



