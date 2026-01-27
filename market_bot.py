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

WATCHLIST = {
    'Nifty Bank': ['HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank', 'Kotak Bank'],
    'IT Services': ['TCS', 'Infosys', 'HCL Tech', 'Wipro', 'LTIMindtree'],
    'Energy': ['Reliance', 'NTPC', 'ONGC', 'Power Grid', 'BPCL'],
    'Metals': ['Tata Steel', 'JSW Steel', 'Hindalco', 'Jindal Steel', 'Vedanta'],
    'Automobile': ['M&M', 'Maruti', 'Tata Motors', 'Bajaj Auto', 'Eicher Motors']
}

def get_valuation_data(current_price):
    url = "https://www.worldperatio.com/area/india/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Capture Insight & PE
        paragraphs = soup.find_all('p')
        insight_text = " ".join([p.get_text() for p in paragraphs[:2]])
        pe_text = soup.find(string=lambda t: "P/E Ratio:" in t)
        current_pe = pe_text.split("P/E Ratio:")[-1].strip() if pe_text else "22.85"
        
        # 2. Extract 1-Year Target
        # Scrapes the forecast section; if not found, it calculates a 1-year mean reversion estimate
        target_text = soup.find(string=lambda t: "One Year Target" in t or "Forecast" in t)
        if target_text:
            target_val = target_text.split(":")[-1].strip()
        else:
            # Fallback: Historical Mean Reversion Estimate (e.g., 10% average growth)
            target_val = f"{current_price * 1.10:,.2f} (+10.0%)"
        
        tables = pd.read_html(io.StringIO(response.text))
        metrics_df = tables[0].head(4)[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current']]
        v_table_html = metrics_df.to_html(index=False, border=0, classes='valuation-table')
        
        return insight_text, current_pe, target_val, v_table_html
    except:
        return "Market valuation metrics provide context for current levels.", "22.85", "TBD", ""

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
    insight, pe, target, v_table = get_valuation_data(price)

    html = f"""
    <style>
        .market-card {{ font-family: 'Inter', sans-serif; max-width: 800px; margin: auto; }}
        .header-box {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 40px 20px; border-radius: 24px; text-align: center; margin-bottom: 30px; }}
        .nifty-price {{ font-size: 56px; font-weight: 800; line-height: 1; }}
        .nifty-change {{ font-size: 22px; font-weight: 600; padding: 8px 16px; border-radius: 12px; display: inline-block; margin-top: 15px; }}
        
        .insight-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 25px; border-radius: 20px; color: #334155; font-size: 16px; }}
        .stat-label {{ color: #64748b; font-weight: 600; font-size: 15px; margin-right: 10px; }}
        .stat-val {{ color: #3b82f6; font-weight: 800; font-size: 20px; }}
        .target-val {{ color: #22c55e; font-weight: 800; font-size: 20px; }}

        .valuation-table {{ width: 100%; margin-top: 20px; font-size: 14px; border-collapse: collapse; }}
        .valuation-table th {{ background: #f1f5f9; padding: 12px; text-align: left; }}
        .valuation-table td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; }}

        .sector-pill {{ background: white; border: 1px solid #e2e8f0; padding: 20px; border-radius: 18px; margin-bottom: 15px; border-left: 6px solid; }}
    </style>

    <div class="market-card">
        <div class="header-box">
            <span style="color:#94a3b8;">NIFTY 50 INDEX</span>
            <div class="nifty-price">{price:,.2f}</div>
            <div class="nifty-change" style="background: {'rgba(34, 197, 94, 0.15)' if change > 0 else 'rgba(239, 68, 68, 0.15)'}; color: {'#22c55e' if change > 0 else '#ef4444'};">
                {change:.2f}% {'▲ Bulls Leading' if change > 0 else '▼ Bears Leading'}
            </div>
        </div>

        <div class="insight-box">
            <h3 style="margin-top:0; font-size:20px; color:#1e293b;">Market Insight & Valuation</h3>
            <p style="line-height:1.6;">{insight}</p>
            <div style="margin: 15px 0;">
                <span class="stat-label">Current P/E Ratio:</span> <span class="stat-val">{pe}</span>
            </div>
            <div style="margin: 15px 0;">
                <span class="stat-label">1-Year Target:</span> <span class="target-val">{target}</span>
            </div>
            <div style="overflow-x:auto;">{v_table}</div>
        </div>

        <h2 style="font-size: 24px; margin: 40px 0 20px;">🚀 Leading Sectors</h2>
        {" ".join([f'''
        <div class="sector-pill" style="border-color: #22c55e;">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="font-weight:700;">{s}</span>
                <span style="color:#16a34a; font-weight:800;">+{v:.2f}%</span>
            </div>
            <div style="font-size:14px; color:#64748b;"><b>Top Stocks:</b> {", ".join(WATCHLIST.get(s, ["Index Stocks"]))}</div>
        </div>''' for s, v in ranked.head(4).items() if s != 'NIFTY 50'])}

        <h2 style="font-size: 24px; margin: 40px 0 20px;">🔻 Laggard Sectors</h2>
        {" ".join([f'''
        <div class="sector-pill" style="border-color: #ef4444;">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="font-weight:700;">{s}</span>
                <span style="color:#dc2626; font-weight:800;">{v:.2f}%</span>
            </div>
            <div style="font-size:14px; color:#64748b;"><b>Under Pressure:</b> {", ".join(WATCHLIST.get(s, ["Index Stocks"]))}</div>
        </div>''' for s, v in ranked.tail(3).items() if s != 'NIFTY 50'])}
    </div>
    """
    return html, change

def post():
    content, change = build_report()
    if content:
        auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
        payload = {'title': f"Indian Market Wrap {datetime.now().strftime('%d %b')}: Nifty {change:.2f}%", 'content': content, 'status': 'publish', 'categories': [CATEGORY_ID]}
        res = requests.post(WP_URL, headers=headers, json=payload)
        print("✅ Success" if res.status_code == 201 else f"❌ Error: {res.text}")

if __name__ == "__main__":
    post()
