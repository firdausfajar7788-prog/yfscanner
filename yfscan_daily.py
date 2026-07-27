import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Daily Scanner Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# SESSION STATE
# =========================================================
if "selected_symbol" not in st.session_state:
    st.session_state.selected_symbol = "BTC"
if "last_notified" not in st.session_state:
    st.session_state.last_notified = {}
if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = datetime.now()
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["BTC", "ETH", "SOL", "BNB", "XRP"]
if "cached_data" not in st.session_state:
    st.session_state.cached_data = []
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []
if "price_alerts" not in st.session_state:
    st.session_state.price_alerts = {}

# =========================================================
# CUSTOM CSS - PREMIUM DARK THEME
# =========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp { background: #070b14; }
    
    /* Glass cards */
    .glass-card {
        background: rgba(16, 24, 40, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 20px;
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(0,255,136,0.15);
        transform: translateY(-2px);
    }
    
    /* Premium metrics */
    .premium-metric {
        background: rgba(16, 24, 40, 0.5);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 14px;
        padding: 16px 20px;
        transition: all 0.3s ease;
    }
    .premium-metric:hover {
        border-color: rgba(0,255,136,0.12);
        background: rgba(16, 24, 40, 0.7);
    }
    .premium-metric .label {
        color: #64748b;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .premium-metric .value {
        color: #f1f5f9;
        font-size: 26px;
        font-weight: 700;
        margin-top: 4px;
    }
    
    /* Signal badges */
    .badge-strong-buy {
        background: linear-gradient(135deg, rgba(0,255,136,0.2), rgba(0,255,136,0.05));
        border: 1px solid #00ff88;
        border-radius: 20px;
        padding: 3px 14px;
        color: #00ff88;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        box-shadow: 0 0 30px rgba(0,255,136,0.05);
    }
    .badge-buy {
        background: linear-gradient(135deg, rgba(0,200,255,0.15), rgba(0,200,255,0.05));
        border: 1px solid #00c8ff;
        border-radius: 20px;
        padding: 3px 14px;
        color: #00c8ff;
        font-weight: 600;
        font-size: 12px;
        display: inline-block;
    }
    .badge-wait {
        background: linear-gradient(135deg, rgba(251,191,36,0.15), rgba(251,191,36,0.05));
        border: 1px solid #fbbf24;
        border-radius: 20px;
        padding: 3px 14px;
        color: #fbbf24;
        font-weight: 600;
        font-size: 12px;
        display: inline-block;
    }
    .badge-avoid {
        background: linear-gradient(135deg, rgba(255,59,92,0.15), rgba(255,59,92,0.05));
        border: 1px solid #ff3b5c;
        border-radius: 20px;
        padding: 3px 14px;
        color: #ff3b5c;
        font-weight: 600;
        font-size: 12px;
        display: inline-block;
    }
    
    .badge-ai {
        background: linear-gradient(135deg, rgba(168,85,247,0.2), rgba(168,85,247,0.05));
        border: 1px solid #a855f7;
        border-radius: 20px;
        padding: 2px 12px;
        color: #a855f7;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00ff88, #00cc66);
        color: #000;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 10px 28px;
        transition: all 0.3s ease;
        font-size: 13px;
    }
    .stButton > button:hover {
        transform: scale(1.02) translateY(-2px);
        box-shadow: 0 8px 40px rgba(0,255,136,0.15);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(16, 24, 40, 0.3);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        color: #64748b !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0,255,136,0.08) !important;
        color: #00ff88 !important;
    }
    
    /* Tables */
    .dataframe {
        border-collapse: separate !important;
        border-spacing: 0 4px !important;
    }
    .dataframe thead tr th {
        background: rgba(16, 24, 40, 0.5) !important;
        color: #94a3b8 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 10px 14px !important;
        border: none !important;
        border-radius: 8px 8px 0 0 !important;
    }
    .dataframe tbody tr td {
        background: rgba(16, 24, 40, 0.3) !important;
        color: #e2e8f0 !important;
        font-size: 13px !important;
        padding: 8px 14px !important;
        border: none !important;
    }
    .dataframe tbody tr:hover td {
        background: rgba(16, 24, 40, 0.6) !important;
    }
    
    /* Divider */
    hr {
        border-color: rgba(255,255,255,0.04) !important;
        margin: 28px 0 !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(16, 24, 40, 0.3); border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #00ff88; }
    
    /* Status dot */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse-dot 2s infinite;
    }
    .status-dot.live { background: #00ff88; }
    .status-dot.error { background: #ff3b5c; }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# RATE LIMITER CLASS
# =========================================================
class RateLimiter:
    def __init__(self, max_calls=15, period=1):
        self.calls = deque()
        self.max_calls = max_calls
        self.period = period
    
    def wait(self):
        now = time.time()
        while self.calls and now - self.calls[0] > self.period:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.calls.append(now)

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0 20px 0;">
    <div>
        <div style="font-size: 32px; font-weight: 800; letter-spacing: -0.5px;">
            <span style="background: linear-gradient(135deg, #00ff88, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Daily Scanner</span>
            <span style="font-size: 14px; color: #475569; -webkit-text-fill-color: #475569; background: none; margin-left: 8px;">Pro</span>
        </div>
        <div style="font-size: 13px; color: #475569; margin-top: -4px;">
            <span class="status-dot live"></span>Live · Yahoo Finance · Real-time
        </div>
    </div>
    <div style="display: flex; gap: 16px; align-items: center;">
        <div style="text-align: right; font-size: 12px; color: #475569;">
            <div>🕐 {}</div>
            <div style="font-size: 11px;">{}</div>
        </div>
    </div>
</div>
""".format(
    st.session_state.last_update_time.strftime('%H:%M:%S'),
    st.session_state.last_update_time.strftime('%d %b %Y')
), unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("""
    <div style="padding: 4px 0 12px 0;">
        <div style="font-size: 17px; font-weight: 700; color: #f1f5f9;">⚙️ Settings</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Currency
    currency = st.selectbox("💱 Currency", ["USD", "IDR"])
    
    st.divider()
    
    # Watchlist
    st.subheader("📋 Watchlist")
    
    col_w1, col_w2 = st.columns([3, 1])
    with col_w1:
        new_coin = st.text_input("Add Coin", placeholder="BTC", label_visibility="collapsed")
    with col_w2:
        if st.button("➕", use_container_width=True):
            if new_coin and new_coin.upper() not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_coin.upper())
                st.rerun()
    
    for coin in st.session_state.watchlist:
        col_c1, col_c2 = st.columns([4, 1])
        with col_c1:
            st.write(f"• {coin}")
        with col_c2:
            if st.button("✕", key=f"del_{coin}"):
                st.session_state.watchlist.remove(coin)
                st.rerun()
    
    st.divider()
    
    # Auto Refresh
    st.subheader("🔄 Auto Refresh")
    refresh_minutes = st.selectbox("Interval (minutes)", [2, 5, 10, 15, 30, 60], index=2)
    
    st.divider()
    
    # Telegram
    st.subheader("📱 Telegram Alert")
    default_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
    default_chat = st.secrets.get("TELEGRAM_CHAT_ID", "")
    BOT_TOKEN = st.text_input("Bot Token", type="password", value=default_token)
    CHAT_ID = st.text_input("Chat ID", value=default_chat)
    send_notifications = st.checkbox("🔔 Enable Alerts", value=True)
    notify_min_score = st.slider("Alert Score Min", 50, 90, 65, step=5)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🚀 Test", use_container_width=True):
            if BOT_TOKEN and CHAT_ID:
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    r = requests.post(url, json={"chat_id": CHAT_ID, "text": "🚀 Scanner Pro aktif!"}, timeout=10)
                    st.success("✅ Sent!" if r.status_code == 200 else f"❌ {r.status_code}")
                except Exception as e:
                    st.error(f"❌ {e}")
            else:
                st.warning("⚠️ Fill credentials")
    with col_t2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    
    st.subheader("📊 Status")
    st.metric("Coins Scanned", "100+")
    st.metric("Watchlist", len(st.session_state.watchlist))
    st.metric("Refresh", f"{refresh_minutes}m")

# =========================================================
# FUNGSI AMBIL KURS IDR
# =========================================================
@st.cache_data(ttl=3600)
def get_usd_to_idr():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        r = requests.get(url, timeout=10)
        return r.json()["rates"]["IDR"] if r.status_code == 200 else 15500
    except:
        return 15500

usd_to_idr = get_usd_to_idr()

# =========================================================
# FUNGSI TELEGRAM
# =========================================================
def send_telegram(bot_token, chat_id, message):
    if not bot_token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        r = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except:
        return False

def format_telegram_message(row):
    emoji = "🚀" if "STRONG" in row["Signal"] else "📈"
    return f"""
{emoji} <b>SIGNAL DETECTED!</b>

<b>Coin:</b> {row['Coin']} ({row['Symbol']})
<b>Signal:</b> {row['Signal']}
<b>Score:</b> {row['Score']}/100
<b>Price:</b> ${row['Price']:.4f}
<b>24H:</b> {row['24H %']}%
<b>7D:</b> {row['7D %']}%
<b>Volume:</b> {row['Volume (M)']}M {row.get('Volume Trend', '')}
<b>Rank:</b> #{row['Rank']}
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

# =========================================================
# DAFTAR COIN (TOP 150)
# =========================================================
TOP_CRYPTO = [
    "BTC", "ETH", "USDT", "BNB", "SOL", "XRP", "USDC", "ADA", "DOGE", "TRX",
    "TON", "DOT", "MATIC", "DAI", "SHIB", "LINK", "BCH", "UNI", "LTC", "ATOM",
    "XLM", "ETC", "OKB", "FIL", "APT", "HBAR", "MNT", "CRO", "XMR", "ARB",
    "VET", "IMX", "MKR", "AAVE", "STX", "SUI", "RNDR", "INJ", "ALGO", "OP",
    "TIA", "GRT", "TAO", "RUNE", "QNT", "SEI", "FLOW", "NEO", "KCS", "LDO",
    "FLOKI", "FTM", "GALA", "WIF", "ENA", "W", "PEPE", "ONDO", "JUP", "AXS",
    "EOS", "CRV", "SNX", "LUNC", "BTT", "XDC", "KAVA", "CAKE", "COMP", "CHZ",
    "YFI", "ZEC", "KSM", "SUSHI", "ENJ", "BAT", "ZIL", "ICX", "QTUM", "SC",
    "RSR", "BAND", "STORJ", "ALPHA", "OCEAN", "KNC", "KDA", "HOT", "RVN", "DASH",
    "ZRX", "NANO", "BTS", "WAVES", "VTHO", "XEM", "DGB", "ETN", "NKN", "ANKR",
    "ONE", "CELO", "DYDX", "LPT", "ENS", "CRV", "MASK", "LRC", "SPELL", "CHR"
]

# =========================================================
# GET DATA WITH RETRY
# =========================================================
rate_limiter = RateLimiter(max_calls=12, period=1)

def get_single_yfinance_data(symbol, max_retries=2):
    """Ambil data single symbol dengan retry"""
    for attempt in range(max_retries):
        try:
            rate_limiter.wait()
            
            ticker = yf.Ticker(symbol + "-USD")
            info = ticker.info
            name = info.get("shortName", symbol)
            market_cap = info.get("marketCap", 0) or info.get("totalAssets", 0)
            
            hist = ticker.history(period="7d", interval="1d")
            if hist.empty or len(hist) < 3:
                return None
            
            latest = hist.iloc[-1]
            price = latest["Close"]
            volume_24h = latest["Volume"]
            
            # Calculate changes
            change_24h = ((price - hist.iloc[-2]["Close"]) / hist.iloc[-2]["Close"]) * 100 if len(hist) >= 2 else 0
            change_7d = ((price - hist.iloc[0]["Close"]) / hist.iloc[0]["Close"]) * 100 if len(hist) >= 7 else 0
            
            # Volume analysis
            volumes = hist["Volume"].tolist()
            avg_volume_7d = sum(volumes) / len(volumes) if volumes else volume_24h
            ratio = volume_24h / avg_volume_7d if avg_volume_7d > 0 else 1
            
            if ratio > 1.5:
                volume_trend = "🔼 SURGE"
            elif ratio > 1.3:
                volume_trend = "🔼 UP"
            elif ratio < 0.5:
                volume_trend = "🔽 LOW"
            elif ratio < 0.7:
                volume_trend = "🔽 DOWN"
            else:
                volume_trend = "➡️ STABLE"
            
            return {
                "Coin": name,
                "Symbol": symbol,
                "Price": price,
                "24H %": change_24h,
                "7D %": change_7d,
                "Market Cap": market_cap,
                "Volume (M)": volume_24h / 1_000_000,
                "Volume Avg 7D": avg_volume_7d,
                "Volume Trend": volume_trend,
                "Volume Ratio": ratio,
                "Historical": hist
            }
            
        except Exception as e:
            if attempt == max_retries - 1:
                return None
            time.sleep(1)
    return None

@st.cache_data(ttl=300, show_spinner=False)
def get_yfinance_data(symbols):
    """Ambil data dari Yahoo Finance untuk banyak symbol"""
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_symbol = {
            executor.submit(get_single_yfinance_data, sym): sym
            for sym in symbols
        }
        
        for idx, future in enumerate(as_completed(future_to_symbol)):
            progress_bar.progress((idx + 1) / len(symbols))
            status_text.text(f"🔍 Scanning {idx + 1}/{len(symbols)} ...")
            try:
                data = future.result()
                if data:
                    results.append(data)
            except:
                pass
    
    progress_bar.empty()
    status_text.empty()
    return results

# =========================================================
# ADVANCED SCORING
# =========================================================
def calculate_score_advanced(row):
    """Calculate score with weighted components"""
    score = 0
    change_24h = row["24H %"]
    change_7d = row["7D %"]
    volume_ratio = row.get("Volume Ratio", 1)
    market_cap = row.get("Market Cap", 0)
    
    # 24h change (max 40)
    if change_24h > 15: score += 40
    elif change_24h > 10: score += 35
    elif change_24h > 5: score += 25
    elif change_24h > 2: score += 15
    elif change_24h > 0: score += 8
    
    # 7d change (max 25)
    if change_7d > 30: score += 25
    elif change_7d > 20: score += 20
    elif change_7d > 10: score += 15
    elif change_7d > 5: score += 10
    
    # Volume surge (max 20)
    if volume_ratio > 3.0: score += 20
    elif volume_ratio > 2.0: score += 15
    elif volume_ratio > 1.5: score += 10
    elif volume_ratio > 1.2: score += 5
    
    # Market cap bonus (max 15)
    if market_cap > 100_000_000_000: score += 15
    elif market_cap > 50_000_000_000: score += 12
    elif market_cap > 10_000_000_000: score += 8
    elif market_cap > 1_000_000_000: score += 5
    
    # RSI bonus (if available)
    if "RSI" in row and row["RSI"]:
        rsi = row["RSI"]
        if rsi < 30: score += 10  # Oversold = buy signal
        elif rsi > 70: score -= 10  # Overbought = sell signal
    
    return score

def get_signal(score):
    if score >= 80: return ("🔥 STRONG BUY", "badge-strong-buy")
    elif score >= 65: return ("🟢 BUY", "badge-buy")
    elif score >= 45: return ("🟡 WAIT", "badge-wait")
    else: return ("🔴 AVOID", "badge-avoid")

# =========================================================
# MAIN
# =========================================================
with st.spinner("📊 Fetching data from Yahoo Finance..."):
    raw_data = get_yfinance_data(TOP_CRYPTO)

if not raw_data:
    st.error("❌ Failed to fetch data. Please try again later.")
    st.stop()

# Process data
results = []
for data in raw_data:
    score = calculate_score_advanced(data)
    signal, badge = get_signal(score)
    
    # Calculate RSI if historical data available
    rsi = None
    if data.get("Historical") is not None:
        hist = data["Historical"]
        if len(hist) >= 14:
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs.iloc[-1])) if not pd.isna(rs.iloc[-1]) else None
    
    results.append({
        "Coin": data["Coin"],
        "Symbol": data["Symbol"],
        "Price": data["Price"],
        "24H %": round(data["24H %"], 2),
        "7D %": round(data["7D %"], 2),
        "Volume (M)": round(data["Volume (M)"], 1),
        "Volume Trend": data["Volume Trend"],
        "Score": score,
        "Signal": signal,
        "Badge": badge,
        "RSI": round(rsi, 1) if rsi else None,
        "Market Cap": data.get("Market Cap", 0)
    })

df = pd.DataFrame(results)
df = df.sort_values("Score", ascending=False).reset_index(drop=True)
df["Rank"] = df.index + 1

# Update time
st.session_state.last_update_time = datetime.now()
st.session_state.cached_data = df.to_dict('records')

# =========================================================
# TELEGRAM NOTIFICATIONS
# =========================================================
if BOT_TOKEN and CHAT_ID and send_notifications:
    alerts = df[(df["Signal"].isin(["🟢 BUY", "🔥 STRONG BUY"])) & (df["Score"] >= notify_min_score)]
    notified_count = 0
    for _, row in alerts.iterrows():
        symbol = row["Symbol"]
        signal = row["Signal"]
        if st.session_state.last_notified.get(symbol) != signal:
            msg = format_telegram_message(row)
            if send_telegram(BOT_TOKEN, CHAT_ID, msg):
                st.session_state.last_notified[symbol] = signal
                notified_count += 1
            time.sleep(0.3)
    if notified_count:
        st.sidebar.success(f"✅ {notified_count} alerts sent")

# =========================================================
# METRICS ROW
# =========================================================
avg_score = df["Score"].mean()
mood = "🟢 BULLISH" if avg_score >= 65 else "🟡 NEUTRAL" if avg_score >= 45 else "🔴 BEARISH"

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.markdown(f"""
    <div class="premium-metric">
        <div class="label">📊 Market Mood</div>
        <div class="value">{mood}</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="premium-metric">
        <div class="label">🪙 Scanned</div>
        <div class="value">{len(df)}</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="premium-metric">
        <div class="label">📈 Avg Score</div>
        <div class="value">{avg_score:.1f}</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    strong_count = len(df[df["Signal"] == "🔥 STRONG BUY"])
    st.markdown(f"""
    <div class="premium-metric">
        <div class="label">🔥 Strong Buy</div>
        <div class="value" style="color: #00ff88;">{strong_count}</div>
    </div>
    """, unsafe_allow_html=True)
with c5:
    buy_count = len(df[df["Signal"] == "🟢 BUY"])
    st.markdown(f"""
    <div class="premium-metric">
        <div class="label">🟢 Buy</div>
        <div class="value" style="color: #00c8ff;">{buy_count}</div>
    </div>
    """, unsafe_allow_html=True)
with c6:
    avoid_count = len(df[df["Signal"] == "🔴 AVOID"])
    st.markdown(f"""
    <div class="premium-metric">
        <div class="label">🔴 Avoid</div>
        <div class="value" style="color: #ff3b5c;">{avoid_count}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# WATCHLIST PERFORMANCE
# =========================================================
st.divider()
st.subheader("📋 Watchlist Performance")

watchlist_data = df[df["Symbol"].isin(st.session_state.watchlist)]
if not watchlist_data.empty:
    watchlist_data = watchlist_data.sort_values("Score", ascending=False)
    
    cols = st.columns(min(len(watchlist_data), 5))
    for idx, (_, row) in enumerate(watchlist_data.iterrows()):
        col_idx = idx % len(cols)
        with cols[col_idx]:
            color = "#00ff88" if "BUY" in row["Signal"] else "#ff3b5c" if "AVOID" in row["Signal"] else "#fbbf24"
            st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: #f1f5f9;">{row['Symbol']}</span>
                    <span class="{row['Badge']}">{row['Signal']}</span>
                </div>
                <div style="font-size: 20px; font-weight: 700; color: {color}; margin: 6px 0;">
                    {row['Score']}
                </div>
                <div style="font-size: 12px; color: #64748b;">
                    24h: <span style="color: {'#00ff88' if row['24H %'] > 0 else '#ff3b5c'}">{row['24H %']}%</span>
                    · ${row['Price']:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Add coins to watchlist to see performance")

# =========================================================
# TOP 3 OPPORTUNITIES
# =========================================================
st.divider()
st.subheader("🔥 Top 3 Opportunities")

top3 = df.head(3)
cols_top = st.columns(3)
for idx, (_, row) in enumerate(top3.iterrows()):
    with cols_top[idx]:
        st.markdown(f"""
        <div style="background: rgba(16, 24, 40, 0.6); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; margin: 5px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="color: #f1f5f9; margin: 0;">{row['Coin']} <span style="font-size: 14px; color: #64748b;">{row['Symbol']}</span></h3>
                <span style="font-size: 20px; font-weight: 700; color: #fbbf24;">#{row['Rank']}</span>
            </div>
            <div style="margin: 10px 0;">
                <span class="{row['Badge']}">{row['Signal']}</span>
                <span style="float: right; color: #f1f5f9; font-size: 20px; font-weight: 700;">{row['Score']}</span>
            </div>
            <div style="display: flex; gap: 16px; color: #94a3b8; font-size: 13px; flex-wrap: wrap;">
                <span>24h: <span style="color: {'#00ff88' if row['24H %'] > 0 else '#ff3b5c'}">{row['24H %']}%</span></span>
                <span>7d: <span style="color: {'#00ff88' if row['7D %'] > 0 else '#ff3b5c'}">{row['7D %']}%</span></span>
                <span>Price: ${row['Price']:.4f}</span>
            </div>
            <div style="color: #64748b; font-size: 12px; margin-top: 6px;">
                Volume: {row['Volume (M)']}M {row['Volume Trend']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================
st.divider()
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 All Coins", "🔥 Strong Buy", "🟢 Buy", "💎 Watchlist", "📈 Charts", "📥 Export"
])

with tab1:
    st.dataframe(df, use_container_width=True, hide_index=True, height=500)

with tab2:
    strong = df[df["Signal"] == "🔥 STRONG BUY"]
    if not strong.empty:
        st.dataframe(strong, use_container_width=True, hide_index=True)
        st.success(f"🔥 Found {len(strong)} strong buy signals")
    else:
        st.info("No strong buy signals at the moment")

with tab3:
    buy = df[df["Signal"] == "🟢 BUY"]
    if not buy.empty:
        st.dataframe(buy, use_container_width=True, hide_index=True)
    else:
        st.info("No buy signals at the moment")

with tab4:
    watchlist_df = df[df["Symbol"].isin(st.session_state.watchlist)]
    if not watchlist_df.empty:
        st.dataframe(watchlist_df, use_container_width=True, hide_index=True)
    else:
        st.info("Add coins to watchlist")

with tab5:
    st.subheader("📊 Score Distribution")
    fig = px.histogram(df, x='Score', nbins=20, title='Score Distribution',
                       color_discrete_sequence=['#00ff88'])
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("🏆 Top 10 Coins")
    fig2 = px.bar(df.head(10), x='Coin', y='Score', title='Top 10 by Score',
                  color='Score', color_continuous_scale='Greens')
    fig2.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig2, use_container_width=True)

with tab6:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, f"scanner_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv")
    
    # Export to Excel
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Scanner', index=False)
        st.download_button("📥 Download Excel", output.getvalue(), 
                          f"scanner_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", 
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except:
        pass

# =========================================================
# AVOID LIST
# =========================================================
with st.expander("⚠️ Avoid List"):
    avoid = df[df["Signal"] == "🔴 AVOID"]
    if not avoid.empty:
        st.dataframe(avoid.head(30), use_container_width=True, hide_index=True)
    else:
        st.info("No coins to avoid")

# =========================================================
# COIN DETAIL
# =========================================================
st.divider()
st.subheader("📈 Coin Detail")

selected = st.selectbox("Select Coin", df["Symbol"].tolist(),
                        index=df["Symbol"].tolist().index(st.session_state.selected_symbol) 
                        if st.session_state.selected_symbol in df["Symbol"].values else 0)
st.session_state.selected_symbol = selected

row = df[df["Symbol"] == selected].iloc[0]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🪙 Coin", row["Coin"])
col2.metric("💰 Price", f"${row['Price']:,.4f}")
col3.metric("📈 24H", f"{row['24H %']}%", delta=f"{row['24H %']}%")
col4.metric("🧠 Score", f"{row['Score']}/100")
col5.metric("📊 Signal", row["Signal"])

# =========================================================
# AUTO REFRESH
# =========================================================
st_autorefresh(interval=refresh_minutes * 60000, key="refresh")

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption(
    f"🔄 Last updated: {st.session_state.last_update_time.strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Total: {len(df)} | Source: Yahoo Finance | "
    f"Telegram: {'✅' if BOT_TOKEN and CHAT_ID else '❌'} | "
    f"Refresh: {refresh_minutes}m"
)
