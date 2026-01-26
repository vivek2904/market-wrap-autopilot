import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime
from bs4 import BeautifulSoup
import re

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

def get_valuation_data():
    """Dynamically scrapes P/E, Returns, and Tables from worldperatio.com"""
    url = "https://www.worldperatio.com/area/united-states/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. DYNAMIC P/E EXTRACTION
        # Searches for the text 'P/E Ratio:' and grabs the following number
        pe_text = soup.find(string=re.compile(r"P/E Ratio:"))
        current_pe = re.search(r"\d+\.\d+", pe_text).group() if pe_text else "N/A"
        
        # 2. DYNAMIC RETURN EXTRACTION
        # Searches for 'Expected Forward 1Y Return' in the HTML text
        return_text = soup.find(string=re.compile(r"Expected Forward 1Y Return"))
        # Looking for a percentage or float following that text
        forward_return = "N/A"
        if return_text:
            # Check the parent or sibling for the actual value (3.13)
            val_match = re.search(r"(-?\d+\.\d+)%", soup.get_text())
            if val_match:
                forward_return = f"{val_match.group(1)}%"

        # 3. DYNAMIC TABLE EXTRACTION
        tables = pd.read_html(response.text)
        metrics_table = ""
        for df in tables:
            if 'Period' in df.columns and any('Average P/E' in col for col in df.columns):
                # Select requested columns and format
                clean_df = df[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current']].head(4)
                metrics_table = clean_df.to_html(index=False, border=0, classes='valuation-table')
                break
        
        return current_pe, forward_return, metrics_table
    except Exception as e:
        print(f"Dynamic Scrape Error: {e}")
        return "N/A", "N/A", ""

def get_market_data():
    all_tickers = list(SECTORS.keys()) + ['^GSPC']
    raw_data = yf.download(all_tickers, period='5d', interval='1d', auto_adjust=True)
    data = raw_data['Close']
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    sp_change = returns['^GSPC']
    direction = "Bulls Leading 🚀" if sp_change > 0 else "Bears in Control 🔻"
    sector_returns = returns[list(SECTORS.keys())].rename(index=SECTORS)
    ranked = sector_returns.sort_values(ascending=False)
    return sp_change, direction, ranked

def build_report():
    try:
        sp_change, direction, ranked = get_market_data()
        current_pe, forward_return, metrics_table = get_valuation_data()
    except Exception as e:
        print(f"Build Error: {e}")
        return None, None

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

    <div style="background:white; border:1px solid #e1e4e8; padding:25px; border-radius:15px; font-family:sans-serif; margin-bottom:30px;">
        <h2 style="color:#1a2b48; margin-top:0; border-left: 4px solid #1890ff; padding-left: 15px;">Valuation & Forward Return Outlook</h2>
        <div style="display:flex; justify-content:space-between; margin:20px 0;">
            <div><strong>Current P/E Ratio:</strong> <span style="font-size:20px; color:#1890ff; font-weight:bold;">{current_pe}</span></div>
            <div><strong>Expected 1Y Forward Return:</strong> <span style="font-size:20px; color:#52c41a; font-weight:bold;">{forward_return}</span></div>
        </div>
        <div style="overflow-x:auto;">
            {metrics_table}
        </div>
    </div>

    <h2 style="margin-top:40px; border-bottom:2px solid #333; padding-bottom:10px; color:#1a2b48;">🚀 Leading Sectors</h2>
    {" ".join([f'''
    <div style="background:#f6ffed; border:1px solid #b7eb8f; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:18px;">{s}</strong>
            <span style="color:#389e0d; font-size:20px; font-weight:bold;">+{v:.2f}%</span>
        </div>
        <p style="margin:10px 0 0 0; font-size:13px; color:#555; line-height:1.5;"><strong>Sector Heavyweights:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in top_3.items()])}

    <h2 style="margin-top:40px; border-bottom:2px solid #333; padding-bottom:10px; color:#1a2b48;">🔻 Laggard Sectors</h2>
    {" ".join([f'''
    <div style="background:#fff1f0; border:1px solid #ffa39e; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:18px;">{s}</strong>
            <span style="color:#cf1322; font-size:20px; font-weight:bold;">{v:.2f}%</span>
        </div>
        <p style="margin:10px 0 0 0; font-size:13px; color:#555; line-height:1.5;"><strong>Under Pressure:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in bottom_3.items()])}

    <p style="margin-top:30px; font-size:14px; color:#888; text-align:center;">
        <em>Data source: Yahoo Finance & WorldPERatio.</em>
    </p>
    """
    return html, sp_change

def post():
    content, change = build_report()
    if content is None: return
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
