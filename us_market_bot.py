import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12  # Change to your US Market Category ID

# Sector ETF Mapping
SECTORS = {
    'XLK': 'Technology', 'XLV': 'Health Care', 'XLF': 'Financials',
    'XLY': 'Cons. Discretionary', 'XLC': 'Communication', 'XLI': 'Industrials',
    'XLP': 'Cons. Staples', 'XLE': 'Energy', 'XLB': 'Materials',
    'XLRE': 'Real Estate', 'XLU': 'Utilities'
}

# Sector heavyweights to track as "Constituents"
WATCHLIST = {
    'Technology': ['AAPL', 'MSFT', 'NVDA'],
    'Financials': ['JPM', 'BAC', 'V'],
    'Energy': ['XOM', 'CVX', 'COP'],
    'Health Care': ['UNH', 'LLY', 'JNJ'],
    'Cons. Discretionary': ['AMZN', 'TSLA', 'HD'],
    'Communication': ['GOOGL', 'META', 'NFLX'],
    'Industrials': ['CAT', 'HON', 'GE'],
    'Cons. Staples': ['PG', 'KO', 'PEP'],
    'Materials': ['LIN', 'APD', 'FCX'],
    'Real Estate': ['PLD', 'AMT', 'EQIX'],
    'Utilities': ['NEE', 'SO', 'DUK']
}

def get_market_data():
    all_tickers = list(SECTORS.keys()) + ['^GSPC'] # ETFs + S&P 500
    data = yf.download(all_tickers, period='2d')['Adj Close']
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    
    # S&P 500 Performance
    sp_change = returns['^GSPC']
    direction = "Bulls Leading 🚀" if sp_change > 0 else "Bears in Control 🔻"
    
    # Rank Sectors
    sector_returns = returns[list(SECTORS.keys())].rename(index=SECTORS)
    ranked = sector_returns.sort_values(ascending=False)
    return sp_change, direction, ranked

def build_report():
    sp_change, direction, ranked = get_market_data()
    top_3 = ranked.head(3)
    bottom_3 = ranked.tail(3)

    html = f"""
    <div style="background:#001529; color:white; padding:45px; border-radius:20px; text-align:center; font-family:sans-serif;">
        <h1 style="color:#1890ff; margin:0;">Wall Street Daily: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="font-size:64px; font-weight:800; margin:15px 0;">S&P 500: {sp_change:.2f}%</div>
        <div style="font-size:22px; color:{'#52c41a' if sp_change > 0 else '#f5222d'};">{direction}</div>
    </div>

    <h2 style="margin-top:40px; border-bottom:2px solid #eee; padding-bottom:10px;">🚀 Top Performing Sectors</h2>
    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px;">
        {" ".join([f"<div style='background:#f6ffed; border:1px solid #b7eb8f; padding:15px; border-radius:10px;'><strong>{s}</strong><br><span style='color:#389e0d;'>+{v:.2f}%</span><br><small style='font-size:11px;'>Movers: {', '.join(WATCHLIST.get(s, []))}</small></div>" for s, v in top_3.items()])}
    </div>

    <h2 style="margin-top:40px; border-bottom:2px solid #eee; padding-bottom:10px;">🔻 Laggard Sectors</h2>
    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px;">
        {" ".join([f"<div style='background:#fff1f0; border:1px solid #ffa39e; padding:15px; border-radius:10px;'><strong>{s}</strong><br><span style='color:#cf1322;'>{v:.2f}%</span><br><small style='font-size:11px;'>Movers: {', '.join(WATCHLIST.get(s, []))}</small></div>" for s, v in bottom_3.items()])}
    </div>
    """
    return html, sp_change

def post():
    content, change = build_report()
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    payload = {
        'title': f"US Market Wrap: S&P 500 {'Climbs' if change > 0 else 'Drops'} {change:.2f}%",
        'content': content, 'status': 'publish', 'categories': [CATEGORY_ID]
    }
    res = requests.post(WP_URL, headers={'Authorization': f'Basic {auth}'}, json=payload)
    print("Post Created!" if res.status_code == 201 else f"Error: {res.text}")

if __name__ == "__main__":
    post()
