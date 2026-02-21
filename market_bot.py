import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide")

# ==============================
# 🎨 PREMIUM PROFESSIONAL STYLING
# ==============================
st.markdown("""
<style>

body {
    background-color: #f4f6f9;
}

/* ====== NIFTY TOP CARD ====== */
.nifty-card {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    padding: 50px;
    border-radius: 22px;
    text-align: center;
    color: white;
    box-shadow: 0px 20px 45px rgba(0,0,0,0.25);
    margin-bottom: 40px;
}

.nifty-title {
    font-size: 15px;
    letter-spacing: 4px;
    color: #94a3b8;
}

.nifty-value {
    font-size: 72px;
    font-weight: 800;
    margin: 12px 0;
}

.nifty-change-positive {
    font-size: 22px;
    font-weight: 600;
    color: #22c55e;
}

.nifty-change-negative {
    font-size: 22px;
    font-weight: 600;
    color: #ef4444;
}

/* ====== VALUATION CARD ====== */
.valuation-card {
    background: white;
    padding: 35px;
    border-radius: 20px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.08);
    margin-bottom: 40px;
}

.valuation-title {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 20px;
    color: #111827;
}

.metric-label {
    font-size: 15px;
    color: #6b7280;
}

.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
}

/* ====== SECTOR CARD ====== */
.sector-card {
    background: white;
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.08);
    margin-bottom: 40px;
}

.sector-header {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 20px;
}

/* ====== STOCK CARD ====== */
.stock-card {
    background: #ffffff;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    margin-bottom: 15px;
    transition: 0.3s;
}

.stock-card:hover {
    box-shadow: 0px 6px 18px rgba(0,0,0,0.1);
}

.stock-name {
    font-weight: 800;
    font-size: 18px;
    color: #000000;
}

.stock-price {
    font-size: 16px;
    font-weight: 600;
}

.stock-positive {
    color: #16a34a;
    font-weight: 600;
}

.stock-negative {
    color: #dc2626;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# 📈 NIFTY DATA
# ==============================
nifty = yf.Ticker("^NSEI")
data = nifty.history(period="1d")

if not data.empty:
    price = data["Close"].iloc[-1]
    prev = data["Open"].iloc[-1]
    change = price - prev
    percent = (change / prev) * 100

    change_class = "nifty-change-positive" if percent >= 0 else "nifty-change-negative"

    st.markdown(f"""
    <div class="nifty-card">
        <div class="nifty-title">DAILY NIFTY 50 INSIGHTS</div>
        <div class="nifty-value">{price:,.2f}</div>
        <div class="{change_class}">
            {'▲' if percent>=0 else '▼'} {percent:.2f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# 📊 VALUATION SECTION
# ==============================

current_pe = 23.86
forecast_1y = 7.33

st.markdown(f"""
<div class="valuation-card">
    <div class="valuation-title">📊 Valuation Analysis & Forecast</div>
    <div style="display:flex; gap:100px;">
        <div>
            <div class="metric-label">Current P/E</div>
            <div class="metric-value">{current_pe}</div>
        </div>
        <div>
            <div class="metric-label">1Y Median Forecast</div>
            <div class="metric-value" style="color:#16a34a;">{forecast_1y}%</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================
# 📊 FULL SECTOR MAP (UNCHANGED)
# ==============================

SECTOR_MAP = {
    'Nifty Bank': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK', 'INDUSINDBK', 'BANKBARODA', 'PNB', 'IDFCFIRSTB', 'FEDERALBNK'],
    'IT Services': ['TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM', 'LTIM', 'PERSISTENT', 'COFORGE', 'MPHASIS', 'KPITTECH'],
    'Automobile': ['M&M', 'MARUTI', 'TATAMOTORS', 'BAJAJ-AUTO', 'EICHERMOT', 'TVSMOTOR', 'HEROMOTOCO', 'ASHOKLEY', 'MRF', 'BALKRISIND'],
    'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'GODREJCP', 'DABUR', 'MARICO', 'VBL', 'COLPAL', 'TATACONSUM'],
    'Metals': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'JINDALSTEL', 'VEDL', 'NMDC', 'SAIL', 'NATIONALUM', 'APLAPOLLO', 'RATNAMANI'],
    'Pharma': ['SUNPHARMA', 'CIPLA', 'DRREDDY', 'LUPIN', 'AUROPHARMA', 'ZYDUSLIFE', 'DIVISLAB', 'ALKEM', 'TORNTPHARM', 'ABBOTT'],
    'Energy': ['RELIANCE', 'NTPC', 'ONGC', 'POWERGRID', 'BPCL', 'ADANIGREEN', 'TATAPOWER', 'IOC', 'GAIL', 'ADANIENSOL'],
    'Financial Services': ['BAJFINANCE', 'HDFCBANK', 'ICICIBANK', 'BAJAJFINSV', 'CHOLAFIN', 'REC', 'PFC', 'SHRIRAMFIN', 'SBILIFE', 'HDFCLIFE'],
    'PSU Bank': ['SBIN', 'BANKBARODA', 'CANBK', 'UNIONBANK', 'IOB', 'PNB', 'INDIANB', 'BANKINDIA', 'UCOBANK', 'CENTRALBK'],
    'Realty': ['DLF', 'LODHA', 'GODREJPROP', 'OBEROIRLTY', 'PRESTIGE', 'PHOENIXLTD', 'BRIGADE', 'SOBHA', 'SIGNATURE', 'SUNTECK'],
    'Media': ['ZEEL', 'SUNTV', 'PVRINOX', 'NETWORK18', 'TV18BRDCST', 'NAZARA', 'DISHTV', 'HATHWAY', 'SAREGMAPA', 'TIPSINDLTD'],
    'Consumption': ['ITC', 'HINDUNILVR', 'TITAN', 'ASIANPAINT', 'NESTLEIND', 'TRENT', 'DMART', 'ZOMATO', 'BRITANNIA', 'PAGEIND'],
    'Infrastructure': ['RELIANCE', 'LT', 'BHARTIARTL', 'NTPC', 'ADANIPORTS', 'ULTRACEMCO', 'ONGC', 'GRASIM', 'IIFL', 'POWERGRID'],
    'PSE': ['NTPC', 'ONGC', 'POWERGRID', 'COALINDIA', 'BEL', 'HAL', 'BPCL', 'IOC', 'PFC', 'REC'],
    'CPSE': ['NTPC', 'ONGC', 'POWERGRID', 'COALINDIA', 'BEL', 'NHPC', 'SJVN', 'NBCC', 'OIL', 'COCHINSHIP'],
    'Commodities': ['RELIANCE', 'TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'NTPC', 'ONGC', 'AMBUJACEM', 'GRASIM', 'VEDL', 'COALINDIA'],
    'Services': ['LT', 'ADANIPORTS', 'APOLLOHOSP', 'HDFCLIFE', 'SBILIFE', 'TRENT', 'INDIGO', 'VBL', 'TATACOMM', 'GMRINFRA']
}

# ==============================
# 📊 SECTOR DISPLAY
# ==============================

for sector, stocks in SECTOR_MAP.items():
    st.markdown(f'<div class="sector-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="sector-header">{sector}</div>', unsafe_allow_html=True)

    cols = st.columns(3)

    for i, stock in enumerate(stocks):
        try:
            ticker = yf.Ticker(stock + ".NS")
            hist = ticker.history(period="1d")

            if hist.empty:
                continue

            price = hist["Close"].iloc[-1]
            prev = hist["Open"].iloc[-1]
            change = price - prev
            percent = (change / prev) * 100

            change_class = "stock-positive" if percent >= 0 else "stock-negative"

            with cols[i % 3]:
                st.markdown(f"""
                <div class="stock-card">
                    <div class="stock-name">{stock}</div>
                    <div class="stock-price">₹{price:,.2f}</div>
                    <div class="{change_class}">
                        {'▲' if percent>=0 else '▼'} {percent:.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

        except:
            pass

    st.markdown("</div>", unsafe_allow_html=True)
