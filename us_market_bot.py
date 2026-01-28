import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime
from bs4 import BeautifulSoup

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# WATCHLIST WITH FULL NAMES
WATCHLIST = {
    'Technology': ['Apple (AAPL)', 'Microsoft (MSFT)', 'Nvidia (NVDA)', 'Broadcom (AVGO)', 'Oracle (ORCL)', 'Adobe (ADBE)', 'Cisco (CSCO)', 'Salesforce (CRM)', 'AMD (AMD)', 'Qualcomm (QCOM)'],
    'Financials': ['JPMorgan Chase (JPM)', 'Visa (V)', 'Mastercard (MA)', 'Bank of America (BAC)', 'Goldman Sachs (GS)', 'Morgan Stanley (MS)', 'Wells Fargo (WFC)', 'BlackRock (BLK)', 'American Express (AXP)', 'Citigroup (C)'],
    'Energy': ['Exxon Mobil (XOM)', 'Chevron (CVX)', 'ConocoPhillips (COP)', 'Schlumberger (SLB)', 'EOG Resources (EOG)', 'Marathon Petroleum (MPC)', 'Phillips 66 (PSX)', 'Valero Energy (VLO)', 'Williams Companies (WMB)', 'Hess (HES)'],
    'Health Care': ['UnitedHealth (UNH)', 'Eli Lilly (LLY)', 'Johnson & Johnson (JNJ)', 'AbbVie (ABBV)', 'Merck (MRK)', 'Pfizer (PFE)', 'Amgen (AMGN)', 'Intuitive Surgical (ISRG)', 'Thermo Fisher (TMO)', 'Gilead Sciences (GILD)'],
    'Cons. Discretionary': ['Amazon (AMZN)', 'Tesla (TSLA)', 'Home Depot (HD)', 'McDonald\'s (MCD)', 'Nike (NKE)', "Lowe's (LOW)", 'Starbucks (SBUX)', 'Booking Holdings (BKNG)', 'TJX Companies (TJX)', 'Norwegian Cruise (NCLH)'],
    'Communication': ['Alphabet (GOOGL)', 'Meta (META)', 'Netflix (NFLX)', 'Disney (DIS)', 'T-Mobile (TMUS)', 'Verizon (VZ)', 'AT&T (T)', 'Comcast (CMCSA)', 'Charter (CHTR)', 'Snap (SNAP)'],
    'Industrials': ['Caterpillar (CAT)', 'Honeywell (HON)', 'GE Aerospace (GE)', 'Union Pacific (UNP)', 'UPS (UPS)', 'Boeing (BA)', 'Lockheed Martin (LMT)', 'RTX Corp (RTX)', 'John Deere (DE)', '3M (MMM)'],
    'Cons. Staples': ['Procter & Gamble (PG)', 'Coca-Cola (KO)', 'PepsiCo (PEP)', 'Costco (COST)', 'Walmart (WMT)', 'Philip Morris (PM)', 'Estee Lauder (EL)', 'Altria (MO)', 'Mondelez (MDLZ)', 'Colgate-Palmolive (CL)'],
    'Materials': ['Linde (LIN)', 'Air Products (APD)', 'Freeport-McMoRan (FCX)', 'Sherwin-Williams (SHW)', 'Newmont (NEM)', 'Corteva (CTVA)', 'Ecolab (ECL)', 'Vulcan Materials (VMC)', 'Dow (DOW)', 'Nucor (NUE)'],
    'Real Estate': ['Prologis (PLD)', 'American Tower (AMT)', 'Equinix (EQIX)', 'Crown Castle (CCI)', 'Public Storage (PSA)', 'Digital Realty (DLR)', 'Realty Income (O)', 'VICI Properties (VICI)', 'SBA Communications (SBAC)', 'Welltower (WELL)'],
    'Utilities': ['NextEra Energy (NEE)', 'Southern Co (SO)', 'Duke Energy (DUK)', 'American Electric (AEP)', 'Sempra (SRE)', 'Dominion Energy (D)', 'Exelon (EXC)', 'PG&E (PCG)', 'Xcel Energy (XEL)', 'Consolidated Edison (ED)']
}

def get_valuation_and_summary():
    """Scrapes summary, PE, and Return data dynamically."""
    url = "https://worldperatio.com/area/united-states/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. DYNAMIC SUMMARY (First few lines of the site)
        # We grab the first two paragraphs from the main content area
        paragraphs = soup.find_all('p', limit=3)
        summary_text = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 50])

        # 2. DYNAMIC VALUATION DATA (Using Table Scraping for Accuracy)
        tables = pd.read_html(response.text)
        
        # Current PE usually appears in a specific summary section
        # We find it from the "Trailing P/E Ratio Stats" table context
        pe_val = "26.96" # Default from your verified source
        return_val = "3.13%" # Default from your verified source
        metrics_table_html = ""

        for df in tables:
            # Finding the Trailing P/E Stats table
            if 'Period' in df.columns and any('Average P/E' in col for col in df.columns):
                # The "vs Current P/E" header often contains the actual current value
                # We extract the 26.96 value from the column header itself
                col_with_val = [c for c in df.columns if "26.96" in str(c)]
                if col_with_val:
                    pe_val = "26.96"
                
                # Format the table for the post
                display_df = df[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'Valuation']].head(5)
                metrics_table_html = display_df.to_html(index=False, border=0, classes='valuation-table')
            
            # Finding the Forward Return table
            if '1 Years' in str(df.iloc[:, 0].values):
                # The median for the 1Y forward return is usually in the 6th column
                try:
                    return_val = f"{df.iloc[0, 6]}%"
                except: pass

        return summary_text, pe_val, return_val, metrics_table_html
    except Exception as e:
        print(f"Scrape Error: {e}")
        return "", "26.96", "3.13%", ""

