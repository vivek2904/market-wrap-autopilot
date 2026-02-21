import os, requests, base64, pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime
from bs4 import BeautifulSoup
import io

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# --- 1. FULL 170+ WATCHLIST ---
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

INDEX_TICKERS = {'^NSEI': 'NIFTY 50', '^NSEBANK': 'Nifty Bank', '^CNXIT': 'IT Services', '^CNXAUTO': 'Automobile', '^CNXFMCG': 'FMCG', '^CNXMETAL': 'Metals', '^CNXPHARMA': 'Pharma', '^CNXENERGY': 'Energy', '^CNXREALTY': 'Realty', '^CNXINFRA': 'Infrastructure', '^CNXFIN': 'Financial Services', '^CNXPSUBANK': 'PSU Bank', '^CNXMEDIA': 'Media', '^CNXCONSUMP': 'Consumption', '^CNXPSE': 'PSE', '^CNXCPSE': 'CPSE', '^CNXCOMMOD': 'Commodities', '^CNXSERVICE': 'Services'}

def get_links(ticker):
    clean = ticker.replace(".NS", "").upper()
    return f"https://www.google.com/finance/quote/{clean}:NSE", f"{WP_URL.split('wp-json')[0]}?s={clean}"

def get_valuation_and_summary():
    url = "https://worldperatio.com/area/india/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        summary_text = " ".join([p.get_text() for p in soup.find_all('p', limit=3) if len(p.get_text()) > 50])
        tables = pd.read_html(io.StringIO(response.text))
        pe, forecast, table_html = "N/A", "N/A", ""
        for df in tables:
            pe_col = [c for c in df.columns if "vs" in str(c)]
            if pe_col and pe == "N/A":
                pe = str(pe_col[0]).split("vs")[-1].strip().translate({ord(i): None for i in "()'"})
            if 'Period' in df.columns and any('Average P/E' in col for col in df.columns):
                table_html = df[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current P/E']].head(5).to_html(index=False, border=0, classes='valuation-table')
            if not df.empty and '1 Years' in str(df.iloc[:, 0].values):
                forecast = f"{df.iloc[0, 6]}%"
        return summary_text, pe, forecast, table_html
    except: return "Historical analysis for Nifty valuation.", "Analyzing...", "7.33%", ""

def fetch_analysis_data():
    all_tickers = list(set([f"{t}.NS" for sublist in SECTOR_MAP.values() for t in sublist]))
    data = yf.download(all_tickers, period="60d", interval="1d", auto_adjust=True)
    results = {}
    for t in all_tickers:
        try:
            subset = data.iloc[:, data.columns.get_level_values(1)==t]
            subset.columns = subset.columns.get_level_values(0)
            prices = subset['Close'].dropna()
            volumes = subset['Volume'].dropna()
            if len(prices) < 20: continue
            curr, prev = prices.iloc[-1], prices.iloc[-2]
            avg_vol_20 = volumes.iloc[-21:-1].mean()
            curr_vol = volumes.iloc[-1]
            vol_ratio = curr_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
            
            results[t.replace(".NS", "")] = {
                'price': curr, 'change': ((curr/prev)-1)*100, 
                'rsi': ta.rsi(prices, length=14).iloc[-1], 
                'vol_ratio': vol_ratio
            }
        except: continue
    return results

def build_report():
    idx_data = yf.download(list(INDEX_TICKERS.keys()), period='5d')['Close'].dropna(axis=1)
    idx_returns = ((idx_data.iloc[-1] / idx_data.iloc[-2] - 1) * 100).dropna()
    nifty_price, nifty_change = idx_data.iloc[-1].get('^NSEI', 0), idx_returns.get('^NSEI', 0)
    stock_analysis = fetch_analysis_data()
    summary, pe, target_return, v_table = get_valuation_and_summary()

    performance_map = {INDEX_TICKERS[k]: v for k, v in idx_returns.items() if k in INDEX_TICKERS}
    sorted_sectors = sorted(performance_map.items(), key=lambda item: item[1], reverse=True)

    html = f"""
    <style>
        .market-card {{ font-family: 'Inter', sans-serif; max-width: 950px; margin: auto; color: #1e293b; }}
        .header-box {{ background: #0f172a; color: white; padding: 50px 25px; border-radius: 24px; text-align: center; margin-bottom: 30px; }}
        .insight-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 30px; border-radius: 20px; margin-bottom: 30px; }}
        .sector-block {{ background: white; border: 1px solid #e2e8f0; border-radius: 20px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
        .stock-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-top: 20px; }}
        .stock-card {{ border: 1px solid #f1f5f9; padding: 12px; border-radius: 10px; font-size: 13px; background: #fff; }}
        .tag {{ font-size: 10px; padding: 2px 5px; border-radius: 4px; font-weight: bold; text-transform: uppercase; }}
        .vol-label {{ font-size: 11px; color: #64748b; font-weight: 600; margin-top: 4px; display: block; }}
        a {{ text-decoration: none; color: #3b82f6; font-weight: 700; }}
    </style>
    <div class="market-card">
        <div class="header-box">
            <span style="font-size:64px; font-weight:800; display:block;">{nifty_price:,.2f}</span>
            <div style="font-size:24px; color:{'#4ade80' if nifty_change > 0 else '#f87171'}; font-weight:700;">
                {'▲' if nifty_change > 0 else '▼'} {nifty_change:.2f}%
            </div>
        </div>
        <div class="insight-box">
            <h2 style="margin-top:0;">📊 Valuation Analytics</h2>
            <div style="display:flex; gap:40px; margin:25px 0;">
                <div><small>CURRENT P/E</small><br><b style="font-size:28px;">{pe}</b></div>
                <div><small>1Y MEDIAN FORECAST</small><br><b style="font-size:28px; color:#22c55e;">{target_return}</b></div>
            </div>
            {v_table}
        </div>
    """

    for sector_name, s_return in sorted_sectors:
        if sector_name not in SECTOR_MAP: continue
        html += f"""
        <div class="sector-block">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="margin:0;">{sector_name}</h3>
                <b style="color:{'#16a34a' if s_return > 0 else '#dc2626'};">{s_return:+.2f}%</b>
            </div>
            <div class="stock-grid">"""
        for t in SECTOR_MAP[sector_name]:
            s = stock_analysis.get(t, {'price': 0, 'change': 0, 'rsi': 50, 'vol_ratio': 1.0})
            ext, int_link = get_links(t)
            rsi_tag = '<span class="tag" style="background:#fee2e2; color:#ef4444;">Overbought</span>' if s['rsi'] > 70 else \
                      ('<span class="tag" style="background:#dcfce7; color:#22c55e;">Oversold</span>' if s['rsi'] < 30 else '')
            vol_color = "#d97706" if s['vol_ratio'] > 2.0 else "#64748b"
            
            html += f"""
                <div class="stock-card">
                    <div style="font-weight:700;"><a href="{int_link}">{t}</a></div>
                    <div style="font-size:16px; font-weight:800; margin:4px 0;"><a href="{ext}" target="_blank">₹{s['price']:,.2f}</a></div>
                    <div style="color:{'#16a34a' if s['change'] > 0 else '#dc2626'}; font-weight:700;">{s['change']:+.2f}%</div>
                    <span class="vol-label" style="color: {vol_color};">Volume: {s['vol_ratio']:.2f}x (20d Avg)</span>
                    <div style="margin-top:8px;">{rsi_tag}</div>
                </div>"""
        html += "</div></div>"
    html += "</div>"
    return html, nifty_change

def post():
    content, change = build_report()
    if not content: return
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
    title = f"Market Wrap {datetime.now().strftime('%d %b')}: Nifty {change:+.2f}% | Volume & Sectoral Analysis"
    payload = {
        'title': title, 'content': content, 'status': 'publish', 'categories': [CATEGORY_ID],
        'aioseo_title': "#post_title #separator_sa #site_title",
        'aioseo_description': f"Nifty ends at {change:+.2f}%. Full 170+ stock analysis with RSI technicals, valuation forecasts, and volume breakouts."
    }
    res = requests.post(WP_URL, headers=headers, json=payload)
    print(f"✅ Live: {title}" if res.status_code == 201 else f"❌ Error: {res.text}")

if __name__ == "__main__":
    post()
