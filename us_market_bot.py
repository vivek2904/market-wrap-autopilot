import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime
from bs4 import BeautifulSoup

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# Full Name Watchlist (10 per sector)
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
    """Dynamically scrapes P/E and Forward Return data from World PE Ratio."""
    url = "https://worldperatio.com/area/united-states/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Searching for the P/E value in the specific table or text blocks
        # Based on site structure, we look for the Current P/E Ratio label
        pe_text = soup.find(text=lambda t: "Current P/E Ratio" in t)
        pe_val = pe_text.find_next().text.strip() if pe_text else "N/A"
        
        # Searching for 1Y Forward Return
        fwd_text = soup.find(text=lambda t: "Expected Forward 1Y Return" in t)
        fwd_val = fwd_text.find_next().text.strip() if fwd_text else "N/A"
        
        # Searching for the 80% Prediction Interval
        interval_text = soup.find(text=lambda t: "80% Prediction Interval" in t)
        interval_val = interval_text.find_next().text.strip() if interval_text else "N/A"
        
        return pe_val, fwd_val, interval_val
    except Exception as e:
        print(f"Valuation Scraper Error: {e}")
        return "N/A", "N/A", "N/A"

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
        pe_val, fwd_val, interval_val = get_valuation_data()
    except Exception as e:
        print(f"Report build error: {e}")
        return None, None, None

    status = "Advances" if sp_change > 0 else "Declines"
    
    html = f"""
    <div style="background:#001529; color:white; padding:30px; border-radius:20px; text-align:center; font-family:sans-serif; margin-bottom:30px;">
        <p style="text-transform:uppercase; letter-spacing:2px; font-size:14px; margin:0; color:#1890ff;">Stock Market Today</p>
        <h1 style="color:white; margin:10px 0; font-size:24px;">Wall Street Wrap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="margin:20px 0;">
            <span style="font-size:20px; display:block; margin-bottom:5px; color:#8c8c8c;">S&P 500 Daily Performance</span>
            <span style="font-size:48px; font-weight:800; display:block;">{sp_change:.2f}%</span>
        </div>
        <div style="font-size:20px; color:{'#52c41a' if sp_change > 0 else '#f5222d'};">Sentiment: {'Bullish 🚀' if sp_change > 0 else 'Bearish 🔻'}</div>
    </div>

    <h2 style="color:#1a2b48; border-left:5px solid #1890ff; padding-left:15px;">S&P 500 Valuation & Forward Outlook</h2>
    <div style="background:#f0f7ff; border:1px solid #1890ff; padding:20px; border-radius:12px; margin-bottom:30px; font-family:sans-serif;">
        <p style="margin:0 0 10px 0;"><strong>Live S&P 500 P/E Ratio:</strong> {pe_val}</p>
        <p style="margin:0 0 10px 0;"><strong>Expected 1Y Forward Return:</strong> <span style="color:#1890ff; font-weight:bold;">{fwd_val}%</span></p>
        <p style="margin:0; font-size:13px; color:#666;"><strong>80% Prediction Interval:</strong> {interval_val}</p>
        <p style="margin:10px 0 0 0; font-size:11px; font-style:italic; color:#888;">*Data dynamically retrieved from World PE Ratio statistical models.</p>
    </div>

    <h2 style="color:#1a2b48; border-left:5px solid #1890ff; padding-left:15px;">🚀 Top Performing Sectors</h2>
    {" ".join([f'''
    <div style="background:#f6ffed; border:1px solid #b7eb8f; padding:20px; border-radius:12px; margin-bottom:15px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:18px;">{s}</strong>
            <span style="color:#389e0d; font-size:20px; font-weight:bold;">+{v:.2f}%</span>
        </div>
        <p style="margin:10px 0 0 0; font-size:13px; color:#555;"><strong>Heavyweights:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>
    ''' for s, v in ranked.head(3).items()])}

    <h2 style="margin-top:40px; color:#1a2b48; border-left:5px solid #cf1322; padding-left:15px;">🔻 Laggard Sectors</h2>
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
        <p style="margin:15px 0 0 0; font-size:12px; color:#888;">Visit our <strong><a href="https://longniftyshort.com/">India Stock Market PE Ratio</a></strong> dashboard for global valuation context.</p>
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
        'excerpt': f"US Market Recap: S&P 500 moves {change:.2f}% as {ranked.index[0]} sector leads. Includes live P/E valuation and 1Y forward return models."
    }
    
    requests.post(WP_URL, headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}, json=payload)

if __name__ == "__main__":
    post()
