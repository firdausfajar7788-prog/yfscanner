import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🎮 Crypto Hunter V2",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS - THEME GAME
# =========================================================
st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0a1a2a 100%);
    }
    [data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 255, 136, 0.2);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 30px rgba(0, 255, 136, 0.05);
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 8px 40px rgba(0, 255, 136, 0.15);
        border-color: #00ff88;
    }
    
    .boss-card {
        background: linear-gradient(145deg, #1a0a2e, #2a0a3e);
        border: 2px solid #ffaa00;
        border-radius: 20px;
        padding: 25px;
        margin: 10px 0;
        animation: glow-pulse 2s infinite;
        box-shadow: 0 0 40px rgba(255, 170, 0, 0.1);
    }
    @keyframes glow-pulse {
        0% { box-shadow: 0 0 20px rgba(255, 170, 0, 0.1); }
        50% { box-shadow: 0 0 60px rgba(255, 170, 0, 0.3); }
        100% { box-shadow: 0 0 20px rgba(255, 170, 0, 0.1); }
    }
    
    .legendary {
        background: linear-gradient(135deg, #ffd700, #ff6b00) !important;
        color: #000 !important;
        font-weight: 900 !important;
        text-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
        animation: legendary-glow 1.5s infinite;
    }
    @keyframes legendary-glow {
        0% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.3); }
        50% { box-shadow: 0 0 60px rgba(255, 215, 0, 0.6); }
        100% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.3); }
    }
    
    .rare {
        background: linear-gradient(135deg, #9b59b6, #8e44ad) !important;
        color: #fff !important;
        border: 1px solid #9b59b6 !important;
    }
    
    .common {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    
    .stButton > button {
        background: linear-gradient(145deg, #00ff88, #00cc66);
        color: #000;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 40px rgba(0, 255, 136, 0.4);
    }
    
    .health-bar {
        height: 20px;
        border-radius: 10px;
        background: #1a1a2e;
        overflow: hidden;
    }
    .health-bar-fill {
        height: 100%;
        transition: width 1s ease;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE - GAME STATE
# =========================================================
if "player_score" not in st.session_state:
    st.session_state.player_score = 0
if "level" not in st.session_state:
    st.session_state.level = 1
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "combo" not in st.session_state:
    st.session_state.combo = 0
if "max_combo" not in st.session_state:
    st.session_state.max_combo = 0
if "found_coins" not in st.session_state:
    st.session_state.found_coins = []
if "achievements" not in st.session_state:
    st.session_state.achievements = []
if "last_scan_time" not in st.session_state:
    st.session_state.last_scan_time = datetime.now()

# =========================================================
# HEADER
# =========================================================
st.markdown("""
# 🎮 CRYPTO HUNTER V2
### `>> Filter: Hanya Koin Gak Aneh <<`
""")

col_level, col_xp, col_score, col_combo = st.columns(4)
col_level.metric("🎯 Level", f"Lv.{st.session_state.level}")
col_xp.metric("⭐ XP", f"{st.session_state.xp}/100")
col_score.metric("🏆 Score", st.session_state.player_score)
col_combo.metric("🔥 Combo", f"{st.session_state.combo}x")

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("🎯 Filter Koin")
    min_market_cap = st.selectbox("Min Market Cap", ["$10M", "$50M", "$100M", "$500M", "$1B"], index=2)
    min_price = st.selectbox("Min Price", ["$0.001", "$0.01", "$0.1", "$1"], index=1)
    
    scan_limit = st.slider("🔍 Scan Depth", 50, 300, 150)
    
    st.divider()
    
    # Telegram
    st.subheader("📱 Telegram Alert")
    default_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
    default_chat = st.secrets.get("TELEGRAM_CHAT_ID", "")
    BOT_TOKEN = st.text_input("Bot Token", type="password", value=default_token)
    CHAT_ID = st.text_input("Chat ID", value=default_chat)
    send_notifications = st.checkbox("🔔 Kirim Notifikasi", value=True)
    
    st.divider()
    
    st.subheader("📊 Status")
    st.metric("Total Hunted", len(st.session_state.found_coins))
    st.metric("Best Combo", f"{st.session_state.max_combo}x")
    st.metric("Achievements", len(st.session_state.achievements))
    
    if st.button("🔄 Start New Hunt", use_container_width=True):
        st.session_state.found_coins = []
        st.session_state.combo = 0
        st.cache_data.clear()
        st.rerun()

# =========================================================
# GET DATA - DENGAN FILTER
# =========================================================
@st.cache_data(ttl=300)
def get_coins_from_coingecko(limit=200):
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
            return resp.json()
        return []
    except:
        return []

@st.cache_data(ttl=300)
def get_yfinance_data_single(symbol, name):
    try:
        ticker = yf.Ticker(f"{symbol}-USD")
        info = ticker.info
        hist = ticker.history(period="7d", interval="1d")
        if hist.empty or len(hist) < 3:
            return None
        
        latest = hist.iloc[-1]
        price = latest["Close"]
        volume_24h = latest["Volume"]
        
        # Filter: harga harus masuk akal
        if price < 0.0001:
            return None
        
        if len(hist) >= 2:
            prev = hist.iloc[-2]
            change_24h = ((price - prev["Close"]) / prev["Close"]) * 100
        else:
            change_24h = 0
        
        if len(hist) >= 7:
            first = hist.iloc[0]
            change_7d = ((price - first["Close"]) / first["Close"]) * 100
        else:
            change_7d = 0
        
        volumes = hist["Volume"].tolist()
        avg_volume_7d = sum(volumes) / len(volumes) if volumes else volume_24h
        ratio = volume_24h / avg_volume_7d if avg_volume_7d > 0 else 1
        
        if ratio > 1.5: volume_trend = "🔼 SURGE"
        elif ratio > 1.3: volume_trend = "🔼 UP"
        elif ratio < 0.7: volume_trend = "🔽 DOWN"
        else: volume_trend = "➡️ STABLE"
        
        market_cap = info.get("marketCap", 0)
        
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
    except:
        return None

def calculate_rarity(score, volume_ratio):
    if score >= 85 and volume_ratio > 1.5:
        return "⚡ LEGENDARY", "legendary"
    elif score >= 75:
        return "💎 EPIC", "rare"
    elif score >= 60:
        return "🌟 RARE", "rare"
    elif score >= 45:
        return "🟢 COMMON", "common"
    else:
        return "💀 TRASH", "common"

def calculate_score(row):
    score = 0
    change_24h = row["24H %"]
    change_7d = row["7D %"]
    volume_ratio = row.get("Volume Ratio", 1)
    market_cap = row.get("Market Cap", 0)
    
    if change_24h > 10: score += 50
    elif change_24h > 5: score += 35
    elif change_24h > 2: score += 20
    elif change_24h > 0: score += 10
    
    if change_7d > 20: score += 20
    elif change_7d > 10 and change_24h > change_7d * 0.3: score += 15
    elif change_7d > 5: score += 10
    
    if volume_ratio > 2.0: score += 20
    elif volume_ratio > 1.5: score += 15
    elif volume_ratio > 1.3: score += 10
    
    if market_cap > 100_000_000_000: score += 15
    elif market_cap > 10_000_000_000: score += 10
    elif market_cap > 1_000_000_000: score += 5
    
    return score

# =========================================================
# MAIN SCAN
# =========================================================
# Parsing filter values
filter_map = {
    "$10M": 10_000_000,
    "$50M": 50_000_000,
    "$100M": 100_000_000,
    "$500M": 500_000_000,
    "$1B": 1_000_000_000
}
min_mcap_value = filter_map.get(min_market_cap, 100_000_000)

price_map = {
    "$0.001": 0.001,
    "$0.01": 0.01,
    "$0.1": 0.1,
    "$1": 1.0
}
min_price_value = price_map.get(min_price, 0.01)

with st.spinner("🔍 Hunting for treasures..."):
    coins_data = get_coins_from_coingecko(limit=scan_limit)
    if not coins_data:
        st.error("❌ Failed to get data")
        st.stop()
    
    # Filter CoinGecko dulu
    filtered_coins = []
    for coin in coins_data:
        mcap = coin.get("market_cap", 0)
        price = coin.get("current_price", 0)
        if mcap >= min_mcap_value and price >= min_price_value:
            filtered_coins.append(coin)
    
    st.info(f"🔍 Found {len(filtered_coins)} coins after filtering (from {len(coins_data)})")
    
    if not filtered_coins:
        st.warning("No coins passed the filter. Try lower thresholds!")
        st.stop()
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_coin = {
            executor.submit(get_yfinance_data_single, coin["symbol"].upper(), coin["name"]): coin
            for coin in filtered_coins
        }
        
        for idx, future in enumerate(as_completed(future_to_coin)):
            progress_bar.progress((idx + 1) / len(filtered_coins))
            status_text.text(f"🔎 Hunting {idx + 1}/{len(filtered_coins)}...")
            
            try:
                data = future.result()
                if data:
                    results.append(data)
            except:
                continue
            time.sleep(0.05)
    
    progress_bar.empty()
    status_text.empty()

if not results:
    st.warning("No valid data found. Try different filters!")
    st.stop()

# =========================================================
# PROCESS RESULTS
# =========================================================
processed = []
for data in results:
    score = calculate_score(data)
    rarity_text, rarity_class = calculate_rarity(score, data["Volume Ratio"])
    if score >= 80:
        signal = "🔥 STRONG BUY"
    elif score >= 65:
        signal = "🟢 BUY"
    elif score >= 45:
        signal = "🟡 WAIT"
    else:
        signal = "🔴 AVOID"
    
    processed.append({
        "Coin": data["Coin"],
        "Symbol": data["Symbol"],
        "Price": data["Price"],
        "24H %": round(data["24H %"], 2),
        "7D %": round(data["7D %"], 2),
        "Volume (M)": round(data["Volume (M)"], 1),
        "Score": score,
        "Signal": signal,
        "Rarity": rarity_text,
        "Rarity Class": rarity_class,
        "Volume Trend": data["Volume Trend"]
    })

df = pd.DataFrame(processed)
df = df.sort_values("Score", ascending=False).reset_index(drop=True)
df["Rank"] = df.index + 1

# =========================================================
# GAME REWARDS
# =========================================================
new_finds = []

legendary = df[df["Rarity"].str.contains("LEGENDARY")]
if not legendary.empty and legendary.iloc[0]["Symbol"] not in st.session_state.found_coins:
    st.session_state.player_score += 50
    st.session_state.xp += 25
    st.session_state.combo += 1
    if st.session_state.combo > st.session_state.max_combo:
        st.session_state.max_combo = st.session_state.combo
    if "legendary_hunter" not in st.session_state.achievements:
        st.session_state.achievements.append("legendary_hunter")
        st.balloons()

epic = df[(df["Rarity"].str.contains("EPIC")) & (df["Score"] > 70)]
if not epic.empty:
    for _, row in epic.iterrows():
        if row["Symbol"] not in st.session_state.found_coins:
            st.session_state.player_score += 20
            st.session_state.xp += 10

for _, row in df.iterrows():
    if row["Symbol"] not in st.session_state.found_coins:
        st.session_state.found_coins.append(row["Symbol"])

if st.session_state.xp >= 100:
    st.session_state.level += 1
    st.session_state.xp = 0
    st.balloons()
    st.success(f"🎉 LEVEL UP! You are now Level {st.session_state.level}!")

st.session_state.last_scan_time = datetime.now()

# =========================================================
# DISPLAY
# =========================================================
st.subheader("🏆 TOP HUNT")

if st.button("⚔️ Hunt Again!", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# =========================================================
# TOP CARD
# =========================================================
if not df.empty:
    top = df.iloc[0]
    rarity_emoji = "👑" if "LEGENDARY" in top["Rarity"] else "💎" if "EPIC" in top["Rarity"] else "🌟"
    
    st.markdown(f"""
    <div class="boss-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 28px; font-weight: 900; color: #fff;">{rarity_emoji} {top['Coin']}</span>
                <span style="font-size: 16px; color: #94a3b8; margin-left: 15px;">{top['Symbol']}</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 24px; font-weight: 900; color: #ffaa00;">{top['Score']}</span>
                <span style="font-size: 14px; color: #94a3b8;">/100</span>
                <div><span class="legendary" style="padding: 2px 12px; border-radius: 20px; font-size: 12px;">{top['Rarity']}</span></div>
            </div>
        </div>
        <div style="display: flex; gap: 30px; margin-top: 15px; color: #94a3b8; font-size: 14px; flex-wrap: wrap;">
            <span>💰 ${top['Price']:.4f}</span>
            <span>📈 <span style="color: {'#00ff88' if top['24H %'] > 0 else '#ff3b5c'}">{top['24H %']}%</span></span>
            <span>📊 {top['Signal']}</span>
            <span>{top['Volume Trend']}</span>
            <span>Rank #{top['Rank']}</span>
        </div>
        <div class="health-bar" style="margin-top: 10px;">
            <div class="health-bar-fill" style="width: {min(top['Score'], 100)}%; background: linear-gradient(90deg, #00ff88, #ffaa00);"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================
tab_legendary, tab_epic, tab_rare, tab_all = st.tabs([
    "👑 Legendary", "💎 Epic", "🌟 Rare", "📊 All"
])

with tab_legendary:
    legendary_df = df[df["Rarity"].str.contains("LEGENDARY")]
    if not legendary_df.empty:
        st.dataframe(legendary_df, use_container_width=True, hide_index=True)
        st.success(f"⚡ Found {len(legendary_df)} Legendary!")
    else:
        st.info("No Legendary found. Keep hunting!")

with tab_epic:
    epic_df = df[df["Rarity"].str.contains("EPIC")]
    if not epic_df.empty:
        st.dataframe(epic_df, use_container_width=True, hide_index=True)
    else:
        st.info("No Epic found.")

with tab_rare:
    rare_df = df[df["Rarity"].str.contains("RARE") & ~df["Rarity"].str.contains("EPIC")]
    if not rare_df.empty:
        st.dataframe(rare_df, use_container_width=True, hide_index=True)
    else:
        st.info("No Rare found.")

with tab_all:
    st.dataframe(df, use_container_width=True, height=400, hide_index=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, f"crypto_hunt_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv")

# =========================================================
# ACHIEVEMENTS
# =========================================================
with st.expander("🏅 Achievements", expanded=False):
    if st.session_state.achievements:
        achievement_names = {
            "legendary_hunter": "👑 Legendary Hunter - Found your first Legendary!",
            "epic_hunter": "💎 Epic Hunter - Found your first Epic!",
            "combo_master": "🔥 Combo Master - 5x combo achieved!",
            "scanner_pro": "📊 Scanner Pro - Scanned 100+ coins!"
        }
        for ach in st.session_state.achievements:
            st.success(f"✅ {achievement_names.get(ach, ach)}")
    else:
        st.info("No achievements yet. Hunt more!")

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption(
    f"⚔️ Total Hunted: {len(st.session_state.found_coins)} coins | "
    f"Level: {st.session_state.level} | "
    f"Combo: {st.session_state.combo}x | "
    f"Best Combo: {st.session_state.max_combo}x | "
    f"Filter: MCap > {min_market_cap}, Price > {min_price}"
)

st_autorefresh(interval=300000, key="refresh")
