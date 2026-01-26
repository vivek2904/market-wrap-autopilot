import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime
from bs4 import BeautifulSoup

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# Sector ETF Mapping - Global Scope
SECTORS = {
    'XLK': 'Technology', 'XLV': 'Health Care', 'XLF': 'Financials',
    'XLY': 'Cons. Discretionary', 'XLC': 'Communication', 'XLI': 'Industrials',
    'XLP': 'Cons. Staples', 'XLE': 'Energy', 'XLB': 'Materials',
    'XLRE': 'Real Estate', 'XLU': 'Utilities'
}

# Watchlist - 10 Stocks per Sector with Full Names
WATCHLIST = {
    'Technology': ['Apple (AAPL)', 'Microsoft (MSFT)', 'NVIDIA (NVDA)', 'Broadcom (AVGO)', 'Oracle (ORCL)', 'Adobe (ADBE)', 'Cisco (CSCO)', 'Salesforce (CRM)', 'AMD (AMD)', 'Qualcomm (QCOM)'],
    'Financials': ['JPMorgan (JPM)', 'Visa (V)', 'Mastercard (MA)', 'Bank of America (BAC)', 'Goldman Sachs (GS)', 'Morgan Stanley (MS)', 'Wells Fargo (WFC)', 'BlackRock (BLK)', 'Amex (AXP)', 'Citigroup (C)'],
    'Energy': ['ExxonMobil (XOM)', 'Chevron (CVX)', 'ConocoPhillips (COP)', 'Schlumberger (SLB)', 'EOG Resources (EOG)', 'Marathon (MPC)', 'Phillips 66 (PSX)', 'Valero (VLO)', 'Williams (WMB)', 'Hess (HES)'],
    'Health Care': ['UnitedHealth (UNH)', 'Eli Lilly (LLY)', 'Johnson & Johnson (JNJ)', 'AbbVie (ABBV)', 'Merck (MRK)', 'Pfizer (PFE)', 'Amgen (AMGN)', 'Intuitive Surgical (ISRG)', 'Thermo Fisher (TMO)', 'Gilead (GILD)'],
    'Cons. Discretionary': ['Amazon (AMZN)', 'Tesla (TSLA)', 'Home Depot (HD)', 'McDonalds (MCD)', 'Nike (NKE)', 'Lowes (LOW)', 'Starbucks (SBUX)', 'Booking (BKNG)', 'TJX Cos (TJX)', 'Norwegian Cruise (NCLH)'],
    'Communication': ['Alphabet/Google (GOOGL)', 'Meta/Facebook (META)', 'Netflix (NFLX)', 'Disney (DIS)', 'T-Mobile (TMUS)', 'Verizon (VZ)', 'AT&T (T)', 'Comcast (CMCSA)', 'Charter (CHTR)', 'Snapchat (SNAP)'],
    'Industrials': ['Caterpillar (CAT)', 'Honeywell (HON)', 'GE Aerospace (GE)', 'Union Pacific (UNP)', 'UPS (UPS)', 'Boeing (BA)', 'Lockheed Martin (LMT)', 'Raytheon (RTX)', 'John Deere (DE)', '3M (MMM)'],
    'Cons. Staples': ['Procter & Gamble (PG)', 'Coca-Cola (KO)', 'PepsiCo (PEP)', 'Costco (COST)', 'Walmart (WMT)', 'Philip Morris (PM)', 'Estee Lauder (EL)', 'Altria (MO)', 'Mondelez (MDLZ)', 'Colgate (CL)'],
    'Materials': ['Linde (LIN)', 'Air Products (APD)', 'Freeport (FCX)', 'Sherwin-Williams (SHW)', 'Newmont (NEM)', 'Corteva (CTVA)', 'Ecolab (ECL)', 'Vulcan (VMC)', 'Dow (DOW)', 'Nucor (NUE)'],
    'Real Estate': ['Prologis (PLD)', 'American Tower (AMT)', 'Equinix (EQIX)', 'Crown Castle (CCI)', 'Public Storage (PSA)', 'Digital Realty (DLR)', 'Realty Income (O)', 'VICI Properties (VICI)', 'SBA Comm (SBAC)', 'Welltower (WELL)'],
    'Utilities': ['NextEra Energy (NEE)', 'Southern Co (SO)', 'Duke Energy (DUK)', 'American Electric (AEP)', 'Sempra (SRE)', 'Dominion (D)', 'Exelon (EXC)', 'PG&E (PCG)', 'Xcel (XEL)', 'Consol Edison (ED)']
}

def get_valuation_data():
    """Scrapes Live P/E & Forward Return Model from worldperatio.com"""
    url = "https://worldperatio.com/area/united-states/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        pe_val = soup.find(text=lambda t: "Current P/E Ratio" in t).find_next().text.strip()
        fwd_val = soup.find(text=lambda t: "Expected Forward 1Y Return" in t).find_next().text.strip()
        interval = soup.find(text=lambda t: "80% Prediction Interval" in t).find_next().text.strip()
        return pe_val, fwd_val, interval
    except:
        return "26.96", "3.13", "[-25.11, 31.38]" # Fallback to latest stable data

