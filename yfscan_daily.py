import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🎮 Crypto Hunter AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS - THEME GAME + AI
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
    
    .ai-buy { color: #00ff88; font-weight: 700; }
    .ai-sell { color: #ff3b5c; font-weight: 700; }
    .ai-hold { color: #ffaa00; font-weight: 700; }
    
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
    
    .ai-badge {
        display: inline-block;
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        margin-left: 8px;
    }
    .ai-badge-buy { background: rgba(0,255,136,0.2); color: #00ff88; border: 1px solid #00ff88; }
    .ai-badge-sell { background: rgba(255,59,92,0.2); color: #ff3b5c; border: 1px solid #ff3b5c; }
    .ai-badge-hold { background: rgba(255,170,0,0.2); color: #ffaa00; border: 1px solid #ffaa00; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE - GAME + AI
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
if "ai_trained" not in st.session_state:
    st.session_state.ai_trained = False
if "ai_accuracy" not in st.session_state:
    st.session_state.ai_accuracy = 0

# =========================================================
# HEADER
# =========================================================
st.markdown("""
# 🎮 CRYPTO HUNTER AI
### `>> AI-Powered Crypto Scanner <<`
""")

col_level, col_xp, col_score, col_combo, col_ai = st.columns(5)
col_level.metric("🎯 Level", f"Lv.{st.session_state.level}")
col_xp.metric("⭐ XP", f"{st.session_state.xp}/100")
col_score.metric("🏆 Score", st.session_state.player_score)
col_combo.metric("🔥 Combo", f"{st.session_state.combo}x")
col_ai.metric("🧠 AI Accuracy", f"{st.session_state.ai_accuracy:.1f}%" if st.session_state.ai_trained else "⚡ Training...")

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
    
    st.subheader("🧠 AI Settings")
    ai_confidence_threshold = st.slider("AI Confidence Threshold", 50, 90, 65, step=5,
                                        help="Minimal confidence untuk rekomendasi AI")
    train_on_historical = st.checkbox("🔄 Train AI on historical data", value=True)
    
    if st.button("🧠 Retrain AI Now!", use_container_width=True):
        st.session_state.ai_trained = False
        st.cache_data.clear()
        st.rerun()
    
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
# AI RANDOM FOREST CLASS
# =========================================================
class AIPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.accuracy = 0
        self.features = []
    
    def _extract_features(self, df):
        """Ekstrak fitur dari dataframe"""
        features = pd.DataFrame()
        
        # Price features
        features['close'] = df['Close']
        features['high'] = df['High']
        features['low'] = df['Low']
        features['volume'] = df['Volume']
        
        # Returns
        features['return_1'] = df['Close'].pct_change()
        features['return_5'] = df['Close'].pct_change(5)
        features['return_10'] = df['Close'].pct_change(10)
        
        # Technical indicators (sederhana)
        features['volatility'] = df['Close'].rolling(10).std()
        
        # Volume ratio
        features['volume_ma'] = df['Volume'].rolling(5).mean()
        features['volume_ratio'] = df['Volume'] / (features['volume_ma'] + 0.001)
        
        features = features.dropna()
        self.features = features.columns.tolist()
        return features
    
    def train(self, df):
        """Train AI model"""
        if len(df) < 50:
            return False
        
        features = self._extract_features(df)
        if features.empty:
            return False
        
        # Target: apakah harga naik >2% dalam 3 hari ke depan?
        future_return = df['Close'].shift(-3) / df['Close'] - 1
        target = pd.Series(index=df.index, dtype=int)
        target[future_return > 0.02] = 1  # BUY
        target[future_return < -0.02] = 2  # SELL
        target[future_return.abs() <= 0.02] = 0  # HOLD
        
        # Align features & target
        valid_idx = features.index.intersection(target.dropna().index)
        X = features.loc[valid_idx]
        y = target.loc[valid_idx]
        
        if len(X) < 30:
            return False
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=50,
            max_depth=8,
            random_state=42,
            n_jobs=-1
        )
        
        # Split untuk validasi
        split_idx = int(len(X_scaled) * 0.8)
        X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        if len(X_train) < 10 or len(X_test) < 5:
            self.model.fit(X_scaled, y)
            self.is_trained = True
            self.accuracy = 0.5
            return True
        
        self.model.fit(X_train, y_train)
        
        # Hitung akurasi
        y_pred = self.model.predict(X_test)
        self.accuracy = (y_pred == y_test).mean()
        self.is_trained = True
        
        return True
    
    def predict(self, df):
        """Prediksi untuk data terbaru"""
        default = {
            'signal': 0, 
            'signal_text': '🟡 HOLD', 
            'confidence': 0,
            'buy_prob': 0,
            'sell_prob': 0,
            'hold_prob': 0
        }
        
        if not self.is_trained or len(df) < 10:
            return default
        
        features = self._extract_features(df)
        if features.empty:
            return default
        
        X = features.iloc[-1:]
        if X.empty or X.isnull().all().all():
            return default
        
        try:
            X_scaled = self.scaler.transform(X)
            pred = self.model.predict(X_scaled)[0]
            proba = self.model.predict_proba(X_scaled)[0]
            
            # Pastikan proba punya 3 elemen
            if len(proba) < 3:
                proba = list(proba) + [0] * (3 - len(proba))
            
            proba_sum = sum(proba)
            if proba_sum > 0:
                proba = [p / proba_sum for p in proba]
            
            # Signal mapping
            signal_map = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
            signal_text_map = {0: '🟡 HOLD', 1: '🟢 BUY', 2: '🔴 SELL'}
            
            return {
                'signal': int(pred),
                'signal_text': signal_text_map.get(pred, '🟡 HOLD'),
                'confidence': float(max(proba) * 100),
                'buy_prob': float(proba[1] * 100) if len(proba) > 1 else 0,
                'sell_prob': float(proba[2] * 100) if len(proba) > 2 else 0,
                'hold_prob': float(proba[0] * 100) if len(proba) > 0 else 0
            }
        except Exception as e:
            return default

# =========================================================
# GET DATA
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
def get_yfinance_data_full(symbol, name):
    """Ambil data lengkap dari Yahoo Finance untuk AI training + scan"""
    try:
        ticker = yf.Ticker(f"{symbol}-USD")
        info = ticker.info
        
        # Ambil data historis 30 hari untuk AI training
        hist = ticker.history(period="30d", interval="1d")
        if hist.empty or len(hist) < 10:
            return None
        
        # Data terbaru untuk scan
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
        avg_volume_7d = sum(volumes[-7:]) / min(len(volumes), 7) if len(volumes) >= 7 else volume_24h
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
            "Market Cap": market_cap,
            "Historical": hist  # Untuk AI training
        }
    except Exception as e:
        return None

# =========================================================
# CALCULATE SCORE + RARITY
# =========================================================
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

def calculate_rarity(score, volume_ratio, ai_signal, ai_confidence):
    """Rarity dengan tambahan AI boost"""
    base_rarity = ""
    if score >= 85 and volume_ratio > 1.5:
        base_rarity = "⚡ LEGENDARY"
    elif score >= 75:
        base_rarity = "💎 EPIC"
    elif score >= 60:
        base_rarity = "🌟 RARE"
    elif score >= 45:
        base_rarity = "🟢 COMMON"
    else:
        base_rarity = "💀 TRASH"
    
    # AI Boost: jika AI BUY dengan confidence tinggi, naikkan rarity
    if ai_signal == "🟢 BUY" and ai_confidence > 70:
        if "COMMON" in base_rarity:
            return "🌟 RARE", "rare"
        elif "RARE" in base_rarity:
            return "💎 EPIC", "rare"
        elif "EPIC" in base_rarity:
            return "⚡ LEGENDARY", "legendary"
    
    # AI SELL dengan confidence tinggi → turunkan rarity
    if ai_signal == "🔴 SELL" and ai_confidence > 70:
        if "LEGENDARY" in base_rarity:
            return "💎 EPIC", "rare"
        elif "EPIC" in base_rarity:
            return "🌟 RARE", "rare"
    
    # Default
    if "LEGENDARY" in base_rarity:
        return base_rarity, "legendary"
    elif "EPIC" in base_rarity:
        return base_rarity, "rare"
    elif "RARE" in base_rarity:
        return base_rarity, "rare"
    else:
        return base_rarity, "common"

def get_signal_from_score(score):
    if score >= 80: return "🔥 STRONG BUY"
    elif score >= 65: return "🟢 BUY"
    elif score >= 45: return "🟡 WAIT"
    else: return "🔴 AVOID"

# =========================================================
# MAIN SCAN
# =========================================================
filter_map = {"$10M": 10_000_000, "$50M": 50_000_000, "$100M": 100_000_000, 
              "$500M": 500_000_000, "$1B": 1_000_000_000}
min_mcap_value = filter_map.get(min_market_cap, 100_000_000)

price_map = {"$0.001": 0.001, "$0.01": 0.01, "$0.1": 0.1, "$1": 1.0}
min_price_value = price_map.get(min_price, 0.01)

with st.spinner("🧠 AI is thinking... Hunting for treasures..."):
    # 1. Ambil data dari CoinGecko
    coins_data = get_coins_from_coingecko(limit=scan_limit)
    if not coins_data:
        st.error("❌ Failed to get data")
        st.stop()
    
    # 2. Filter awal
    filtered_coins = []
    for coin in coins_data:
        mcap = coin.get("market_cap", 0)
        price = coin.get("current_price", 0)
        if mcap >= min_mcap_value and price >= min_price_value:
            filtered_coins.append(coin)
    
    if not filtered_coins:
        st.warning("No coins passed the filter. Try lower thresholds!")
        st.stop()
    
    # 3. Ambil data dari YFinance
    results = []
    all_historical = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_coin = {
            executor.submit(get_yfinance_data_full, coin["symbol"].upper(), coin["name"]): coin
            for coin in filtered_coins
        }
        
        for idx, future in enumerate(as_completed(future_to_coin)):
            progress_bar.progress((idx + 1) / len(filtered_coins))
            status_text.text(f"🧠 AI Analyzing {idx + 1}/{len(filtered_coins)}...")
            
            try:
                data = future.result()
                if data:
                    results.append(data)
                    # Simpan historical untuk AI training
                    if data.get("Historical") is not None:
                        all_historical[data["Symbol"]] = data["Historical"]
            except:
                continue
            time.sleep(0.05)
    
    progress_bar.empty()
    status_text.empty()

if not results:
    st.warning("No valid data found. Try different filters!")
    st.stop()

# =========================================================
# TRAIN AI
# =========================================================
ai_predictor = AIPredictor()
total_accuracy = 0
trained_count = 0

if train_on_historical and all_historical:
    status_text.text("🧠 Training AI on historical data...")
    
    for symbol, hist_df in all_historical.items():
        if len(hist_df) >= 30:
            if ai_predictor.train(hist_df):
                trained_count += 1
                total_accuracy += ai_predictor.accuracy
    
    if trained_count > 0:
        st.session_state.ai_trained = True
        st.session_state.ai_accuracy = (total_accuracy / trained_count) * 100
        st.success(f"✅ AI trained on {trained_count} coins! Accuracy: {st.session_state.ai_accuracy:.1f}%")
    else:
        # Fallback: train dengan data gabungan
        combined_df = pd.concat([h for h in all_historical.values() if h is not None])
        if len(combined_df) > 50:
            if ai_predictor.train(combined_df):
                st.session_state.ai_trained = True
                st.session_state.ai_accuracy = ai_predictor.accuracy * 100
                st.success(f"✅ AI trained on combined data! Accuracy: {st.session_state.ai_accuracy:.1f}%")
            else:
                st.warning("⚠️ AI training failed. Using rule-based signals only.")
        else:
            st.warning("⚠️ Not enough data for AI. Using rule-based signals only.")

# =========================================================
# PROCESS RESULTS WITH AI
# =========================================================
processed = []
for data in results:
    score = calculate_score(data)
    
    # AI Prediction
    ai_pred = None
    if st.session_state.ai_trained and data.get("Historical") is not None:
        hist = data["Historical"]
        if len(hist) >= 10:
            ai_pred = ai_predictor.predict(hist)
    
    # Signal
    base_signal = get_signal_from_score(score)
    
    # Gabungkan AI dengan base signal
    final_signal = base_signal
    ai_signal_text = "⚡ No AI"
    ai_confidence = 0
    ai_buy_prob = 0
    ai_sell_prob = 0
    ai_hold_prob = 0
    
    if ai_pred and st.session_state.ai_trained:
        ai_signal_text = ai_pred['signal_text']
        ai_confidence = ai_pred['confidence']
        ai_buy_prob = ai_pred['buy_prob']
        ai_sell_prob = ai_pred['sell_prob']
        ai_hold_prob = ai_pred['hold_prob']
        
        # AI Boost: jika AI BUY dengan confidence tinggi
        if ai_confidence >= ai_confidence_threshold:
            if ai_signal_text == "🟢 BUY" and score > 50:
                final_signal = "🔥 STRONG BUY (AI)"
            elif ai_signal_text == "🔴 SELL" and score < 60:
                final_signal = "🔴 STRONG SELL (AI)"
            elif ai_signal_text == "🟢 BUY":
                final_signal = "🟢 BUY (AI)"
            elif ai_signal_text == "🔴 SELL":
                final_signal = "🔴 SELL (AI)"
    
    # AI Confidence badge
    ai_badge_class = "ai-badge-hold"
    if ai_signal_text == "🟢 BUY": ai_badge_class = "ai-badge-buy"
    elif ai_signal_text == "🔴 SELL": ai_badge_class = "ai-badge-sell"
    
    # Rarity
    rarity_text, rarity_class = calculate_rarity(score, data["Volume Ratio"], ai_signal_text, ai_confidence)
    
    processed.append({
        "Coin": data["Coin"],
        "Symbol": data["Symbol"],
        "Price": data["Price"],
        "24H %": round(data["24H %"], 2),
        "7D %": round(data["7D %"], 2),
        "Volume (M)": round(data["Volume (M)"], 1),
        "Score": score,
        "Signal": final_signal,
        "AI Signal": ai_signal_text,
        "AI Confidence": f"{ai_confidence:.0f}%" if ai_confidence > 0 else "N/A",
        "Rarity": rarity_text,
        "Rarity Class": rarity_class,
        "Volume Trend": data["Volume Trend"],
        "AI Buy %": f"{ai_buy_prob:.0f}%",
        "AI Sell %": f"{ai_sell_prob:.0f}%",
        "AI Hold %": f"{ai_hold_prob:.0f}%"
    })

df = pd.DataFrame(processed)
df = df.sort_values("Score", ascending=False).reset_index(drop=True)
df["Rank"] = df.index + 1

# =========================================================
# GAME REWARDS
# =========================================================
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
# TOP CARD WITH AI
# =========================================================
if not df.empty:
    top = df.iloc[0]
    rarity_emoji = "👑" if "LEGENDARY" in top["Rarity"] else "💎" if "EPIC" in top["Rarity"] else "🌟"
    
    ai_badge = ""
    if "AI" in str(top["Signal"]):
        ai_badge = '<span class="ai-badge ai-badge-buy">🤖 AI</span>'
    
    st.markdown(f"""
    <div class="boss-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 28px; font-weight: 900; color: #fff;">{rarity_emoji} {top['Coin']}</span>
                <span style="font-size: 16px; color: #94a3b8; margin-left: 15px;">{top['Symbol']}</span>
                {ai_badge}
            </div>
            <div style="text-align: right;">
                <span style="font-size: 24px; font-weight: 900; color: #ffaa00;">{top['Score']}</span>
                <span style="font-size: 14px; color: #94a3b8;">/100</span>
                <div><span class="legendary" style="padding: 2px 12px; border-radius: 20px; font-size: 12px;">{top['Rarity']}</span></div>
            </div>
        </div>
        <div style="display: flex; gap: 20px; margin-top: 15px; color: #94a3b8; font-size: 14px; flex-wrap: wrap;">
            <span>💰 ${top['Price']:.4f}</span>
            <span>📈 <span style="color: {'#00ff88' if top['24H %'] > 0 else '#ff3b5c'}">{top['24H %']}%</span></span>
            <span>📊 {top['Signal']}</span>
            <span>{top['Volume Trend']}</span>
            <span>🧠 {top['AI Signal']} ({top['AI Confidence']})</span>
            <span>Rank #{top['Rank']}</span>
        </div>
        <div style="display: flex; gap: 20px; margin-top: 8px; font-size: 12px; color: #64748b;">
            <span>Buy: {top['AI Buy %']}</span>
            <span>Sell: {top['AI Sell %']}</span>
            <span>Hold: {top['AI Hold %']}</span>
        </div>
        <div class="health-bar" style="margin-top: 10px;">
            <div class="health-bar-fill" style="width: {min(top['Score'], 100)}%; background: linear-gradient(90deg, #00ff88, #ffaa00);"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================
tab_legendary, tab_epic, tab_rare, tab_ai_recommend, tab_all = st.tabs([
    "👑 Legendary", "💎 Epic", "🌟 Rare", "🧠 AI Recommendations", "📊 All"
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

with tab_ai_recommend:
    st.subheader("🧠 AI Recommendations (Confidence ≥ Threshold)")
    ai_recommend = df[(df["AI Confidence"] != "N/A") & 
                      (df["AI Signal"].isin(["🟢 BUY", "🔴 SELL"]))]
    if not ai_recommend.empty:
        st.dataframe(ai_recommend, use_container_width=True, hide_index=True)
        st.caption(f"🎯 AI Confidence Threshold: {ai_confidence_threshold}%")
    else:
        st.info("No AI recommendations yet. Try lowering the threshold or scanning more coins.")

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
    f"🧠 AI: {'✅ Trained' if st.session_state.ai_trained else '❌ Not Trained'} | "
    f"Filter: MCap > {min_market_cap}, Price > {min_price}"
)

st_autorefresh(interval=300000, key="refresh")
