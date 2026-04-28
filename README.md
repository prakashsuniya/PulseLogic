import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from pandas_ta import ema, rsi
from smartmoneyconcepts import smc

# --- 1. PRO UI CONFIG ---
st.set_page_config(page_title="PulseLogic Elite", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div.stButton > button:first-child { background-color: #00ff00; color: black; font-weight: bold; width: 100%; }
    .metric-container { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ELITE SIDEBAR ---
st.sidebar.title("💎 PulseLogic Elite")
user_ticker = st.sidebar.text_input("SYMBOL (e.g. SBIN, RELIANCE)", value="TATAPOWER").upper()
ticker = user_ticker + ".NS" if ".NS" not in user_ticker else user_ticker
tf = st.sidebar.selectbox("TIMEFRAME", ["15m", "1h", "4h", "1d"], index=1)
capital = 100000

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=30)
def get_clean_data(symbol, interval):
    df = yf.download(symbol, period="60d" if "h" in interval else "2y", interval=interval)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    
    # Add Professional Indicators
    df['ema20'] = ema(df['close'], length=20)
    df['ema50'] = ema(df['close'], length=50)
    df['rsi'] = rsi(df['close'], length=14)
    
    # SMC Analysis
    df_smc = df.copy()
    structure = smc.swing_highs_lows(df_smc, swing_length=5)
    return df, structure

df, structure = get_clean_data(ticker, tf)

if df is not None:
    curr_price = float(df['close'].iloc[-1])
    change = curr_price - float(df['open'].iloc[-1])
    p_change = (change / float(df['open'].iloc[-1])) * 100

    # --- 4. TOP BAR (ZERO-STYLE) ---
    st.subheader(f"{user_ticker} • NSE")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-container'><b>Price</b><br><span style='font-size:24px; color:{'#00ff00' if change > 0 else '#ff4b4b'}'>₹{curr_price:.2f} ({p_change:+.2f}%)</span></div>", unsafe_allow_html=True)
    with m2:
        trend = "BULLISH" if structure.iloc[-1]['HighLow'] == 1 else "BEARISH"
        st.markdown(f"<div class='metric-container'><b>AI Trend</b><br><span style='font-size:24px; color:{'#00ff00' if trend == 'BULLISH' else '#ff4b4b'}'>{trend}</span></div>", unsafe_allow_html=True)
    with m3:
        stop_loss = float(df['low'].tail(10).min())
        risk = curr_price - stop_loss
        qty = int((capital * 0.01) / risk) if risk > 0 else 0
        st.markdown(f"<div class='metric-container'><b>Elite Qty</b><br><span style='font-size:24px; color:white'>{qty} Shares</span></div>", unsafe_allow_html=True)

    # --- 5. THE PRO CHART ---
    fig = go.Figure()
    # Candlesticks
    fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="OHLC"))
    # EMAs
    fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name="EMA 20", line=dict(color='#00d1ff', width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name="EMA 50", line=dict(color='#ff9900', width=1)))

    # Structure Markers (BOS/CHoCH)
    bull_marks = structure[structure['HighLow'] == 1]
    fig.add_trace(go.Scatter(x=bull_marks.index, y=bull_marks['low']*0.99, mode='markers', marker=dict(symbol='triangle-up', size=10, color='#00ff00'), name="BULL CHoCH"))

    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    st.plotly_chart(fig, use_container_width=True)

    # RSI Area
    st.markdown("### Momentum (RSI)")
    st.line_chart(df['rsi'].tail(50), height=150)
    
else:
    st.error("Enter a valid Indian Stock Symbol to begin.")




