import os, requests, base64, pandas as pd
import yfinance as yf
from datetime import datetime
from bs4 import BeautifulSoup

# --- SECURE CONFIG ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 # Replace with your Indian Market category ID

# Nifty 50 Sector Mapping (NSE Indices)
SECTORS = {
    '^NSEBANK': 'Banking', 'NIFTY_IT.NS': 'IT Services', 'NIFTY_FIN_SERVICE.NS': 'Financial Services',
    'NIFTY_AUTO.NS': 'Automobiles', 'NIFTY_FMCG.NS': 'FMCG', 'NIFTY_METAL.NS': 'Metals & Mining',
    'NIFTY_PHARMA.NS': 'Healthcare', 'NIFTY_ENERGY.NS': 'Oil & Gas', 'NIFTY_REALTY.NS': 'Real Estate'
}

# 10 Heavyweights per Nifty Sector
WATCHLIST = {
    'Banking': ['HDFC Bank', 'ICICI Bank', 'State Bank of India', 'Axis Bank', 'Kotak Mahindra Bank', 'IndusInd Bank', 'Bank of Baroda', 'PNB', 'IDFC First Bank', 'Federal Bank'],
    'IT Services': ['TCS', 'Infosys', 'HCL Tech', 'Wipro', 'Tech Mahindra', 'LTIMindtree', 'Persistent Systems', 'Coforge', 'Mphasis', 'KPIT Tech'],
    'Financial Services': ['Bajaj Finance', 'Bajaj Finserv', 'Jio Financial', 'Chola Investment', 'REC Ltd', 'PFC', 'Shriram Finance', 'Muthoot Finance', 'Mahindra Finance', 'HDFC Life'],
    'Automobiles': ['Maruti Suzuki', 'Mahindra & Mahindra', 'Tata Motors', 'Bajaj Auto', 'Eicher Motors', 'Hero MotoCorp', 'TVS Motor', 'Ashok Leyland', 'Bharat Forge', 'Apollo Tyres'],
    'FMCG': ['Hindustan Unilever', 'ITC', 'Nestle India', 'Britannia', 'Tata Consumer', 'Godrej Consumer', 'Dabur', 'Marico', 'Varun Beverages', 'Colgate-Palmolive'],
    'Metals & Mining': ['JSW Steel', 'Tata Steel', 'Hindalco', 'Coal India', 'Vedanta', 'Jindal Steel', 'NMDC', 'National Aluminium', 'SAIL', 'APL Apollo'],
    'Healthcare': ['Sun Pharma', 'Cipla', 'Dr. Reddys', 'Apollo Hospitals', 'Divis Lab', 'Zydus Lifesciences', 'Max Healthcare', 'Torrent Pharma', 'Lupin', 'Aurobindo Pharma'],
    'Oil & Gas': ['Reliance Industries', 'ONGC', 'NTPC', 'Power Grid', 'BPCL', 'GAIL', 'IOC', 'Adani Total Gas', 'Petronet LNG', 'Oil India'],
    'Real Estate': ['DLF', 'Godrej Properties', 'Macrotech Developers', 'Oberoi Realty', 'Phoenix Mills', 'Prestige Estates', 'Brigade Enterprises', 'Sobha', 'Sunteck Realty', 'SignatureGlobal']
}

def get_valuation_data():
    url = "https://worldperatio.com/area/india/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Scrape Summary
        paragraphs = soup.find_all('p', limit=3)
        summary = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 50])

        # Dynamic Table Extraction
        tables = pd.read_html(response.text)
        pe_val, ret_val, table_html = "21.8", "11.7%", "" # Fallback to common Nifty averages

        for df in tables:
            if 'Period' in df.columns and any('Average P/E' in col for col in df.columns):
                # Clean table for Nifty context
                display_df = df[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'Valuation']].head(5)
                table_html = display_df.to_html(index=False, border=0, classes='valuation-table')
                break
        
        return summary, pe_val, ret_val, table_html
    except:
        return "Market valuation context unavailable.", "21.8", "11.7%", ""

def get_market_data():
    all_tickers = ['^NSEI'] + list(SECTORS.keys())
    data = yf.download(all_tickers, period='2d', auto_adjust=True)['Close']
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    
    ranked = returns[list(SECTORS.keys())].rename(index=SECTORS).sort_values(ascending=False)
    return returns['^NSEI'], ranked

def build_report():
    summary, pe, ret, table = get_valuation_data()
    nifty_change, ranked = get_market_data()
    
    html = f"""
    <style>
        .valuation-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-family: sans-serif; }}
        .valuation-table th {{ background: #f8f9fa; padding: 10px; border: 1px solid #dee2e6; text-align: left; }}
        .valuation-table td {{ padding: 10px; border: 1px solid #dee2e6; font-size: 13px; }}
    </style>

    <div style="background:#1a2b48; color:white; padding:35px; border-radius:15px; text-align:center; font-family:sans-serif; margin-bottom:25px;">
        <h1 style="color:#ffd700; margin:0; font-size:22px;">NIFTY 50 CLOSING BELL</h1>
        <h2 style="color:white; margin:10px 0; font-size:28px;">{datetime.now().strftime('%d %b %Y')}</h2>
        <div style="font-size:52px; font-weight:800; margin:10px 0;">{nifty_change:.2f}%</div>
        <div style="font-size:18px;">Sentiment: {'Bulls Charging 🐂' if nifty_change > 0 else 'Bears Clawing 🐻'}</div>
    </div>

    <div style="background:#fff; border:1px solid #e1e4e8; padding:20px; border-radius:12px; font-family:sans-serif; line-height:1.6;">
        <h2 style="color:#1a2b48; margin-top:0; border-left: 4px solid #ffd700; padding-left: 12px;">Valuation Summary</h2>
        <p>{summary}</p>
        <div style="display:flex; justify-content:space-between; margin:15px 0; background:#f4f7f6; padding:15px; border-radius:8px;">
            <div><strong>Nifty P/E:</strong> <span style="color:#1a2b48; font-weight:bold;">{pe}</span></div>
            <div><strong>Avg 5Y Return:</strong> <span style="color:#28a745; font-weight:bold;">{ret}</span></div>
        </div>
        <div style="overflow-x:auto;">{table}</div>
    </div>

    <h2 style="margin-top:30px; color:#1a2b48; font-family:sans-serif;">🚀 Leading Sectors</h2>
    {" ".join([f'''<div style="background:#f0fff4; border:1px solid #c6f6d5; padding:15px; border-radius:10px; margin-bottom:10px;">
        <div style="display:flex; justify-content:space-between;"><strong>{s}</strong><span style="color:#2f855a;">+{v:.2f}%</span></div>
        <p style="margin:8px 0 0 0; font-size:12px; color:#4a5568;"><strong>Heavyweights:</strong> {', '.join(WATCHLIST.get(s, []))}</p>
    </div>''' for s, v in ranked.head(3).items()])}
    """
    return html, nifty_change

def post():
    content, change = build_report()
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    payload = {
        'title': f"Nifty Wrap: Market {'Advances' if change > 0 else 'Dips'} {change:.2f}% ({datetime.now().strftime('%d %b')})",
        'content': content, 'status': 'publish', 'categories': [CATEGORY_ID]
    }
    requests.post(WP_URL, headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}, json=payload)

if __name__ == "__main__":
    post()