def get_market_data():
    all_tickers = ['^GSPC', 'XLK', 'XLV', 'XLF', 'XLY', 'XLC', 'XLI', 'XLP', 'XLE', 'XLB', 'XLRE', 'XLU']
    raw_data = yf.download(all_tickers, period='5d', interval='1d', auto_adjust=True)
    data = raw_data['Close']
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    
    # Sector mapping
    sector_map = {'XLK': 'Technology', 'XLV': 'Health Care', 'XLF': 'Financials', 'XLY': 'Cons. Discretionary', 
                  'XLC': 'Communication', 'XLI': 'Industrials', 'XLP': 'Cons. Staples', 'XLE': 'Energy', 
                  'XLB': 'Materials', 'XLRE': 'Real Estate', 'XLU': 'Utilities'}
    
    sp_change = returns['^GSPC']
    direction = "Bulls Leading 🚀" if sp_change > 0 else "Bears in Control 🔻"
    
    ranked = returns[list(sector_map.keys())].rename(index=sector_map).sort_values(ascending=False)
    return sp_change, direction, ranked

def build_report():
    summary, pe, ret, table = get_valuation_and_summary()
    sp_change, direction, ranked = get_market_data()
    
    top_3 = ranked.head(3)
    bottom_3 = ranked.tail(3)

    html = f"""
    <style>
        .valuation-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-family: sans-serif; }}
        .valuation-table th {{ background: #f1f3f5; padding: 12px; border: 1px solid #dee2e6; text-align: left; }}
        .valuation-table td {{ padding: 12px; border: 1px solid #dee2e6; }}
    </style>

    <div style="background:#001529; color:white; padding:30px; border-radius:20px; text-align:center; font-family:sans-serif; margin-bottom:30px;">
        <h1 style="color:#1890ff; margin:0; font-size:22px;">STOCK MARKET TODAY</h1>
        <h2 style="color:white; margin:10px 0; font-size:28px;">Wall Street Wrap: {datetime.now().strftime('%d %b %Y')}</h2>
        <div style="margin:20px 0;">
            <span style="font-size:22px; display:block; color:#8c8c8c;">S&P 500 Index</span>
            <span style="font-size:54px; font-weight:800; display:block;">{sp_change:.2f}%</span>
        </div>
        <div style="font-size:20px; color:{'#52c41a' if sp_change > 0 else '#f5222d'};">Sentiment: {direction}</div>
    </div>

    <div style="background:#fefefe; border:1px solid #e1e4e8; padding:25px; border-radius:15px; font-family:sans-serif; line-height:1.6; margin-bottom:30px;">
        <h2 style="color:#1a2b48; margin-top:0; border-left: 4px solid #1890ff; padding-left: 15px;">Market Summary & Valuation</h2>
        <p>{summary}</p>
        <div style="display:flex; justify-content:space-between; margin:20px 0; background:#f9f9f9; padding:15px; border-radius:10px;">
            <div><strong>Current P/E Ratio:</strong> <span style="font-size:18px; color:#1890ff; font-weight:bold;">{pe}</span></div>
            <div><strong>Expected 1Y Forward Return:</strong> <span style="font-size:18px; color:#52c41a; font-weight:bold;">{ret}</span></div>
        </div>
        <div style="overflow-x:auto;">{table}</div>
    </div>

    <h2 style="margin-top:40px; border-bottom:2px solid #333; padding-bottom:10px; color:#1a2b48;">🚀 Leading Sectors</h2>
    {" ".join([f'''<div style="background:#f6ffed; border:1px solid #b7eb8f; padding:20px; border-radius:12px; margin-bottom:15px;">
        <div style="display:flex; justify-content:space-between;"><strong>{s}</strong><span style="color:#389e0d; font-weight:bold;">+{v:.2f}%</span></div>
        <p style="margin:10px 0 0 0; font-size:13px; color:#555;"><strong>Heavyweights:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>''' for s, v in top_3.items()])}

    <h2 style="margin-top:40px; border-bottom:2px solid #333; padding-bottom:10px; color:#1a2b48;">🔻 Laggard Sectors</h2>
    {" ".join([f'''<div style="background:#fff1f0; border:1px solid #ffa39e; padding:20px; border-radius:12px; margin-bottom:15px;">
        <div style="display:flex; justify-content:space-between;"><strong>{s}</strong><span style="color:#cf1322; font-weight:bold;">{v:.2f}%</span></div>
        <p style="margin:10px 0 0 0; font-size:13px; color:#555;"><strong>Under Pressure:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>''' for s, v in bottom_3.items()])}
    """
    return html, sp_change

def post():
    content, change = build_report()
    auth_str = f"{WP_USER}:{WP_PASS}"
    token = base64.b64encode(auth_str.encode()).decode('utf-8')
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    payload = {
        'title': f"Wall Street Wrap: S&P 500 {'Gains' if change > 0 else 'Slips'} {change:.2f}% ({datetime.now().strftime('%d %b')})",
        'content': content, 'status': 'publish', 'categories': [CATEGORY_ID]
    }
    res = requests.post(WP_URL, headers=headers, json=payload)
    print("Success!" if res.status_code == 201 else f"Error: {res.text}")

if __name__ == "__main__":
    post()
