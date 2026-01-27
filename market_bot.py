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

# COMPREHENSIVE SECTOR MAPPING
SECTORS = {
    '^NSEI': 'NIFTY 50', '^NSEBANK': 'Nifty Bank', '^CNXIT': 'IT Services',
    '^CNXAUTO': 'Automobile', '^CNXFMCG': 'FMCG', '^CNXMETAL': 'Metals',
    '^CNXPHARMA': 'Pharma', '^CNXENERGY': 'Energy', '^CNXFIN': 'Financial Services',
    '^CNXPSUBANK': 'PSU Bank', '^CNXREALTY': 'Realty', '^CNXMEDIA': 'Media',
    'NIFTY_CONSUMPTION.NS': 'Consumption', '^CNXINFRA': 'Infrastructure', 
    'NIFTY_COMMODITIES.NS': 'Commodities', '^CNXPSE': 'PSE', 'NIFTY_CPSE.NS': 'CPSE'
}

# FULL HEAVYWEIGHT LIST
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

def get_valuation_and_summary():
    """Scrapes India summary, PE, and Return data dynamically like the US bot."""
    url = "https://worldperatio.com/area/india/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. DYNAMIC SUMMARY
        paragraphs = soup.find_all('p', limit=3)
        summary_text = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 50])

        # 2. DYNAMIC VALUATION DATA
        tables = pd.read_html(io.StringIO(response.text))
        pe_val = "22.85" 
        return_val = "12.45%" # Default median for India
        metrics_table_html = ""

        for df in tables:
            # Trailing P/E Stats Table
            if 'Period' in df.columns and any('Average P/E' in col for col in df.columns):
                # Extract PE from the column that contains the current value (e.g., vs 22.85)
                pe_col = [c for c in df.columns if "vs" in str(c)]
                if pe_col: pe_val = str(pe_col[0]).split("vs")[-1].strip()
                
                display_df = df[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current P/E']].head(5)
                metrics_table_html = display_df.to_html(index=False, border=0, classes='valuation-table')
            
            # Forward Return Table (1Y Target)
            # Looks for the row containing '1 Years' and grabs the median from column index 6
            if not df.empty and '1 Years' in str(df.iloc[:, 0].values):
                try:
                    return_val = f"{df.iloc[0, 6]}%"
                except: pass

        return summary_text, pe_val, return_val, metrics_table_html
    except Exception as e:
        print(f"Scrape Error: {e}")
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
    summary, pe, target_return, v_table = get_valuation_and_summary()

    html = f"""
    <style>
        .market-card {{ font-family: 'Inter', -apple-system, sans-serif; max-width: 800px; margin: auto; }}
        .header-box {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 40px 20px; border-radius: 24px; text-align: center; margin-bottom: 30px; }}
        .nifty-price {{ font-size: 56px; font-weight: 800; display: block; line-height: 1; }}
        .nifty-change {{ font-size: 22px; font-weight: 600; padding: 8px 16px; border-radius: 12px; display: inline-block; margin-top: 15px; }}
        
        .insight-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 25px; border-radius: 20px; color: #334155; font-size: 16px; line-height: 1.7; }}
        .stat-group {{ display: flex; gap: 30px; margin-top: 20px; padding: 15px; background: white; border-radius: 12px; border: 1px solid #e2e8f0; }}
        .stat-item {{ display: flex; flex-direction: column; }}
        .stat-label {{ font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase; }}
        .stat-val {{ font-size: 22px; font-weight: 800; color: #3b82f6; }}
        .target-val {{ color: #22c55e; }}

        .valuation-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
        .valuation-table th {{ background: #f1f5f9; text-align: left; padding: 12px; font-weight: 600; }}
        .valuation-table td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; }}

        .sector-pill {{ background: white; border: 1px solid #e2e8f0; padding: 20px; border-radius: 18px; margin-bottom: 15px; border-left: 6px solid; }}
    </style>

    <div class="market-card">
        <div class="header-box">
            <span style="color:#94a3b8; font-weight:500; letter-spacing:1px;">NIFTY 50 INDEX</span>
            <span class="nifty-price">{price:,.2f}</span>
            <div class="nifty-change" style="background: {'rgba(34, 197, 94, 0.15)' if change > 0 else 'rgba(239, 68, 68, 0.15)'}; color: {'#22c55e' if change > 0 else '#ef4444'};">
                {'+' if change > 0 else ''}{change:.2f}% {'▲ Bulls Leading 🚀' if change > 0 else '▼ Bears in Control 🔻'}
            </div>
        </div>

        <div class="insight-box">
            <h3 style="margin-top:0; font-size:22px; color:#1e293b;">Market Insight & Valuation</h3>
            <p>{summary}</p>
            
            <div class="stat-group">
                <div class="stat-item">
                    <span class="stat-label">Current P/E</span>
                    <span class="stat-val">{pe}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">1Y Expected Return</span>
                    <span class="stat-val target-val">{target_return}</span>
                </div>
            </div>

            <div style="overflow-x:auto;">{v_table}</div>
        </div>

        <h2 style="font-size:24px; font-weight:700; color:#1e293b; margin:40px 0 20px;">🚀 Leading Sectors</h2>
        {" ".join([f'''
        <div class="sector-pill" style="border-color: #22c55e;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:18px; font-weight:700; color:#1e293b;">{s}</span>
                <span style="font-size:20px; font-weight:800; color:#16a34a;">+{v:.2f}%</span>
            </div>
            <div style="font-size:14px; color:#64748b;"><b>Top Stocks:</b> {", ".join(WATCHLIST.get(s, ["Index Stocks"]))}</div>
        </div>''' for s, v in ranked.head(4).items() if s != 'NIFTY 50'])}

        <h2 style="font-size:24px; font-weight:700; color:#1e293b; margin:40px 0 20px;">🔻 Laggard Sectors</h2>
        {" ".join([f'''
        <div class="sector-pill" style="border-color: #ef4444;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:18px; font-weight:700; color:#1e293b;">{s}</span>
                <span style="font-size:20px; font-weight:800; color:#dc2626;">{v:.2f}%</span>
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
        payload = {
            'title': f"Indian Market Wrap {datetime.now().strftime('%d %b')}: Nifty {change:.2f}%",
            'content': content, 'status': 'publish', 'categories': [CATEGORY_ID]
        }
        res = requests.post(WP_URL, headers=headers, json=payload)
        print("✅ Post Created!" if res.status_code == 201 else f"❌ Error: {res.text}")

if __name__ == "__main__":
    post()
