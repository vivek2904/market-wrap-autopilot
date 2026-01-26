import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime

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

# Watchlist with Full Names for Better UX
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

def get_market_data():
    etfs = list(SECTORS.keys())
    all_tickers = etfs + ['^GSPC']
    raw_data = yf.download(all_tickers, period='5d', interval='1d', auto_adjust=True)
    data = raw_data['Close']
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    sector_returns = returns[etfs].rename(index=SECTORS)
    return returns['^GSPC'], sector_returns.sort_values(ascending=False)

def build_report():
    try:
        sp_change, ranked = get_market_data()
    except: return None, None, None

    status = "Advances" if sp_change > 0 else "Declines"
    
    html = f"""
    <div style="background:#001529; color:white; padding:30px; border-radius:20px; text-align:center; font-family:sans-serif; margin-bottom:30px;">
        <p style="text-transform:uppercase; letter-spacing:2px; font-size:14px; margin:0; color:#1890ff;">Stock Market Today</p>
        <h1 style="color:white; margin:10px 0; font-size:24px;">Wall Street Wrap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="margin:20px 0;">
            <span style="font-size:20px; display:block; margin-bottom:5px; color:#8c8c8c;">S&P 500 Performance</span>
            <span style="font-size:48px; font-weight:800; display:block;">{sp_change:.2f}%</span>
        </div>
        <div style="font-size:20px; color:{'#52c41a' if sp_change > 0 else '#f5222d'};">Market Direction: {'Bullish 🚀' if sp_change > 0 else 'Bearish 🔻'}</div>
    </div>

    <h2 style="color:#1a2b48; border-left:5px solid #1890ff; padding-left:15px;">Market Intelligence Brief</h2>
    <p style="line-height:1.6; color:#444;">The US markets {status.lower()} today. Below are the key sectoral moves and the heavyweights driving the action.</p>

    <h3 style="margin-top:30px; color:#389e0d;">🚀 Leading Sectors</h3>
    {" ".join([f'''
    <div style="background:#f6ffed; border:1px solid #b7eb8f; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:18px;">{s}</strong>
            <span style="color:#389e0d; font-size:20px; font-weight:bold;">+{v:.2f}%</span>
        </div>
        <p style="margin:10px 0 0 0; font-size:13px; color:#555;"><strong>Key Movers:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in ranked.head(3).items()])}

    <h3 style="margin-top:40px; color:#cf1322;">🔻 Laggard Sectors</h3>
    {" ".join([f'''
    <div style="background:#fff1f0; border:1px solid #ffa39e; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:18px;">{s}</strong>
            <span style="color:#cf1322; font-size:20px; font-weight:bold;">{v:.2f}%</span>
        </div>
        <p style="margin:10px 0 0 0; font-size:13px; color:#555;"><strong>Under Pressure:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in ranked.tail(3).items()])}

    <div style="background:#f9f9f9; border:1px dashed #ccc; padding:25px; border-radius:12px; margin-top:40px; text-align:center; font-family:sans-serif;">
        <h4 style="margin:0 0 15px 0; color:#333;">Master Your Own Analysis</h4>
        <div style="display:flex; gap:10px; justify-content:center; flex-wrap:wrap;">
            <a href="YOUR_TRADINGVIEW_LINK" style="background:#1890ff; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold;">Analyze Charts on TradingView</a>
            <a href="YOUR_BROKER_LINK" style="background:#52c41a; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold;">Open a Trading Account</a>
        </div>
        <p style="margin:15px 0 0 0; font-size:12px; color:#888;">Visit our <strong><a href="https://longniftyshort.com/">India Stock Market PE Ratio</a></strong> dashboard for long-term valuation context.</p>
    </div>
    """
    return html, sp_change, ranked

def post():
    content, change, ranked = build_report()
    if not content: return
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    
    payload = {
        'title': f"Stock Market Today: S&P 500 {'Gains' if change > 0 else 'Slips'} {change:.2f}% | Wall Street Wrap {datetime.now().strftime('%d %b')}",
        'content': content,
        'status': 'publish',
        'categories': [CATEGORY_ID],
        'excerpt': f"US Market Recap for {datetime.now().strftime('%B %d')}. S&P 500 moves {change:.2f}% as {ranked.index[0]} sector leads the way."
    }
    
    requests.post(WP_URL, headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}, json=payload)

if __name__ == "__main__":
    post()
