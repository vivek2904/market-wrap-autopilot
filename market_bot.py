import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime
from bs4 import BeautifulSoup
import io

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# REFINED TICKER MAPPING (Fixed for Yahoo Finance stability)
SECTORS = {
    '^NSEI': 'NIFTY 50', '^NSEBANK': 'Nifty Bank', '^CNXIT': 'IT Services',
    '^CNXAUTO': 'Automobile', '^CNXFMCG': 'FMCG', '^CNXMETAL': 'Metals',
    '^CNXPHARMA': 'Pharma', '^CNXENERGY': 'Energy', '^CNXFIN': 'Financial Services',
    '^CNXPSUBANK': 'PSU Bank', '^CNXREALTY': 'Realty', '^CNXMEDIA': 'Media',
    '^CNXSERVICE': 'Services', 'NIFTY_CONSUMPTION.NS': 'Consumption', 
    '^CNXINFRA': 'Infrastructure', 'NIFTY_COMMODITIES.NS': 'Commodities', 
    '^CNXPSE': 'PSE', 'NIFTY_CPSE.NS': 'CPSE'
}

WATCHLIST = {
    'Nifty Bank': ['HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank', 'Kotak Bank'],
    'IT Services': ['TCS', 'Infosys', 'HCL Tech', 'Wipro', 'Tech Mahindra'],
    'Automobile': ['M&M', 'Maruti', 'Tata Motors', 'Bajaj Auto', 'Eicher Motors'],
    'FMCG': ['HUL', 'ITC', 'Nestle India', 'Britannia', 'Godrej CP'],
    'Metals': ['Tata Steel', 'JSW Steel', 'Hindalco', 'Jindal Steel', 'Vedanta'],
    'Pharma': ['Sun Pharma', 'Cipla', 'Dr Reddys', 'Lupin', 'Aurobindo'],
    'Energy': ['Reliance', 'NTPC', 'ONGC', 'Power Grid', 'BPCL'],
    'Financial Services': ['Bajaj Finance', 'HDFC Bank', 'ICICI Bank', 'Bajaj Finserv', 'REC'],
    'PSU Bank': ['SBI', 'Bank of Baroda', 'Canara Bank', 'Union Bank', 'PNB'],
    'Realty': ['DLF', 'Macrotech', 'Godrej Prop', 'Oberoi Realty', 'Prestige'],
    'Media': ['Zee Ent', 'Sun TV', 'PVR Inox', 'Network18', 'TV18'],
    'Consumption': ['ITC', 'HUL', 'Titan', 'Asian Paints', 'Nestle'],
    'Infrastructure': ['Reliance', 'L&T', 'Bharti Airtel', 'NTPC', 'Adani Port'],
    'PSE': ['NTPC', 'ONGC', 'Power Grid', 'Coal India', 'BEL'],
    'CPSE': ['NTPC', 'ONGC', 'Power Grid', 'Coal India', 'NHPC']
}

def get_valuation_data():
    url = "https://www.worldperatio.com/area/india/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        insight_text = " ".join([p.get_text() for p in paragraphs[:2]])
        pe_text = soup.find(string=lambda t: "P/E Ratio:" in t)
        current_pe = pe_text.split("P/E Ratio:")[-1].strip() if pe_text else "22.85"
        
        # Wrapped in StringIO to fix the FutureWarning
        tables = pd.read_html(io.StringIO(response.text))
        metrics_df = tables[0].head(4)[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current']]
        return insight_text, current_pe, metrics_df.to_html(index=False, border=0)
    except:
        return "Nifty 50 valuation metrics provide context for current market levels.", "22.85", ""

def get_market_data():
    raw_data = yf.download(list(SECTORS.keys()), period='5d', auto_adjust=True)['Close']
    data = raw_data.dropna(axis=1, how='any').dropna(axis=0)
    if len(data) < 2: return None, None, None
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    price = data.iloc[-1]['^NSEI']
    change = returns['^NSEI']
    ranked = returns.rename(index=SECTORS).sort_values(ascending=False)
    return price, change, ranked

def build_report():
    price, change, ranked = get_market_data()
    if price is None: return None, None
    insight, pe, v_table = get_valuation_data()

    html = f"""
    <div style="background:#001529; color:white; padding:30px; border-radius:20px; text-align:center; font-family:sans-serif; margin-bottom:30px;">
        <h1 style="color:#1890ff; margin:0; font-size:24px;">Indian Market Wrap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="margin:20px 0;">
            <span style="font-size:24px; display:block; margin-bottom:5px; color:#8c8c8c;">NIFTY 50 Index</span>
            <span style="font-size:48px; font-weight:800; display:block;">{price:,.2f}</span>
        </div>
        <div style="font-size:20px; color:{'#52c41a' if change > 0 else '#f5222d'};">
            {change:.2f}% {'▲ Bulls Leading 🚀' if change > 0 else '▼ Bears in Control 🔻'}
        </div>
    </div>
    <div style="background:white; border:1px solid #e1e4e8; padding:25px; border-radius:15px; font-family:sans-serif; margin-bottom:30px;">
        <h3 style="color:#1a2b48; margin-top:0; border-bottom:2px solid #1890ff; padding-bottom:10px;">Valuation Insight</h3>
        <p style="font-size:14px; line-height:1.6; color:#444;">{insight}</p>
        <p style="font-size:16px;"><strong>Current P/E Ratio:</strong> <span style="color:#1890ff; font-weight:bold;">{pe}</span></p>
        <div style="overflow-x:auto; font-size:12px; margin-top:15px;">{v_table}</div>
    </div>
    <h2 style="color:#1a2b48; border-bottom:2px solid #333; padding-bottom:8px;">🚀 Leading Sectors</h2>
    {" ".join([f'''
    <div style="background:#f6ffed; border:1px solid #b7eb8f; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between;">
            <strong>{s}</strong><b style="color:#389e0d;">+{v:.2f}%</b>
        </div>
        <p style="margin:10px 0 0 0; font-size:12px; color:#666;"><b>Heavyweights:</b> {", ".join(WATCHLIST.get(s, ["Index Stocks"]))}</p>
    </div>''' for s, v in ranked.head(4).items() if s != 'NIFTY 50'])}
    <h2 style="color:#1a2b48; border-bottom:2px solid #333; padding-bottom:8px; margin-top:30px;">🔻 Laggard Sectors</h2>
    {" ".join([f'''
    <div style="background:#fff1f0; border:1px solid #ffa39e; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between;">
            <strong>{s}</strong><b style="color:#cf1322;">{v:.2f}%</b>
        </div>
        <p style="margin:10px 0 0 0; font-size:12px; color:#666;"><b>Under Pressure:</b> {", ".join(WATCHLIST.get(s, ["Index Stocks"]))}</p>
    </div>''' for s, v in ranked.tail(3).items() if s != 'NIFTY 50'])}
    """
    return html, change

def post():
    content, change = build_report()
    if content:
        auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
        
        # FIXED SYNTAX: Standard dictionary definition
        payload = {
            'title': f"Indian Market Wrap {datetime.now().strftime('%d %b')}: Nifty {change:.2f}%",
            'content': content,
            'status': 'publish',
            'categories': [CATEGORY_ID]
        }
        
        res = requests.post(WP_URL, headers=headers, json=payload)
        print("✅ Post Created!" if res.status_code == 201 else f"❌ Error: {res.text}")

if __name__ == "__main__":
    post()
