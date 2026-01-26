import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# Sector ETF Mapping
SECTORS = {
    'XLK': 'Technology', 'XLV': 'Health Care', 'XLF': 'Financials',
    'XLY': 'Cons. Discretionary', 'XLC': 'Communication', 'XLI': 'Industrials',
    'XLP': 'Cons. Staples', 'XLE': 'Energy', 'XLB': 'Materials',
    'XLRE': 'Real Estate', 'XLU': 'Utilities'
}

# Expanded Watchlist - 10 Stocks per Sector
WATCHLIST = {
    'Technology': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'ADBE', 'CSCO', 'CRM', 'AMD', 'QCOM'],
    'Financials': ['JPM', 'V', 'MA', 'BAC', 'GS', 'MS', 'WFC', 'BLK', 'AXP', 'C'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'WMB', 'HES'],
    'Health Care': ['UNH', 'LLY', 'JNJ', 'ABBV', 'MRK', 'PFE', 'AMGN', 'ISRG', 'TMO', 'GILD'],
    'Cons. Discretionary': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'BKNG', 'TJX', 'NCLH'],
    'Communication': ['GOOGL', 'META', 'NFLX', 'DIS', 'TMUS', 'VZ', 'T', 'CMCSA', 'CHTR', 'SNAP'],
    'Industrials': ['CAT', 'HON', 'GE', 'UNP', 'UPS', 'BA', 'LMT', 'RTX', 'DE', 'MMM'],
    'Cons. Staples': ['PG', 'KO', 'PEP', 'COST', 'WMT', 'PM', 'EL', 'MO', 'MDLZ', 'CL'],
    'Materials': ['LIN', 'APD', 'FCX', 'SHW', 'NEM', 'CTVA', 'ECL', 'VMC', 'DOW', 'NUE'],
    'Real Estate': ['PLD', 'AMT', 'EQIX', 'CCI', 'PSA', 'DLR', 'O', 'VICI', 'SBAC', 'WELL'],
    'Utilities': ['NEE', 'SO', 'DUK', 'AEP', 'SRE', 'D', 'EXC', 'PCG', 'XEL', 'ED']
}

def get_market_data():
    all_tickers = list(SECTORS.keys()) + ['^GSPC']
    raw_data = yf.download(all_tickers, period='5d', interval='1d', auto_adjust=True)
    
    # Access the 'Close' data (MultiIndex safe)
    data = raw_data['Close']
    
    # Calculate % change from previous close
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    
    sp_change = returns['^GSPC']
    direction = "Bulls Leading 🚀" if sp_change > 0 else "Bears in Control 🔻"
    
    sector_returns = returns[list(SECTORS.keys())].rename(index=SECTORS)
    ranked = sector_returns.sort_values(ascending=False)
    return sp_change, direction, ranked

def build_report():
    try:
        sp_change, direction, ranked = get_market_data()
    except Exception as e:
        print(f"Data error: {e}")
        return None, None

    top_3 = ranked.head(3)
    bottom_3 = ranked.tail(3)

    html = f"""
    <div style="background:#001529; color:white; padding:45px; border-radius:20px; text-align:center; font-family:sans-serif; margin-bottom:30px;">
        <h1 style="color:#1890ff; margin:0; font-size:26px;">Wall Street Wrap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="font-size:64px; font-weight:800; margin:15px 0;">S&P 500: {sp_change:.2f}%</div>
        <div style="font-size:22px; color:{'#52c41a' if sp_change > 0 else '#f5222d'};">{direction}</div>
    </div>

    <h2 style="margin-top:40px; border-bottom:2px solid #333; padding-bottom:10px; color:#1a2b48;">🚀 Top Performing Sectors</h2>
    {" ".join([f'''
    <div style="background:#f6ffed; border:1px solid #b7eb8f; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:18px;">{s}</strong>
            <span style="color:#389e0d; font-size:20px; font-weight:bold;">+{v:.2f}%</span>
        </div>
        <p style="margin:10px 0 0 0; font-size:13px; color:#555;"><strong>Sector Heavyweights:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in top_3.items()])}

    <h2 style="margin-top:40px; border-bottom:2px solid #333; padding-bottom:10px; color:#1a2b48;">🔻 Laggard Sectors</h2>
    {" ".join([f'''
    <div style="background:#fff1f0; border:1px solid #ffa39e; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:18px;">{s}</strong>
            <span style="color:#cf1322; font-size:20px; font-weight:bold;">{v:.2f}%</span>
        </div>
        <p style="margin:10px 0 0 0; font-size:13px; color:#555;"><strong>Under Pressure:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in bottom_3.items()])}

    <p style="margin-top:30px; font-size:14px; color:#888; text-align:center;">
        <em>Data source: Yahoo Finance. Updates automated for US Market Close.</em>
    </p>
    """
    return html, sp_change

def post():
    content, change = build_report()
    if content is None: return
    
    auth_str = f"{WP_USER}:{WP_PASS}"
    token = base64.b64encode(auth_str.encode()).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'title': f"Wall Street Wrap: S&P 500 {'Gains' if change > 0 else 'Slips'} {change:.2f}% ({datetime.now().strftime('%d %b')})",
        'content': content,
        'status': 'publish',
        'categories': [CATEGORY_ID]
    }
    
    res = requests.post(WP_URL, headers=headers, json=payload)
    if res.status_code == 201:
        print("✅ US Market Post Created Successfully!")
    else:
        print(f"❌ Error: {res.status_code} - {res.text}")

if __name__ == "__main__":
    post()
