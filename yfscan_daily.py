import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Full Crypto Scanner - All Coins",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
    .stApp { background: #0a0a1a; }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #111827, #0b1220);
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 20px rgba(0,255,255,0.05);
    }
    .signal-strong-buy {
        background: linear-gradient(135deg, rgba(0,255,136,0.2), rgba(0,255,136,0.05));
        border: 1px solid #00ff88;
        border-radius: 8px;
        padding: 4px 12px;
        color: #00ff88;
        font-weight: 600;
    }
    .signal-buy {
        background: linear-gradient(135deg, rgba(0,200,255,0.2), rgba(0,200,255,0.05));
        border: 1px solid #00c8ff;
        border-radius: 8px;
        padding: 4px 12px;
        color: #00c8ff;
        font-weight: 600;
    }
    .signal-wait {
        background: linear-gradient(135deg, rgba(255,170,0,0.2), rgba(255,170,0,0.05));
        border: 1px solid #ffaa00;
        border-radius: 8px;
        padding: 4px 12px;
        color: #ffaa00;
        font-weight: 600;
    }
    .signal-avoid {
        background: linear-gradient(135deg, rgba(255,59,92,0.2), rgba(255,59,92,0.05));
        border: 1px solid #ff3b5c;
        border-radius: 8px;
        padding: 4px 12px;
        color: #ff3b5c;
        font-weight: 600;
    }
    .stButton > button {
        background: linear-gradient(145deg, #00ff88, #00cc66);
        color: #000;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================
if "selected_symbol" not in st.session_state:
    st.session_state.selected_symbol = "BTC"
if "last_notified" not in st.session_state:
    st.session_state.last_notified = {}
if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = datetime.now()

# =========================================================
# HEADER
# =========================================================
st.title("📊 Full Crypto Scanner")
st.caption("Scan SEMUA coin yang tersedia di Yahoo Finance + CoinGecko")
col_time, _ = st.columns([2, 3])
with col_time:
    st.caption(f"🕐 Last updated: {st.session_state.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("⚙️ Settings")
    currency = st.selectbox("💱 Currency", ["USD", "IDR"])
    
    st.divider()
    
    # Jumlah coin yang di-scan
    scan_limit = st.slider("📊 Jumlah Coin di-Scan", 50, 500, 200, step=50)
    
    st.divider()
    
    # Telegram
    st.subheader("📱 Telegram Alert")
    default_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
    default_chat = st.secrets.get("TELEGRAM_CHAT_ID", "")
    BOT_TOKEN = st.text_input("Bot Token", type="password", value=default_token)
    CHAT_ID = st.text_input("Chat ID", value=default_chat)
    send_notifications = st.checkbox("🔔 Kirim Notifikasi", value=True)
    notify_min_score = st.slider("Min Score untuk Notifikasi", 50, 100, 65)
    
    col_test1, col_test2 = st.columns(2)
    with col_test1:
        if st.button("🚀 Test Telegram", use_container_width=True):
            if BOT_TOKEN and CHAT_ID:
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    r = requests.post(url, json={"chat_id": CHAT_ID, "text": "🚀 Full Scanner aktif!"}, timeout=10)
                    st.success("✅ Pesan test terkirim!" if r.status_code == 200 else f"❌ Error {r.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("⚠️ Isi Bot Token dan Chat ID")
    with col_test2:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    
    st.subheader("📊 Status")
    st.metric("Coin Source", "CoinGecko → YFinance")
    st.metric("Auto Refresh", "10 menit")

# =========================================================
# FUNGSI AMBIL KURS IDR
# =========================================================
@st.cache_data(ttl=3600)
def get_usd_to_idr():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()["rates"]["IDR"]
    except:
        pass
    return 15500

usd_to_idr = get_usd_to_idr()

# =========================================================
# FUNGSI TELEGRAM
# =========================================================
def send_telegram(bot_token, chat_id, message):
    if not bot_token or not chat_id:
        return False, "Kosong"
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        r = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)

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
# 1. AMBIL DAFTAR SEMUA COIN DARI COINGECKO
# =========================================================
@st.cache_data(ttl=3600)
def get_all_coins_from_coingecko(limit=200):
    """Ambil daftar coin dari CoinGecko (nama + symbol)"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h,7d"
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # Ambil symbol dan name saja
            return [{"symbol": coin["symbol"].upper(), "name": coin["name"]} for coin in data]
        else:
            st.error(f"❌ CoinGecko error: {resp.status_code}")
            return []
    except Exception as e:
        st.error(f"❌ CoinGecko exception: {e}")
        return []

# =========================================================
# 2. AMBIL DATA DARI YFINANCE UNTUK 1 COIN
# =========================================================
def get_yfinance_data_single(symbol, name):
    """Ambil data dari Yahoo Finance untuk 1 coin"""
    try:
        ticker = yf.Ticker(f"{symbol}-USD")
        
        # Coba dapatkan info
        info = ticker.info
        
        # Ambil data historis 7 hari
        hist = ticker.history(period="7d", interval="1d")
        if hist.empty or len(hist) < 3:
            return None
        
        latest = hist.iloc[-1]
        price = latest["Close"]
        volume_24h = latest["Volume"]
        
        # Change 24h
        if len(hist) >= 2:
            prev = hist.iloc[-2]
            change_24h = ((price - prev["Close"]) / prev["Close"]) * 100
        else:
            change_24h = 0
        
        # Change 7d
        if len(hist) >= 7:
            first = hist.iloc[0]
            change_7d = ((price - first["Close"]) / first["Close"]) * 100
        else:
            change_7d = 0
        
        # Volume trend
        volumes = hist["Volume"].tolist()
        avg_volume_7d = sum(volumes) / len(volumes) if volumes else volume_24h
        ratio = volume_24h / avg_volume_7d if avg_volume_7d > 0 else 1
        
        if ratio > 1.3:
            volume_trend = "🔼"
        elif ratio < 0.7:
            volume_trend = "🔽"
        else:
            volume_trend = "➡️"
        
        # Market cap dari info
        market_cap = info.get("marketCap", 0) or info.get("totalAssets", 0)
        
        return {
            "Coin": name,
            "Symbol": symbol,
            "Price": price,
            "24H %": change_24h,
            "7D %": change_7d,
            "Volume (M)": volume_24h / 1_000_000,
            "Volume Trend": volume_trend,
            "Volume Ratio": ratio,
            "Market Cap": market_cap
        }
    except Exception as e:
        return None

# =========================================================
# 3. HITUNG SCORE
# =========================================================
def calculate_score(row):
    score = 0
    change_24h = row["24H %"]
    change_7d = row["7D %"]
    volume_ratio = row.get("Volume Ratio", 1)
    market_cap = row.get("Market Cap", 0)
    
    # 24h change (max 50)
    if change_24h > 10: score += 50
    elif change_24h > 5: score += 35
    elif change_24h > 2: score += 20
    elif change_24h > 0: score += 10
    
    # 7d change (max 20)
    if change_7d > 20: score += 20
    elif change_7d > 10 and change_24h > change_7d * 0.3: score += 15
    elif change_7d > 5: score += 10
    
    # Volume surge (max 20)
    if volume_ratio > 2.0: score += 20
    elif volume_ratio > 1.5: score += 15
    elif volume_ratio > 1.3: score += 10
    
    # Market cap bonus (max 15)
    if market_cap > 100_000_000_000: score += 15  # > 100B
    elif market_cap > 10_000_000_000: score += 10  # > 10B
    elif market_cap > 1_000_000_000: score += 5   # > 1B
    
    # Signal
    if score >= 80: signal = "🔥 STRONG BUY"
    elif score >= 65: signal = "🟢 BUY"
    elif score >= 45: signal = "🟡 WAIT"
    else: signal = "🔴 AVOID"
    
    return score, signal

# =========================================================
# MAIN - SCAN SEMUA
# =========================================================
st.info(f"🔄 Mengambil daftar {scan_limit} coin dari CoinGecko...")

# 1. Ambil daftar coin dari CoinGecko
coin_list = get_all_coins_from_coingecko(limit=scan_limit)

if not coin_list:
    st.error("❌ Gagal mengambil daftar coin dari CoinGecko")
    st.stop()

st.success(f"✅ Mendapat {len(coin_list)} coin dari CoinGecko")

# 2. Ambil data dari YFinance untuk setiap coin
st.info("📊 Mengambil data dari Yahoo Finance...")

results = []
progress_bar = st.progress(0)
status_text = st.empty()

with ThreadPoolExecutor(max_workers=15) as executor:
    future_to_coin = {
        executor.submit(get_yfinance_data_single, coin["symbol"], coin["name"]): coin
        for coin in coin_list
    }
    
    for idx, future in enumerate(as_completed(future_to_coin)):
        progress_bar.progress((idx + 1) / len(coin_list))
        status_text.text(f"🔄 Memproses {idx + 1}/{len(coin_list)}...")
        
        try:
            data = future.result()
            if data:
                results.append(data)
        except Exception as e:
            continue
        time.sleep(0.05)

progress_bar.empty()
status_text.empty()

if not results:
    st.error("❌ Tidak ada data yang berhasil diambil")
    st.stop()

# 3. Proses data
processed_results = []
for data in results:
    score, signal = calculate_score(data)
    processed_results.append({
        "Coin": data["Coin"],
        "Symbol": data["Symbol"],
        "Price": data["Price"],
        "24H %": round(data["24H %"], 2),
        "7D %": round(data["7D %"], 2),
        "Volume (M)": round(data["Volume (M)"], 1),
        "Volume Trend": data["Volume Trend"],
        "Score": score,
        "Signal": signal,
        "Market Cap": data.get("Market Cap", 0)
    })

df = pd.DataFrame(processed_results)
df = df.sort_values("Score", ascending=False).reset_index(drop=True)
df["Rank"] = df.index + 1

# Update waktu
st.session_state.last_update_time = datetime.now()

# =========================================================
# TELEGRAM NOTIFICATION
# =========================================================
if BOT_TOKEN and CHAT_ID and send_notifications:
    new_signals = df[(df["Signal"].isin(["🟢 BUY", "🔥 STRONG BUY"])) & (df["Score"] >= notify_min_score)]
    notified = 0
    failed = 0
    for _, row in new_signals.iterrows():
        symbol = row["Symbol"]
        signal = row["Signal"]
        if st.session_state.last_notified.get(symbol) != signal:
            msg = format_telegram_message(row)
            ok, _ = send_telegram(BOT_TOKEN, CHAT_ID, msg)
            if ok:
                st.session_state.last_notified[symbol] = signal
                notified += 1
            else:
                failed += 1
            time.sleep(0.3)
    if notified: st.sidebar.success(f"✅ {notified} notifikasi terkirim!")
    if failed: st.sidebar.error(f"❌ {failed} gagal!")

# =========================================================
# METRICS
# =========================================================
avg_score = df["Score"].mean()
mood = "🟢 BULLISH" if avg_score >= 65 else "🟡 NEUTRAL" if avg_score >= 45 else "🔴 BEARISH"
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📊 Market Mood", mood)
c2.metric("🪙 Coins Scanned", len(df))
c3.metric("📈 Average Score", round(avg_score, 1))
c4.metric("🔥 Strong Buy", len(df[df["Signal"] == "🔥 STRONG BUY"]))
c5.metric("🟢 Buy", len(df[df["Signal"] == "🟢 BUY"]))

# =========================================================
# TOP 3
# =========================================================
st.subheader("🔥 Top 3 Opportunities")
top3 = df.head(3)
cols_top = st.columns(3)
for idx, (_, row) in enumerate(top3.iterrows()):
    with cols_top[idx]:
        cls = "signal-strong-buy" if "STRONG" in row["Signal"] else "signal-buy"
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #111827, #0b1220); border:1px solid #1e293b; border-radius:16px; padding:20px; margin:5px;">
            <h3 style="color:#f1f5f9; margin:0;">{row['Coin']} <span style="font-size:14px; color:#94a3b8;">{row['Symbol']}</span></h3>
            <div style="margin:10px 0;"><span class="{cls}">{row['Signal']}</span>
            <span style="float:right; color:#f1f5f9; font-size:20px; font-weight:700;">{row['Score']}</span></div>
            <div style="display:flex; gap:20px; color:#94a3b8; font-size:14px;">
                <span>24h: <span style="color:{'#00ff88' if row['24H %']>0 else '#ff3b5c'}">{row['24H %']}%</span></span>
                <span>Rank: #{row['Rank']}</span>
            </div>
            <div style="color:#94a3b8; font-size:14px; margin-top:8px;">
                Price: ${row['Price']:,.4f} | Volume: {row['Volume (M)']}M {row.get('Volume Trend', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# TABEL
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Breakout Watchlist", "💎 Strong Buy", "🟢 Buy", "📊 Full Scanner"])
with tab1:
    breakout = df[(df["24H %"] > 5) & (df["Score"] > 40)]
    if not breakout.empty:
        st.dataframe(breakout.head(20), use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada breakout")
with tab2:
    strong = df[df["Signal"] == "🔥 STRONG BUY"]
    if not strong.empty:
        st.dataframe(strong, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada Strong Buy")
with tab3:
    buy = df[df["Signal"] == "🟢 BUY"]
    if not buy.empty:
        st.dataframe(buy, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada Buy")
with tab4:
    st.dataframe(df, use_container_width=True, height=500, hide_index=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, f"crypto_scanner_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv")

# =========================================================
# AVOID
# =========================================================
with st.expander("⚠️ Avoid List"):
    avoid = df[df["Signal"] == "🔴 AVOID"]
    if not avoid.empty:
        st.dataframe(avoid.head(30), use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada coin yang perlu dihindari")

# =========================================================
# COIN DETAIL
# =========================================================
st.divider()
st.subheader("📈 Coin Detail")
if not df.empty:
    selected = st.selectbox("Select Coin", df["Symbol"].tolist())
    st.session_state.selected_symbol = selected
    row = df[df["Symbol"] == selected].iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🪙 Coin", row["Coin"])
    col2.metric("💰 Price", f"{row['Price']:,.4f} USD")
    col3.metric("📈 24H Change", f"{row['24H %']}%")
    col4.metric("🧠 Score", f"{row['Score']}/100")

# =========================================================
# AUTO REFRESH
# =========================================================
st_autorefresh(interval=600000, key="refresh")

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption(
    f"🔄 Last updated: {st.session_state.last_update_time.strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Total: {len(df)} | Sumber: CoinGecko → Yahoo Finance | "
    f"Telegram: {'✅' if BOT_TOKEN and CHAT_ID else '❌'}"
)
