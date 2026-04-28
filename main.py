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
st.sidebar.title("🛡️ Risk & Capital")
total_capital = 100000 
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

st.sidebar.divider()
st.sidebar.title("🏹 Market Selection")
user_input = st.sidebar.text_input("Enter Stock Name (e.g. RELIANCE, SBIN)", value="TATAPOWER")
stock = user_input.upper() + ".NS" if not user_input.endswith(".NS") else user_input.upper()
tf = st.sidebar.selectbox("Timeframe", ["15m", "1h", "4h", "1d"], index=1)

# --- 3. CLEAN DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_analysis(ticker, timeframe):
    try:
        raw_df = yf.download(ticker, period="60d" if "h" in timeframe else "2y", interval=timeframe)
        if raw_df.empty: return None, None
        
        df = raw_df.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df.columns = [str(col).lower() for col in df.columns]
        df = df[['open', 'high', 'low', 'close', 'volume']].dropna()
        
        # Calculate Only Market Structure (BOS/CHoCH)
        structure = smc.swing_highs_lows(df, swing_length=5)
        return df, structure
    except:
        return None, None

# --- 4. DISPLAY ---
df, structure = fetch_analysis(stock, tf)

if df is not None:
    curr_price = float(df['close'].iloc[-1])
    st.header(f"Live: {stock}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Live Price", f"₹{curr_price:.2f}")
    
    is_bullish = structure.iloc[-1]['HighLow'] == 1
    c2.metric("Structure", "BULLISH" if is_bullish else "BEARISH")
    
    # Precise Risk Calc
    last_low = float(df['low'].tail(10).min())
    risk_amt = curr_price - last_low
    qty = int((total_capital * (risk_pct/100)) / risk_amt) if risk_amt > 0 else 0
    c3.metric("Quantity", qty)

    # --- 5. THE CHART ---
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Please enter a valid Indian stock name.")
