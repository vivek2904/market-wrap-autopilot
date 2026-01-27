import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime
from bs4 import BeautifulSoup

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# Corrected Sector Mapping
SECTORS = {
    '^NSEI': 'NIFTY 50', '^NSEBANK': 'Banking', '^CNXIT': 'IT Services',
    '^CNXAUTO': 'Automobile', '^CNXFMCG': 'FMCG', '^CNXMETAL': 'Metals',
    '^CNXPHARMA': 'Healthcare', '^CNXENERGY': 'Energy', '^CNXFIN': 'Financial Services'
}

WATCHLIST = {
    'Banking': ['HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank', 'Kotak Bank', 'IndusInd Bank', 'Bank of Baroda', 'PNB', 'IDFC First', 'Federal Bank'],
    'IT Services': ['TCS', 'Infosys', 'HCL Tech', 'Wipro', 'Tech Mahindra', 'LTIMindtree', 'Persistent', 'Coforge', 'Mphasis', 'KPIT Tech'],
    'Financial Services': ['Bajaj Finance', 'Bajaj Finserv', 'Jio Financial', 'Chola Inv', 'REC Ltd', 'PFC', 'Shriram Fin', 'Muthoot', 'M&M Finance', 'HDFC Life'],
    'Healthcare': ['Sun Pharma', 'Cipla', 'Dr Reddys', 'Apollo Hospitals', 'Divis Lab', 'Zydus', 'Max Health', 'Torrent Pharma', 'Lupin', 'Aurobindo'],
    'Energy': ['Reliance', 'ONGC', 'NTPC', 'Power Grid', 'BPCL', 'GAIL', 'IOC', 'Adani Total', 'Petronet LNG', 'Oil India']
}

def get_valuation_insights():
    """Scrapes top text, current PE, and metrics table from worldperatio.com/area/india/"""
    url = "https://www.worldperatio.com/area/india/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Capture top text (Insight)
        paragraphs = soup.find_all('p')
        insight_text = " ".join([p.get_text() for p in paragraphs[:2]])
        if len(insight_text) > 400: insight_text = insight_text[:397] + "..."
        
        # 2. Capture Current PE
        pe_text = soup.find(string=lambda t: "P/E Ratio:" in t)
        current_pe = pe_text.split("P/E Ratio:")[-1].strip() if pe_text else "22.85"
        
        # 3. Capture Metrics Table
        tables = pd.read_html(response.text)
        metrics_df = tables[0].head(4)[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current']]
        
        return insight_text, current_pe, metrics_df.to_html(index=False, border=0, classes='pe-table')
    except:
        return "Nifty 50 valuation provides a broad perspective on current market conditions.", "22.85", "Data updating..."

def get_market_data():
    """Fetches 2 days of data to calculate 'Today vs Yesterday' move."""
    tickers = list(SECTORS.keys())
    raw_data = yf.download(tickers, period='2d', interval='1d', auto_adjust=True)
    
    # Clean data structure
    data = raw_data['Close'].dropna(axis=1, how='all')
    
    # Calculate % change from previous close
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    
    price = data.iloc[-1]['^NSEI']
    change = returns['^NSEI']
    
    sector_returns = returns.rename(index=SECTORS)
    ranked = sector_returns.sort_values(ascending=False)
    
    return price, change, ranked

def build_report():
    try:
        price, change, ranked = get_market_data()
        insight, pe, v_table = get_valuation_insights()
    except Exception as e:
        print(f"Error building report: {e}")
        return None, None

    # Identify winners and losers
    top_3 = ranked.head(4)
    bottom_3 = ranked.tail(3)

    html = f"""
    <div style="background:linear-gradient(135deg, #001529 0%, #003366 100%); color:white; padding:30px; border-radius:20px; text-align:center; font-family:sans-serif; margin-bottom:30px;">
        <h1 style="color:#1890ff; margin:0; font-size:22px;">Indian Market Wrap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="margin:20px 0;">
            <span style="font-size:18px; color:#adb5bd; display:block; margin-bottom:5px;">NIFTY 50 Index</span>
            <span style="font-size:48px; font-weight:800; display:block;">{price:,.2f}</span>
        </div>
        <div style="font-size:20px; color:{'#52c41a' if change > 0 else '#f5222d'};">
            {change:.2f}% {'▲ Bulls Leading 🚀' if change > 0 else '▼ Bears in Control 🔻'}
        </div>
    </div>

    <div style="background:white; border:1px solid #e1e4e8; padding:20px; border-radius:15px; margin-bottom:30px; font-family:sans-serif;">
        <h3 style="margin-top:0; border-bottom:2px solid #1890ff; padding-bottom:8px; color:#1a2b48;">Valuation & Market Insight</h3>
        <p style="font-size:14px; line-height:1.6; color:#444; margin-bottom:15px;">{insight}</p>
        <p style="font-size:16px;"><strong>Current P/E Ratio:</strong> <span style="color:#1890ff; font-weight:bold;">{pe}</span></p>
        <div style="overflow-x:auto; font-size:12px; margin-top:15px;">{v_table}</div>
    </div>

    <h2 style="color:#1a2b48; border-bottom:2px solid #333; padding-bottom:8px; font-family:sans-serif;">🚀 Leading Sectors</h2>
    {" ".join([f'''
    <div style="background:#f6ffed; border:1px solid #b7eb8f; padding:15px; border-radius:12px; margin-bottom:12px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong>{s}</strong>
            <b style="color:#389e0d;">+{v:.2f}%</b>
        </div>
        <p style="margin:8px 0 0 0; font-size:12px; color:#666;"><b>Heavyweights:</b> {", ".join(WATCHLIST.get(s, ["Major Stocks"]))}</p>
    </div>''' for s, v in top_3.items() if s != 'NIFTY 50'])}

    <h2 style="color:#1a2b48; border-bottom:2px solid #333; padding-bottom:8px; margin-top:30px; font-family:sans-serif;">🔻 Laggard Sectors</h2>
    {" ".join([f'''
    <div style="background:#fff1f0; border:1px solid #ffa39e; padding:15px; border-radius:12px; margin-bottom:12px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong>{s}</strong>
            <b style="color:#cf1322;">{v:.2f}%</b>
        </div>
        <p style="margin:8px 0 0 0; font-size:12px; color:#666;"><b>Under Pressure:</b> {", ".join(WATCHLIST.get(s, ["Major Stocks"]))}</p>
    </div>''' for s, v in bottom_3.items() if s != 'NIFTY 50'])}

    <p style="margin-top:30px; font-size:14px; color:#888; text-align:center;">
        <em>Data source: Yahoo Finance & WorldPERatio.</em>
    </p>
    """
    return html, change

def post():
    content, change = build_report()
    if content:
        auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
        payload = {
            'title': f"Indian Market Wrap {datetime.now().strftime('%d %b')}: Nifty {change:.2f}%",
            'content': content, 'status': 'publish', 'categories': [CATEGORY_ID]
        }
        res = requests.post(WP_URL, headers=headers, json=payload)
        print("✅ Post Created Successfully!" if res.status_code == 201 else f"❌ Error: {res.text}")

if __name__ == "__main__":
    post()
