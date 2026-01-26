import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# SEO-Targeted Watchlist (10 per sector)
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
    etfs = ['XLK', 'XLV', 'XLF', 'XLY', 'XLC', 'XLI', 'XLP', 'XLE', 'XLB', 'XLRE', 'XLU']
    all_tickers = etfs + ['^GSPC']
    raw_data = yf.download(all_tickers, period='5d', interval='1d', auto_adjust=True)
    data = raw_data['Close']
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    
    sector_map = {'XLK': 'Technology', 'XLV': 'Health Care', 'XLF': 'Financials', 'XLY': 'Cons. Discretionary', 
                  'XLC': 'Communication', 'XLI': 'Industrials', 'XLP': 'Cons. Staples', 'XLE': 'Energy', 
                  'XLB': 'Materials', 'XLRE': 'Real Estate', 'XLU': 'Utilities'}
    
    sector_returns = returns[etfs].rename(index=sector_map)
    return returns['^GSPC'], sector_returns.sort_values(ascending=False)

def build_seo_report():
    try:
        sp_change, ranked = get_market_data()
    except Exception as e:
        print(f"Data Fetch Error: {e}")
        return None, None, None

    status = "Advances" if sp_change > 0 else "Declines"
    
    html = f"""
    <div style="background:#001529; color:white; padding:35px; border-radius:20px; text-align:center; font-family:sans-serif; margin-bottom:30px;">
        <p style="text-transform:uppercase; letter-spacing:2px; font-size:14px; margin:0; color:#1890ff;">Stock Market Today</p>
        <h1 style="color:white; margin:10px 0; font-size:28px;">US Market Recap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="margin:20px 0;">
            <span style="font-size:20px; color:#8c8c8c; display:block;">S&P 500 Performance</span>
            <span style="font-size:52px; font-weight:800; display:block;">{sp_change:.2f}%</span>
        </div>
        <p style="font-size:18px; color:{'#52c41a' if sp_change > 0 else '#f5222d'};">Market Sentiment: {'Bullish 🚀' if sp_change > 0 else 'Bearish 🔻'}</p>
    </div>

    <h2 style="color:#1a2b48; border-left:5px solid #1890ff; padding-left:15px;">Wall Street Intelligence Report</h2>
    <p style="line-height:1.6; color:#444;">The US stock market {status.lower()} in today's session as investors parsed global economic data and institutional flows. This recap highlights the key sectoral shifts and price action across major indices.</p>

    <h3 style="margin-top:30px; color:#389e0d;">🚀 Sector Outperformers</h3>
    {" ".join([f'''
    <div style="background:#f6ffed; border:1px solid #b7eb8f; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong>{s}</strong>
            <span style="color:#389e0d; font-weight:bold; font-size:18px;">+{v:.2f}%</span>
        </div>
        <p style="margin:8px 0 0 0; font-size:12px; color:#555;"><strong>Top Weights:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in ranked.head(3).items()])}

    <h3 style="margin-top:30px; color:#cf1322;">🔻 Sector Laggards</h3>
    {" ".join([f'''
    <div style="background:#fff1f0; border:1px solid #ffa39e; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong>{s}</strong>
            <span style="color:#cf1322; font-weight:bold; font-size:18px;">{v:.2f}%</span>
        </div>
        <p style="margin:8px 0 0 0; font-size:12px; color:#666;"><strong>Under Pressure:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in ranked.tail(3).items()])}

    <p style="margin-top:40px; border-top:1px solid #eee; padding-top:20px; font-size:14px; color:#888; text-align:center;">
        <em>Source: Yahoo Finance Data. Check our <strong>India Stock Market PE Ratio</strong> tool for long-term valuation trends.</em>
    </p>
    """
    return html, sp_change, ranked

def post():
    content, change, ranked = build_seo_report()
    if not content: return
    
    auth_str = f"{WP_USER}:{WP_PASS}"
    token = base64.b64encode(auth_str.encode()).decode('utf-8')
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    
    # Title optimized for keywords
    post_title = f"Stock Market Today: S&P 500 {'Gains' if change > 0 else 'Slips'} {change:.2f}% | US Market Wrap {datetime.now().strftime('%d %b')}"
    
    payload = {
        'title': post_title,
        'content': content,
        'status': 'publish',
        'categories': [CATEGORY_ID],
        'excerpt': f"Daily US Market Recap: S&P 500 moves {change:.2f}% as {ranked.index[0]} sector leads performance for the day."
    }
    
    res = requests.post(WP_URL, headers=headers, json=payload)
    print("✅ Success!" if res.status_code == 201 else f"❌ Error: {res.text}")

if __name__ == "__main__":
    post()
