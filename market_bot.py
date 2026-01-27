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

# TICKER MAPPING
SECTORS = {
    '^NSEI': 'NIFTY 50', '^NSEBANK': 'Nifty Bank', '^CNXIT': 'IT Services',
    '^CNXAUTO': 'Automobile', '^CNXFMCG': 'FMCG', '^CNXMETAL': 'Metals',
    '^CNXPHARMA': 'Pharma', '^CNXENERGY': 'Energy', '^CNXFIN': 'Financial Services',
    '^CNXPSUBANK': 'PSU Bank', '^CNXREALTY': 'Realty', '^CNXMEDIA': 'Media',
    'NIFTY_CONSUMPTION.NS': 'Consumption', '^CNXINFRA': 'Infrastructure', 
    'NIFTY_COMMODITIES.NS': 'Commodities', '^CNXPSE': 'PSE', 'NIFTY_CPSE.NS': 'CPSE'
}

# 5 CORE HEAVYWEIGHTS PER SECTOR
WATCHLIST = {
    'Nifty Bank': ['HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank', 'Kotak Bank'],
    'IT Services': ['TCS', 'Infosys', 'HCL Tech', 'Wipro', 'LTIMindtree'],
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
        tables = pd.read_html(io.StringIO(response.text))
        metrics_df = tables[0].head(4)[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current']]
        
        # Style the Valuation Table
        v_table_html = metrics_df.to_html(index=False, border=0, classes='valuation-table')
        return insight_text, current_pe, v_table_html
    except:
        return "Market valuation metrics provide context for current market levels.", "22.85", ""

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
    <style>
        .market-card {{ font-family: 'Inter', -apple-system, sans-serif; max-width: 800px; margin: auto; }}
        .header-box {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 40px 20px; border-radius: 24px; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); }}
        .nifty-label {{ font-size: 18px; color: #94a3b8; font-weight: 500; display: block; letter-spacing: 0.05em; margin-bottom: 8px; }}
        .nifty-price {{ font-size: 56px; font-weight: 800; display: block; margin-bottom: 5px; line-height: 1; }}
        .nifty-change {{ font-size: 22px; font-weight: 600; padding: 8px 16px; border-radius: 12px; display: inline-block; margin-top: 15px; }}
        
        .section-title {{ font-size: 24px; font-weight: 700; color: #1e293b; border-left: 5px solid #3b82f6; padding-left: 15px; margin: 40px 0 20px; }}
        .insight-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 25px; border-radius: 20px; line-height: 1.7; color: #334155; font-size: 16px; }}
        .pe-stat {{ color: #3b82f6; font-weight: 800; font-size: 20px; }}
        
        .valuation-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; border-radius: 12px; overflow: hidden; }}
        .valuation-table th {{ background: #f1f5f9; color: #475569; text-align: left; padding: 12px; font-weight: 600; border-bottom: 2px solid #e2e8f0; }}
        .valuation-table td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; }}

        .sector-pill {{ background: white; border: 1px solid #e2e8f0; padding: 20px; border-radius: 18px; margin-bottom: 15px; transition: transform 0.2s; }}
        .sector-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .sector-name {{ font-size: 18px; font-weight: 700; color: #1e293b; }}
        .sector-val {{ font-size: 20px; font-weight: 800; }}
        .heavyweights {{ font-size: 14px; color: #64748b; line-height: 1.4; }}
    </style>

    <div class="market-card">
        <div class="header-box">
            <span class="nifty-label">NIFTY 50 INDEX</span>
            <span class="nifty-price">{price:,.2f}</span>
            <div class="nifty-change" style="background: {'rgba(34, 197, 94, 0.15)' if change > 0 else 'rgba(239, 68, 68, 0.15)'}; color: {'#22c55e' if change > 0 else '#ef4444'};">
                {'+' if change > 0 else ''}{change:.2f}% {'▲ Bulls Leading 🚀' if change > 0 else '▼ Bears in Control 🔻'}
            </div>
        </div>

        <div class="insight-box">
            <h3 style="margin-top:0; font-size:20px; color:#1e293b;">Market Insight & Valuation</h3>
            <p>{insight}</p>
            <p>Current P/E Ratio: <span class="pe-stat">{pe}</span></p>
            <div style="overflow-x:auto;">{v_table}</div>
        </div>

        <h2 class="section-title">🚀 Leading Sectors</h2>
        {" ".join([f'''
        <div class="sector-pill" style="border-left: 6px solid #22c55e;">
            <div class="sector-header">
                <span class="sector-name">{s}</span>
                <span class="sector-val" style="color:#16a34a;">+{v:.2f}%</span>
            </div>
            <div class="heavyweights"><b>Top Stocks:</b> {", ".join(WATCHLIST.get(s, ["Index Stocks"]))}</div>
        </div>''' for s, v in ranked.head(4).items() if s != 'NIFTY 50'])}

        <h2 class="section-title">🔻 Laggard Sectors</h2>
        {" ".join([f'''
        <div class="sector-pill" style="border-left: 6px solid #ef4444;">
            <div class="sector-header">
                <span class="sector-name">{s}</span>
                <span class="sector-val" style="color:#dc2626;">{v:.2f}%</span>
            </div>
            <div class="heavyweights"><b>Under Pressure:</b> {", ".join(WATCHLIST.get(s, ["Index Stocks"]))}</div>
        </div>''' for s, v in ranked.tail(3).items() if s != 'NIFTY 50'])}
    </div>
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
        print("✅ Post Created!" if res.status_code == 201 else f"❌ Error: {res.text}")

if __name__ == "__main__":
    post()
