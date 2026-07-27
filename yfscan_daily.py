import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Crypto Hunter AI Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS - PROFESSIONAL DARK THEME
# =========================================================
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: #0b0e1a;
    }
    
    /* Cards */
    .metric-card {
        background: linear-gradient(145deg, #141824, #0d1120);
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 18px 20px;
        margin: 6px 0;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .metric-card:hover {
        border-color: #00ff88;
        box-shadow: 0 4px 30px rgba(0,255,136,0.08);
        transform: translateY(-2px);
    }
    .metric-label {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .metric-value {
        color: #f1f5f9;
        font-size: 26px;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-value .green { color: #00ff88; }
    .metric-value .red { color: #ff3b5c; }
    .metric-value .gold { color: #fbbf24; }
    
    /* Signal badges */
    .badge-strong-buy {
        background: rgba(0,255,136,0.15);
        color: #00ff88;
        border: 1px solid rgba(0,255,136,0.3);
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-buy {
        background: rgba(0,200,255,0.12);
        color: #00c8ff;
        border: 1px solid rgba(0,200,255,0.25);
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-wait {
        background: rgba(255,170,0,0.12);
        color: #fbbf24;
        border: 1px solid rgba(255,170,0,0.25);
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-avoid {
        background: rgba(255,59,92,0.12);
        color: #ff3b5c;
        border: 1px solid rgba(255,59,92,0.25);
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Rarity */
    .rarity-legendary {
        background: linear-gradient(135deg, #fbbf24, #f59e0b);
        color: #000;
        font-weight: 800;
        padding: 2px 14px;
        border-radius: 20px;
        font-size: 12px;
        text-shadow: 0 0 20px rgba(251,191,36,0.3);
    }
    .rarity-epic {
        background: linear-gradient(135deg, #8b5cf6, #7c3aed);
        color: #fff;
        font-weight: 700;
        padding: 2px 14px;
        border-radius: 20px;
        font-size: 12px;
    }
    .rarity-rare {
        background: rgba(59,130,246,0.2);
        color: #60a5fa;
        border: 1px solid rgba(59,130,246,0.3);
        padding: 2px 14px;
        border-radius: 20px;
        font-size: 12px;
    }
    .rarity-common {
        background: rgba(255,255,255,0.05);
        color: #94a3b8;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 2px 14px;
        border-radius: 20px;
        font-size: 12px;
    }
    
    /* AI Badge */
    .ai-badge {
        background: rgba(139,92,246,0.15);
        border: 1px solid rgba(139,92,246,0.3);
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 11px;
        font-weight: 600;
        color: #a78bfa;
        display: inline-block;
    }
    
    /* Progress bar */
    .progress-track {
        background: #1a1f2e;
        border-radius: 8px;
        height: 6px;
        overflow: hidden;
        margin-top: 6px;
    }
    .progress-fill {
        height: 100%;
        border-radius: 8px;
        background: linear-gradient(90deg, #00ff88, #fbbf24);
        transition: width 1s ease;
    }
    
    /* Table styling */
    .dataframe {
        background: transparent !important;
    }
    .dataframe th {
        color: #94a3b8 !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 10px 12px !important;
        border-bottom: 1px solid #1e293b !important;
    }
    .dataframe td {
        color: #e2e8f0 !important;
        font-size: 13px !important;
        padding: 8px 12px !important;
        border-bottom: 1px solid rgba(30,41,59,0.3) !important;
    }
    .dataframe tr:hover td {
        background: rgba(30,41,59,0.2) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(145deg, #00ff88, #00cc66);
        color: #000;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 10px 28px;
        transition: all 0.2s ease;
        font-size: 14px;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 40px rgba(0,255,136,0.2);
    }
    
    /* Sidebar */
    .css-1d391kg, .css-1adrfps {
        background: #0b0e1a !important;
    }
    
    /* Divider */
    hr {
        border-color: #1e293b !important;
        margin: 24px 0 !important;
    }
    
    /* Typography */
    h1, h2, h3 {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
    }
    .subtitle {
        color: #64748b;
        font-size: 14px;
        margin-top: -8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.03);
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        color: #94a3b8;
        font-weight: 500;
        font-size: 13px;
        border: 1px solid transparent;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0,255,136,0.06);
        color: #00ff88;
        border-color: #1e293b;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
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
col_logo, col_meta = st.columns([1, 3])
with col_logo:
    st.markdown("""
    <div style="font-size: 38px; font-weight: 900; background: linear-gradient(135deg, #00ff88, #fbbf24); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
        🎯
    </div>
    """, unsafe_allow_html=True)
with col_meta:
    st.markdown("""
    <div style="font-size: 28px; font-weight: 700; color: #f1f5f9;">
        Crypto Hunter <span style="color: #00ff88;">AI</span> <span style="font-size: 14px; font-weight: 400; color: #64748b; -webkit-text-fill-color: #64748b;">Pro</span>
    </div>
    <div style="font-size: 14px; color: #64748b; margin-top: -4px;">
        AI-Powered Crypto Scanner · Random Forest · Real-time Signals
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TOP METRICS
# =========================================================
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🎯 Level</div>
        <div class="metric-value">Lv.{st.session_state.level}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">⭐ XP</div>
        <div class="metric-value">{st.session_state.xp} <span style="font-size: 14px; color: #64748b;">/ 100</span></div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🏆 Score</div>
        <div class="metric-value"><span class="gold">{st.session_state.player_score}</span></div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🔥 Combo</div>
        <div class="metric-value"><span class="green">{st.session_state.combo}x</span> <span style="font-size: 14px; color: #64748b;">best {st.session_state.max_combo}x</span></div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🧠 AI Status</div>
        <div class="metric-value" style="font-size: 18px;">
            {"✅ Trained" if st.session_state.ai_trained else "⚡ Training..."}
            <span style="font-size: 13px; color: #64748b; font-weight: 400;">
                {f"({st.session_state.ai_accuracy:.1f}%)" if st.session_state.ai_trained else ""}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🪙 Hunted</div>
        <div class="metric-value">{len(st.session_state.found_coins)} <span style="font-size: 14px; color: #64748b;">coins</span></div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    st.markdown("#### 🎯 Filters")
    min_market_cap = st.selectbox("Min Market Cap", ["$10M", "$50M", "$100M", "$500M", "$1B"], index=2)
    min_price = st.selectbox("Min Price", ["$0.001", "$0.01", "$0.1", "$1"], index=1)
    scan_limit = st.slider("🔍 Scan Depth", 50, 300, 150, step=25)
    
    st.divider()
    
    st.markdown("#### 🧠 AI Settings")
    ai_confidence_threshold = st.slider("AI Confidence Threshold", 50, 90, 65, step=5)
    train_on_historical = st.checkbox("🔄 Train AI on historical data", value=True)
    
    if st.button("🧠 Retrain AI", use_container_width=True):
        st.session_state.ai_trained = False
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    st.markdown("#### 📱 Telegram Alert")
    default_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
    default_chat = st.secrets.get("TELEGRAM_CHAT_ID", "")
    BOT_TOKEN = st.text_input("Bot Token", type="password", value=default_token)
    CHAT_ID = st.text_input("Chat ID", value=default_chat)
    send_notifications = st.checkbox("🔔 Kirim Notifikasi", value=True)
    
    st.divider()
    
    st.markdown("#### 📊 Status")
    st.metric("Total Hunted", len(st.session_state.found_coins))
    st.metric("Best Combo", f"{st.session_state.max_combo}x")
    st.metric("Achievements", len(st.session_state.achievements))
    
    st.caption(f"🕐 Last scan: {st.session_state.last_scan_time.strftime('%H:%M:%S')}")
    
    if st.button("🔄 New Hunt", use_container_width=True):
        st.session_state.found_coins = []
        st.session_state.combo = 0
        st.cache_data.clear()
        st.rerun()

# =========================================================
# AI CLASS
# =========================================================
class AIPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.accuracy = 0
        self.features = []
    
    def _extract_features(self, df):
        features = pd.DataFrame()
        features['close'] = df['Close']
        features['high'] = df['High']
        features['low'] = df['Low']
        features['volume'] = df['Volume']
        features['return_1'] = df['Close'].pct_change()
        features['return_5'] = df['Close'].pct_change(5)
        features['return_10'] = df['Close'].pct_change(10)
        features['volatility'] = df['Close'].rolling(10).std()
        features['volume_ma'] = df['Volume'].rolling(5).mean()
        features['volume_ratio'] = df['Volume'] / (features['volume_ma'] + 0.001)
        features = features.replace([np.inf, -np.inf], np.nan)
        features = features.dropna()
        self.features = features.columns.tolist()
        return features
    
    def train(self, df):
        if len(df) < 50:
            return False
        try:
            features = self._extract_features(df)
            if features.empty:
                return False
            future_return = df['Close'].shift(-3) / df['Close'] - 1
            target = pd.Series(index=df.index, dtype=int)
            target[future_return > 0.02] = 1
            target[future_return < -0.02] = 2
            target[future_return.abs() <= 0.02] = 0
            valid_idx = features.index.intersection(target.dropna().index)
            X = features.loc[valid_idx]
            y = target.loc[valid_idx]
            y = y.dropna()
            X = X.loc[y.index]
            if len(X) < 30:
                return False
            X_scaled = self.scaler.fit_transform(X)
            if np.isnan(X_scaled).any():
                return False
            self.model = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42, n_jobs=-1)
            split_idx = int(len(X_scaled) * 0.8)
            if split_idx < 2 or split_idx >= len(X_scaled):
                self.model.fit(X_scaled, y)
                self.is_trained = True
                self.accuracy = 0.5
                return True
            X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            if len(X_train) < 5 or len(X_test) < 3:
                self.model.fit(X_scaled, y)
                self.is_trained = True
                self.accuracy = 0.5
                return True
            self.model.fit(X_train, y_train)
            self.accuracy = (self.model.predict(X_test) == y_test).mean()
            self.is_trained = True
            return True
        except:
            return False
    
    def predict(self, df):
        default = {'signal': 0, 'signal_text': '🟡 HOLD', 'confidence': 0, 'buy_prob': 0, 'sell_prob': 0, 'hold_prob': 0}
        if not self.is_trained or len(df) < 10:
            return default
        try:
            features = self._extract_features(df)
            if features.empty:
                return default
            X = features.iloc[-1:]
            if X.empty or X.isnull().all().all():
                return default
            X_scaled = self.scaler.transform(X)
            if np.isnan(X_scaled).any():
                return default
            pred = self.model.predict(X_scaled)[0]
            proba = self.model.predict_proba(X_scaled)[0]
            if len(proba) < 3:
                proba = list(proba) + [0] * (3 - len(proba))
            proba_sum = sum(proba)
            if proba_sum > 0:
                proba = [p / proba_sum for p in proba]
            signal_text_map = {0: '🟡 HOLD', 1: '🟢 BUY', 2: '🔴 SELL'}
            return {
                'signal': int(pred),
                'signal_text': signal_text_map.get(pred, '🟡 HOLD'),
                'confidence': float(max(proba) * 100),
                'buy_prob': float(proba[1] * 100) if len(proba) > 1 else 0,
                'sell_prob': float(proba[2] * 100) if len(proba) > 2 else 0,
                'hold_prob': float(proba[0] * 100) if len(proba) > 0 else 0
            }
        except:
            return default

# =========================================================
# DATA FETCH FUNCTIONS
# =========================================================
@st.cache_data(ttl=300)
def get_coins_from_coingecko(limit=200):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": limit, "page": 1, "sparkline": False, "price_change_percentage": "24h,7d"}
    try:
        resp = requests.get(url, params=params, timeout=30)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=300)
def get_yfinance_data_full(symbol, name):
    try:
        ticker = yf.Ticker(f"{symbol}-USD")
        info = ticker.info
        hist = ticker.history(period="30d", interval="1d")
        if hist.empty or len(hist) < 10:
            return None
        latest = hist.iloc[-1]
        price = latest["Close"]
        volume_24h = latest["Volume"]
        change_24h = ((price - hist.iloc[-2]["Close"]) / hist.iloc[-2]["Close"]) * 100 if len(hist) >= 2 else 0
        change_7d = ((price - hist.iloc[0]["Close"]) / hist.iloc[0]["Close"]) * 100 if len(hist) >= 7 else 0
        volumes = hist["Volume"].tolist()
        avg_volume_7d = sum(volumes[-7:]) / min(len(volumes), 7) if len(volumes) >= 7 else volume_24h
        ratio = volume_24h / avg_volume_7d if avg_volume_7d > 0 else 1
        volume_trend = "🔼 SURGE" if ratio > 1.5 else "🔼 UP" if ratio > 1.3 else "🔽 DOWN" if ratio < 0.7 else "➡️ STABLE"
        market_cap = info.get("marketCap", 0)
        return {"Coin": name, "Symbol": symbol, "Price": price, "24H %": change_24h, "7D %": change_7d,
                "Volume (M)": volume_24h / 1_000_000, "Volume Trend": volume_trend, "Volume Ratio": ratio,
                "Market Cap": market_cap, "Historical": hist}
    except:
        return None

def calculate_score(row):
    score = 0
    if row["24H %"] > 10: score += 50
    elif row["24H %"] > 5: score += 35
    elif row["24H %"] > 2: score += 20
    elif row["24H %"] > 0: score += 10
    if row["7D %"] > 20: score += 20
    elif row["7D %"] > 10 and row["24H %"] > row["7D %"] * 0.3: score += 15
    elif row["7D %"] > 5: score += 10
    ratio = row.get("Volume Ratio", 1)
    if ratio > 2.0: score += 20
    elif ratio > 1.5: score += 15
    elif ratio > 1.3: score += 10
    mcap = row.get("Market Cap", 0)
    if mcap > 100_000_000_000: score += 15
    elif mcap > 10_000_000_000: score += 10
    elif mcap > 1_000_000_000: score += 5
    return score

def get_signal_badge(score):
    if score >= 80: return ("🔥 STRONG BUY", "badge-strong-buy")
    elif score >= 65: return ("🟢 BUY", "badge-buy")
    elif score >= 45: return ("🟡 WAIT", "badge-wait")
    else: return ("🔴 AVOID", "badge-avoid")

def get_rarity(score, volume_ratio, ai_signal, ai_conf):
    if score >= 85 and volume_ratio > 1.5:
        return ("⚡ LEGENDARY", "rarity-legendary")
    if ai_signal == "🟢 BUY" and ai_conf > 70 and score >= 70:
        return ("💎 EPIC", "rarity-epic")
    if score >= 75:
        return ("💎 EPIC", "rarity-epic")
    if score >= 60:
        return ("🌟 RARE", "rarity-rare")
    return ("🟢 COMMON", "rarity-common")

# =========================================================
# MAIN SCAN
# =========================================================
filter_map = {"$10M": 10_000_000, "$50M": 50_000_000, "$100M": 100_000_000,
              "$500M": 500_000_000, "$1B": 1_000_000_000}
min_mcap_value = filter_map.get(min_market_cap, 100_000_000)
price_map = {"$0.001": 0.001, "$0.01": 0.01, "$0.1": 0.1, "$1": 1.0}
min_price_value = price_map.get(min_price, 0.01)

with st.spinner("🧠 Analyzing markets with AI..."):
    coins_data = get_coins_from_coingecko(limit=scan_limit)
    if not coins_data:
        st.error("❌ Failed to fetch data from CoinGecko. Please try again later.")
        st.stop()

    filtered_coins = [c for c in coins_data if c.get("market_cap", 0) >= min_mcap_value and c.get("current_price", 0) >= min_price_value]
    if not filtered_coins:
        st.warning("⚠️ No coins passed the filters. Try lower thresholds.")
        st.stop()

    results, all_historical = [], {}
    progress_bar = st.progress(0)
    status_text = st.empty()

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(get_yfinance_data_full, c["symbol"].upper(), c["name"]): c for c in filtered_coins}
        for idx, future in enumerate(as_completed(futures)):
            progress_bar.progress((idx + 1) / len(filtered_coins))
            status_text.text(f"Scanning {idx + 1}/{len(filtered_coins)} ...")
            try:
                data = future.result()
                if data:
                    results.append(data)
                    if data.get("Historical") is not None:
                        all_historical[data["Symbol"]] = data["Historical"]
            except:
                pass
            time.sleep(0.04)

    progress_bar.empty()
    status_text.empty()

if not results:
    st.warning("No valid data found. Try adjusting filters.")
    st.stop()

# =========================================================
# TRAIN AI
# =========================================================
ai_predictor = AIPredictor()
if train_on_historical and all_historical:
    status_text.text("🧠 Training AI model...")
    trained_count = 0
    total_accuracy = 0
    for symbol, hist_df in all_historical.items():
        if len(hist_df) >= 30:
            try:
                if ai_predictor.train(hist_df):
                    trained_count += 1
                    total_accuracy += ai_predictor.accuracy
            except:
                pass
    if trained_count > 0:
        st.session_state.ai_trained = True
        st.session_state.ai_accuracy = (total_accuracy / trained_count) * 100
    else:
        try:
            combined = pd.concat([h for h in all_historical.values() if h is not None])
            combined = combined.replace([np.inf, -np.inf], np.nan).dropna()
            if len(combined) > 50 and ai_predictor.train(combined):
                st.session_state.ai_trained = True
                st.session_state.ai_accuracy = ai_predictor.accuracy * 100
        except:
            pass
    status_text.empty()

# =========================================================
# PROCESS RESULTS
# =========================================================
processed = []
for data in results:
    score = calculate_score(data)
    ai_pred = None
    if st.session_state.ai_trained and data.get("Historical") is not None:
        hist = data["Historical"]
        if len(hist) >= 10:
            ai_pred = ai_predictor.predict(hist)
    
    signal, badge = get_signal_badge(score)
    ai_signal = ai_pred['signal_text'] if ai_pred and st.session_state.ai_trained else "⚡ No AI"
    ai_conf = ai_pred['confidence'] if ai_pred and st.session_state.ai_trained else 0
    
    # Combine AI with signal
    if ai_pred and st.session_state.ai_trained and ai_conf >= ai_confidence_threshold:
        if ai_signal == "🟢 BUY" and score > 50:
            signal = "🔥 STRONG BUY (AI)"
            badge = "badge-strong-buy"
        elif ai_signal == "🔴 SELL" and score < 60:
            signal = "🔴 SELL (AI)"
            badge = "badge-avoid"
        elif ai_signal == "🟢 BUY":
            signal = "🟢 BUY (AI)"
            badge = "badge-buy"
    
    rarity, rarity_class = get_rarity(score, data["Volume Ratio"], ai_signal, ai_conf)
    
    processed.append({
        "Coin": data["Coin"], "Symbol": data["Symbol"], "Price": data["Price"],
        "24H %": round(data["24H %"], 2), "7D %": round(data["7D %"], 2),
        "Volume (M)": round(data["Volume (M)"], 1), "Score": score,
        "Signal": signal, "Badge": badge,
        "AI Signal": ai_signal, "AI Confidence": f"{ai_conf:.0f}%" if ai_conf > 0 else "N/A",
        "Rarity": rarity, "Rarity Class": rarity_class,
        "Volume Trend": data["Volume Trend"],
        "AI Buy %": f"{ai_pred['buy_prob']:.0f}%" if ai_pred else "N/A",
        "AI Sell %": f"{ai_pred['sell_prob']:.0f}%" if ai_pred else "N/A",
        "AI Hold %": f"{ai_pred['hold_prob']:.0f}%" if ai_pred else "N/A"
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
    st.success(f"🎉 Level Up! You are now Level {st.session_state.level}!")

st.session_state.last_scan_time = datetime.now()

# =========================================================
# DISPLAY - TOP CARD
# =========================================================
st.divider()

col_refresh, col_scaninfo = st.columns([1, 3])
with col_refresh:
    if st.button("⚔️ Scan Again", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with col_scaninfo:
    st.caption(f"🕐 Last scan: {st.session_state.last_scan_time.strftime('%Y-%m-%d %H:%M:%S')} · {len(df)} coins scanned")

if not df.empty:
    top = df.iloc[0]
    rarity_emoji = "👑" if "LEGENDARY" in top["Rarity"] else "💎" if "EPIC" in top["Rarity"] else "🌟"
    
    st.markdown(f"""
    <div style="background: linear-gradient(145deg, #141824, #0d1120); border: 1px solid #1e293b; border-radius: 20px; padding: 24px 30px; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <span style="font-size: 28px; font-weight: 700; color: #f1f5f9;">{rarity_emoji} {top['Coin']}</span>
                <span style="font-size: 16px; color: #64748b; margin-left: 12px;">{top['Symbol']}</span>
                <span style="font-size: 13px; margin-left: 12px;" class="{top['Badge']}">{top['Signal']}</span>
                <span style="font-size: 13px; margin-left: 8px;" class="ai-badge">🤖 {top['AI Signal']}</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 28px; font-weight: 700; color: #fbbf24;">{top['Score']}</span>
                <span style="font-size: 14px; color: #64748b;">/100</span>
                <div><span class="{top['Rarity Class']}">{top['Rarity']}</span></div>
            </div>
        </div>
        <div style="display: flex; gap: 24px; margin-top: 14px; color: #94a3b8; font-size: 14px; flex-wrap: wrap;">
            <span>💰 ${top['Price']:.4f}</span>
            <span>📈 24h: <span style="color: {'#00ff88' if top['24H %'] > 0 else '#ff3b5c'}">{top['24H %']}%</span></span>
            <span>📊 7d: <span style="color: {'#00ff88' if top['7D %'] > 0 else '#ff3b5c'}">{top['7D %']}%</span></span>
            <span>{top['Volume Trend']}</span>
            <span>🧠 Conf: {top['AI Confidence']}</span>
            <span>🏅 Rank #{top['Rank']}</span>
        </div>
        <div style="display: flex; gap: 16px; margin-top: 8px; font-size: 12px; color: #475569;">
            <span>📊 AI Probabilities: Buy {top['AI Buy %']} · Sell {top['AI Sell %']} · Hold {top['AI Hold %']}</span>
        </div>
        <div class="progress-track" style="margin-top: 10px;">
            <div class="progress-fill" style="width: {min(top['Score'], 100)}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 All Coins", "🔥 Strong Buy", "🧠 AI Picks", "💎 Rarity", "📥 Export"
])

with tab1:
    st.dataframe(df, use_container_width=True, hide_index=True, height=450)

with tab2:
    strong = df[df["Signal"].str.contains("STRONG BUY")]
    if not strong.empty:
        st.dataframe(strong, use_container_width=True, hide_index=True)
        st.success(f"🔥 Found {len(strong)} strong buy signals")
    else:
        st.info("No strong buy signals at the moment.")

with tab3:
    ai_picks = df[(df["AI Signal"].isin(["🟢 BUY", "🔴 SELL"])) & (df["AI Confidence"] != "N/A")]
    if not ai_picks.empty:
        st.dataframe(ai_picks, use_container_width=True, hide_index=True)
        st.caption(f"🧠 {len(ai_picks)} AI recommendations · Threshold: {ai_confidence_threshold}%")
    else:
        st.info("No AI recommendations. Try lowering the confidence threshold.")

with tab4:
    for rarity, label in [("LEGENDARY", "👑 Legendary"), ("EPIC", "💎 Epic"), ("RARE", "🌟 Rare")]:
        subset = df[df["Rarity"].str.contains(rarity)]
        if not subset.empty:
            st.markdown(f"#### {label} ({len(subset)})")
            st.dataframe(subset, use_container_width=True, hide_index=True)

with tab5:
    st.download_button("📥 Download CSV", df.to_csv(index=False).encode('utf-8'),
                       f"crypto_hunt_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv")

# =========================================================
# ACHIEVEMENTS
# =========================================================
st.divider()
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
        st.info("No achievements yet. Keep hunting!")

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption(f"""
⚔️ {len(st.session_state.found_coins)} coins hunted · Level {st.session_state.level} · Combo {st.session_state.combo}x · Best {st.session_state.max_combo}x
🧠 AI {'✅' if st.session_state.ai_trained else '❌'} · Accuracy {st.session_state.ai_accuracy:.1f}% · Filter: MCap > {min_market_cap}, Price > {min_price}
🔄 Data from CoinGecko + Yahoo Finance · Auto-refresh every 5 min
""")

st_autorefresh(interval=300000, key="refresh")
