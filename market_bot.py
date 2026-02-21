import os, requests, base64, pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime
from bs4 import BeautifulSoup
import io
import random

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# --- 1. COMPREHENSIVE SECTOR MAPPING ---
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

# --- 2. HELPERS ---
def get_links(ticker):
    clean = ticker.replace(".NS", "").upper()
    return f"https://www.google.com/finance/quote/{clean}:NSE", f"{WP_URL.split('wp-json')[0]}?s={clean}"

def get_valuation_and_summary():
    url = "https://worldperatio.com/area/india/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p', limit=3)
        summary_text = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 50])
        tables = pd.read_html(io.StringIO(response.text))
        current_pe, return_val, metrics_html = "N/A", "N/A", ""
        for df in tables:
            pe_col = [c for c in df.columns if "vs" in str(c)]
            if pe_col and current_pe == "N/A":
                current_pe = str(pe_col[0]).split("vs")[-1].strip().replace("'", "").replace(")", "").replace("(", "")
            if 'Period' in df.columns and any('Average P/E' in col for col in df.columns):
                metrics_html = df[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current P/E']].head(5).to_html(index=False, border=0, classes='valuation-table')
            if not df.empty and '1 Years' in str(df.iloc[:, 0].values):
                return_val = f"{df.iloc[0, 6]}%"
        return summary_text, current_pe, return_val, metrics_html
    except:
        return "Nifty valuation metrics provide context for current market levels.", "Analyzing...", "N/A", ""

def fetch_analysis_data():
    all_tickers = list(set([f"{t}.NS" for sublist in SECTOR_MAP.values() for t in sublist]))
    data = yf.download(all_tickers, period="60d", interval="1d", auto_adjust=True)
    results = {}
    for t in all_tickers:
        try:
            prices = data['Close'][t].dropna()
            if len(prices) < 20: continue
            curr, prev = prices.iloc[-1], prices.iloc[-2]
            results[t.replace(".NS", "")] = {
                'price': curr, 'change': ((curr/prev)-1)*100, 
                'rsi': ta.rsi(prices, length=14).iloc[-1], 
                'trend': "UP" if curr > prices.rolling(window=20).mean().iloc[-1] else "DOWN"
            }
        except: continue
    return results

# --- 3. REPORT BUILDER ---
def build_report():
    idx_data = yf.download(list(INDEX_TICKERS.keys()), period='5d')['Close'].dropna(axis=1)
    idx_returns = ((idx_data.iloc[-1] / idx_data.iloc[-2] - 1) * 100).dropna()
    nifty_price, nifty_change = idx_data.iloc[-1].get('^NSEI', 0), idx_returns.get('^NSEI', 0)
    stock_analysis = fetch_analysis_data()
    summary, pe, target_return, v_table = get_valuation_and_summary()

    try: pe_float = float(pe)
    except: pe_float = 23.5
    val_status = "🚀 High Growth Premium" if pe_float > 25 else "⚖️ Growth Value" if pe_float > 21 else "💎 Massive Opportunity"

    html = f"""
    <style>
        .market-card {{ font-family: 'Inter', sans-serif; max-width: 950px; margin: auto; color: #1e293b; line-height: 1.6; }}
        .header-box {{ background: #0f172a; color: white; padding: 50px 25px; border-radius: 24px; text-align: center; margin-bottom: 30px; }}
        .insight-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 30px; border-radius: 20px; margin-bottom: 30px; }}
        .valuation-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
        .valuation-table th {{ background: #f1f5f9; text-align: left; padding: 12px; border-bottom: 2px solid #e2e8f0; }}
        .sector-block {{ background: white; border: 1px solid #e2e8f0; border-radius: 20px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
        .stock-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; margin-top: 20px; }}
        .stock-card {{ border: 1px solid #f1f5f9; padding: 12px; border-radius: 10px; font-size: 13px; background: #fff; }}
        .tag {{ font-size: 10px; padding: 2px 5px; border-radius: 4px; font-weight: bold; text-transform: uppercase; margin-right: 4px; }}
        a {{ text-decoration: none; color: #3b82f6; font-weight: 600; }}
    </style>
    <div class="market-card">
        <div class="header-box">
            <span style="opacity:0.7; letter-spacing:2px; font-weight:600;">DAILY NIFTY 50 INSIGHTS</span>
            <span style="font-size:64px; font-weight:800; display:block;">{nifty_price:,.2f}</span>
            <div style="font-size:24px; color:{'#4ade80' if nifty_change > 0 else '#f87171'}; font-weight:700;">
                {'▲' if nifty_change > 0 else '▼'} {nifty_change:.2f}% ({val_status})
            </div>
        </div>
        <div class="insight-box">
            <h2 style="margin-top:0; color:#0f172a;">📊 Valuation Analysis & Forecast</h2>
            <p style="font-size:17px;">{summary}</p>
            <div style="display:flex; gap:40px; margin:25px 0; background:white; padding:20px; border-radius:15px;">
                <div><small style="color:#64748b; font-weight:700;">CURRENT P/E</small><br><b style="font-size:28px;">{pe}</b></div>
                <div><small style="color:#64748b; font-weight:700;">1Y MEDIAN FORECAST</small><br><b style="font-size:28px; color:#22c55e;">{target_return}</b></div>
            </div>
            {v_table}
        </div>
        <h2 style="border-left:8px solid #3b82f6; padding-left:15px; margin:50px 0 25px; font-size:28px;">🏗️ Sectoral Performance (Gainers First)</h2>
    """

    performance_map = {INDEX_TICKERS[k]: v for k, v in idx_returns.items() if k in INDEX_TICKERS}
    sorted_sectors = sorted(performance_map.items(), key=lambda item: item[1], reverse=True)

    for sector_name, s_return in sorted_sectors:
        if sector_name not in SECTOR_MAP: continue
        html += f"""
        <div class="sector-block">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #f1f5f9; padding-bottom:10px;">
                <h3 style="margin:0; font-size:22px;">{sector_name}</h3>
                <b style="font-size:20px; color:{'#16a34a' if s_return > 0 else '#dc2626'};">{'+' if s_return > 0 else ''}{s_return:.2f}%</b>
            </div>
            <div class="stock-grid">"""
        for t in SECTOR_MAP[sector_name]:
            s = stock_analysis.get(t, {'price': 0, 'change': 0, 'rsi': 50})
            ext, int_link = get_links(t)
            rsi_tag = '<span class="tag" style="background:#fee2e2; color:#ef4444;">Overbought</span>' if s['rsi'] > 70 else \
                      ('<span class="tag" style="background:#dcfce7; color:#22c55e;">Oversold</span>' if s['rsi'] < 30 else '')
            html += f"""
                <div class="stock-card">
                    <div style="font-weight:700;"><a href="{int_link}">{t}</a></div>
                    <div style="font-size:16px; font-weight:800; margin-bottom:4px;"><a href="{ext}" target="_blank" style="color:#1e293b;">₹{s['price']:,.2f}</a></div>
                    <div style="font-weight:700; color:{'#16a34a' if s['change'] > 0 else '#dc2626'};">{'+' if s['change'] > 0 else ''}{s['change']:.2f}%</div>
                    <div style="margin-top:10px;">{rsi_tag}</div>
                </div>"""
        html += "</div></div>"
    html += "</div>"
    return html, nifty_change

# --- 4. POSTING & SEO ---
def post():
    content, change = build_report()
    if not content: return
    
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
    
    # Custom SEO Data
    title = f"Market Wrap {datetime.now().strftime('%d %b')}: Nifty {change:.2f}% | Top Performing Sectors"
    seo_desc = f"Nifty ends at {change:.2f}% today. Full breakdown of 170+ stocks, P/E valuation analytics, and sectoral momentum for the Indian market."
    
    payload = {
        'title': title,
        'content': content,
        'status': 'publish',
        'categories': [CATEGORY_ID],
        # AIOSEO Integration
        'aioseo_title': "#post_title #separator_sa #site_title",
        'aioseo_description': seo_desc
    }
    
    res = requests.post(WP_URL, headers=headers, json=payload)
    if res.status_code == 201:
        print(f"✅ Live: {title}")
    else:
        print(f"❌ Error: {res.text}")

if __name__ == "__main__":
    post()