def get_market_data():
    etfs = list(SECTORS.keys())
    raw_data = yf.download(etfs + ['^GSPC'], period='5d', interval='1d', auto_adjust=True)
    data = raw_data['Close']
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    ranked = returns[etfs].rename(index=SECTORS).sort_values(ascending=False)
    return returns['^GSPC'], ranked

def build_report():
    try:
        sp_change, ranked = get_market_data()
        pe, fwd, interval = get_valuation_data()
    except: return None, None, None

    status = "Advances" if sp_change > 0 else "Declines"
    html = f"""
    <div style="background:#001529; color:white; padding:30px; border-radius:20px; text-align:center; font-family:sans-serif; margin-bottom:30px;">
        <p style="text-transform:uppercase; letter-spacing:2px; font-size:14px; margin:0; color:#1890ff;">Stock Market Today</p>
        <h1 style="color:white; margin:10px 0; font-size:24px;">Wall Street Wrap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="margin:20px 0;">
            <span style="font-size:22px; display:block; margin-bottom:5px; color:#8c8c8c;">S&P 500 Index</span>
            <span style="font-size:48px; font-weight:800; display:block;">{sp_change:.2f}%</span>
        </div>
        <div style="font-size:20px; color:{'#52c41a' if sp_change > 0 else '#f5222d'};">Sentiment: {'Bullish 🚀' if sp_change > 0 else 'Bearish 🔻'}</div>
    </div>

    <h2 style="color:#1a2b48; border-left:5px solid #1890ff; padding-left:15px;">Market Intelligence Brief</h2>
    <div style="background:#f0f7ff; border:1px solid #1890ff; padding:20px; border-radius:12px; margin-bottom:30px; font-family:sans-serif;">
        <p style="margin:0 0 8px 0;"><strong>Current P/E Ratio:</strong> {pe}</p>
        <p style="margin:0 0 8px 0;"><strong>Expected 1Y Forward Return:</strong> <span style="color:#1890ff; font-weight:bold;">{fwd}%</span></p>
        <p style="margin:0; font-size:12px; color:#666;"><strong>80% Prediction Interval:</strong> {interval}</p>
    </div>

    <h3 style="color:#389e0d;">🚀 Sector Outperformers</h3>
    {" ".join([f'''
    <div style="background:#f6ffed; border:1px solid #b7eb8f; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:17px;">{s}</strong>
            <span style="color:#389e0d; font-size:18px; font-weight:bold;">+{v:.2f}%</span>
        </div>
        <p style="margin:10px 0 0 0; font-size:12px; color:#555;"><strong>Heavyweights:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in ranked.head(3).items()])}

    <h3 style="color:#cf1322; margin-top:35px;">🔻 Sector Laggards</h3>
    {" ".join([f'''
    <div style="background:#fff1f0; border:1px solid #ffa39e; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:17px;">{s}</strong>
            <span style="color:#cf1322; font-size:18px; font-weight:bold;">{v:.2f}%</span>
        </div>
        <p style="margin:10px 0 0 0; font-size:12px; color:#555;"><strong>Under Pressure:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in ranked.tail(3).items()])}

    <div style="background:#f9f9f9; border:1px dashed #ccc; padding:25px; border-radius:12px; margin-top:40px; text-align:center; font-family:sans-serif;">
        <h4 style="margin:0 0 15px 0; color:#333;">Master Your Own Analysis</h4>
        <div style="display:flex; gap:10px; justify-content:center; flex-wrap:wrap;">
            <a href="YOUR_TRADINGVIEW_LINK" style="background:#1890ff; color:white; padding:10px 18px; text-decoration:none; border-radius:5px; font-weight:bold; font-size:13px;">Charts on TradingView</a>
            <a href="YOUR_BROKER_LINK" style="background:#52c41a; color:white; padding:10px 18px; text-decoration:none; border-radius:5px; font-weight:bold; font-size:13px;">Open Account</a>
        </div>
        <p style="margin:15px 0 0 0; font-size:11px; color:#888;">Visit our <strong><a href="https://longniftyshort.com/">India Stock Market PE Ratio</a></strong> dashboard for context.</p>
    </div>
    """
    return html, sp_change, ranked

def post():
    content, change, ranked = build_report()
    if not content: return
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    title = f"Stock Market Today: S&P 500 {'Gains' if change > 0 else 'Slips'} {change:.2f}% | Wall Street Wrap"
    payload = {'title': title, 'content': content, 'status': 'publish', 'categories': [CATEGORY_ID]}
    requests.post(WP_URL, headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}, json=payload)

if __name__ == "__main__":
    post()
