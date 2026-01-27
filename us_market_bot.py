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

# 1. THE COMPLETE 18+ SECTOR LIST
SECTORS = {
    '^NSEI': 'NIFTY 50', '^NSEBANK': 'Nifty Bank', '^CNXIT': 'IT Services',
    '^CNXAUTO': 'Automobile', '^CNXFMCG': 'FMCG', '^CNXMETAL': 'Metals',
    '^CNXPHARMA': 'Pharma', '^CNXENERGY': 'Energy', '^CNXFIN': 'Financial Services',
    '^CNXPSUBANK': 'PSU Bank', '^CNXREALTY': 'Realty', '^CNXMEDIA': 'Media',
    '^CNXSERVICE': 'Services', 'NIFTY_CONSUMPTION.NS': 'Consumption', 
    '^CNXINFRA': 'Infrastructure', 'NIFTY_COMMODITIES.NS': 'Commodities', 
    '^CNXPSE': 'PSE', 'NIFTY_CPSE.NS': 'CPSE'
}

# 2. 10 UNIQUE HEAVYWEIGHTS FOR EVERY SECTOR
WATCHLIST = {
    'Nifty Bank': ['HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank', 'Kotak Bank', 'IndusInd Bank', 'Bank of Baroda', 'PNB', 'IDFC First', 'Federal Bank'],
    'IT Services': ['TCS', 'Infosys', 'HCL Tech', 'Wipro', 'Tech Mahindra', 'LTIMindtree', 'Persistent', 'Coforge', 'Mphasis', 'KPIT Tech'],
    'Automobile': ['M&M', 'Maruti', 'Tata Motors', 'Bajaj Auto', 'Eicher Motors', 'TVS Motor', 'Hero MotoCorp', 'Ashok Leyland', 'MRF', 'Balkrishna Ind'],
    'FMCG': ['HUL', 'ITC', 'Nestle India', 'Britannia', 'Godrej CP', 'Dabur', 'Marico', 'Varun Beverages', 'Colgate', 'Tata Consumer'],
    'Metals': ['Tata Steel', 'JSW Steel', 'Hindalco', 'Jindal Steel', 'Vedanta', 'NMDC', 'SAIL', 'National Aluminium', 'APL Apollo', 'Ratnamani'],
    'Pharma': ['Sun Pharma', 'Cipla', 'Dr Reddys', 'Lupin', 'Aurobindo Pharma', 'Zydus Life', 'Divis Lab', 'Alkem', 'Torrent Pharma', 'Abbott'],
    'Energy': ['Reliance', 'NTPC', 'ONGC', 'Power Grid', 'BPCL', 'Adani Green', 'Tata Power', 'IOC', 'Gail', 'Adani Energy'],
    'Financial Services': ['Bajaj Finance', 'HDFC Bank', 'ICICI Bank', 'Bajaj Finserv', 'Chola Inv', 'REC', 'PFC', 'Shriram Finance', 'SBI Life', 'HDFC Life'],
    'PSU Bank': ['SBI', 'Bank of Baroda', 'Canara Bank', 'Union Bank', 'IOB', 'PNB', 'Indian Bank', 'Bank of India', 'UCO Bank', 'Central Bank'],
    'Realty': ['DLF', 'Macrotech', 'Godrej Prop', 'Oberoi Realty', 'Prestige', 'Phoenix Mills', 'Brigade', 'Sobha', 'SignatureGlobal', 'Sunteck'],
    'Media': ['Zee Ent', 'Sun TV', 'PVR Inox', 'Network18', 'TV18 Broadcast', 'Nazara Tech', 'Dish TV', 'Hathway', 'Saregama', 'Tips Industries'],
    'Consumption': ['ITC', 'HUL', 'Titan', 'Asian Paints', 'Nestle', 'Trent', 'DMart', 'Zomato', 'Britannia', 'Page Industries'],
    'Infrastructure': ['Reliance', 'L&T', 'Bharti Airtel', 'NTPC', 'Adani Port', 'UltraTech', 'ONGC', 'Grasim', 'IIFL', 'Power Grid'],
    'PSE': ['NTPC', 'ONGC', 'Power Grid', 'Coal India', 'BEL', 'HAL', 'BPCL', 'IOC', 'PFC', 'REC'],
    'CPSE': ['NTPC', 'ONGC', 'Power Grid', 'Coal India', 'BEL', 'NHPC', 'SJVN', 'NBCC', 'Oil India', 'Cochin Shipyard'],
    'Commodities': ['Reliance', 'Tata Steel', 'JSW Steel', 'HINDALCO', 'NTPC', 'ONGC', 'Ambuja Cement', 'Grasim', 'Vedanta', 'Coal India'],
    'Services': ['L&T', 'Adani Ports', 'Apollo Hosp', 'HDFC Life', 'SBI Life', 'Trend', 'IndiGo', 'VBL', 'TATACOMM', 'GMR Infra']
}

def get_valuation_and_summary():
    url = "https://worldperatio.com/area/india/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p', limit=3)
        summary_text = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 50])
        tables = pd.read_html(io.StringIO(response.text))
        pe_val, return_val, metrics_table_html = "22.85", "12.45%", ""
        for df in tables:
            if 'Period' in df.columns and any('Average P/E' in col for col in df.columns):
                pe_col = [c for c in df.columns if "vs" in str(c)]
                if pe_col: pe_val = str(pe_col[0]).split("vs")[-1].strip()
                metrics_table_html = df[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current P/E']].head(5).to_html(index=False, border=0, classes='valuation-table')
            if not df.empty and '1 Years' in str(df.iloc[:, 0].values):
                try: return_val = f"{df.iloc[0, 6]}%"
                except: pass
        return summary_text, pe_val, return_val, metrics_table_html
    except: return "Valuation metrics provide market context.", "22.85", "12.45%", ""

def get_market_data():
    raw_data = yf.download(list(SECTORS.keys()), period='5d', auto_adjust=True)['Close']
    data = raw_data.dropna(axis=1, how='any').dropna(axis=0)
    if len(data) < 2: return None, None, None
    returns = (data.iloc[-1] / data.iloc[-2] - 1) * 100
    price, change = data.iloc[-1]['^NSEI'], returns['^NSEI']
    ranked = returns.rename(index=SECTORS).sort_values(ascending=False)
    return price, change, ranked

def build_report():
    price, change, ranked = get_market_data()
    if price is None: return None, None
    summary, pe, target_return, v_table = get_valuation_and_summary()

    html = f"""
    <style>
        .market-card {{ font-family: 'Inter', -apple-system, sans-serif; max-width: 850px; margin: auto; color: #1e293b; }}
        .header-box {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 50px 25px; border-radius: 24px; text-align: center; margin-bottom: 30px; }}
        .nifty-price {{ font-size: 64px; font-weight: 800; display: block; line-height: 1; margin: 10px 0; }}
        .nifty-change {{ font-size: 24px; font-weight: 600; padding: 10px 20px; border-radius: 12px; display: inline-block; margin-top: 15px; }}
        .insight-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 30px; border-radius: 20px; color: #334155; font-size: 17px; line-height: 1.8; }}
        .stat-group {{ display: flex; gap: 40px; margin: 25px 0; padding: 20px; background: white; border-radius: 16px; border: 1px solid #e2e8f0; }}
        .stat-val {{ font-size: 26px; font-weight: 800; color: #3b82f6; }}
        .valuation-table {{ width: 100%; border-collapse: collapse; margin-top: 25px; font-size: 15px; }}
        .valuation-table th {{ background: #f1f5f9; text-align: left; padding: 14px; border-bottom: 2px solid #e2e8f0; }}
        .valuation-table td {{ padding: 14px; border-bottom: 1px solid #f1f5f9; }}
        .disclaimer-box {{ background: #fff7ed; border: 1px solid #ffedd5; padding: 20px; border-radius: 16px; font-size: 13px; color: #9a3412; margin-top: 25px; line-height: 1.6; }}
        .sector-pill {{ background: white; border: 1px solid #e2e8f0; padding: 25px; border-radius: 20px; margin-bottom: 15px; border-left: 8px solid; }}
    </style>

    <div class="market-card">
        <div class="header-box">
            <span style="color:#94a3b8; font-weight:600; letter-spacing:1.5px;">NIFTY 50 INDEX</span>
            <span class="nifty-price">{price:,.2f}</span>
            <div class="nifty-change" style="background: {'rgba(34, 197, 94, 0.15)' if change > 0 else 'rgba(239, 68, 68, 0.15)'}; color: {'#22c55e' if change > 0 else '#ef4444'};">
                {'+' if change > 0 else ''}{change:.2f}% {'▲ Bulls Leading 🚀' if change > 0 else '▼ Bears in Control 🔻'}
            </div>
        </div>

        <div class="insight-box">
            <h3 style="margin-top:0; font-size:24px; color:#1e293b;">Valuation Analysis</h3>
            <p>{summary}</p>
            <div class="stat-group">
                <div style="display:flex; flex-direction:column;"><span style="font-size:14px; color:#64748b; font-weight:600;">CURRENT P/E</span><span class="stat-val">{pe}</span></div>
                <div style="display:flex; flex-direction:column;"><span style="font-size:14px; color:#64748b; font-weight:600;">1Y MEDIAN FORECAST</span><span class="stat-val" style="color:#22c55e;">{target_return}</span></div>
            </div>
            <div style="overflow-x:auto;">{v_table}</div>
            
            <div class="disclaimer-box">
                <strong>📌 Statistical Note:</strong> The "1Y Median Forecast" is an automated projection derived from a 25-year statistical distribution of historical median returns for this valuation tier. It represents the central tendency of past data and is for analytical purposes only. <br><br>
                <strong>⚠️ Disclaimer:</strong> This is an automated update and does <u>NOT</u> constitute a buy call, financial advice, or investment recommendation. Market returns are subject to volatility and past performance is not indicative of future results. Consult a SEBI-registered advisor for all investment decisions.
            </div>
        </div>

        <h2 style="font-size:26px; font-weight:800; color:#1e293b; margin:45px 0 25px;">🚀 Leading Sectors</h2>
        {" ".join([f'''<div class="sector-pill" style="border-color: #22c55e;"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;"><span style="font-size:20px; font-weight:700;">{s}</span><span style="font-size:24px; font-weight:800; color:#16a34a;">+{v:.2f}%</span></div><div style="font-size:15px; color:#64748b;"><b>Key Constituents:</b> {", ".join(WATCHLIST.get(s, ["Major Index Components"]))}</div></div>''' for s, v in ranked.head(4).items() if s != 'NIFTY 50'])}

        <h2 style="font-size:26px; font-weight:800; color:#1e293b; margin:45px 0 25px;">🔻 Laggard Sectors</h2>
        {" ".join([f'''<div class="sector-pill" style="border-color: #ef4444;"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;"><span style="font-size:20px; font-weight:700;">{s}</span><span style="font-size:24px; font-weight:800; color:#dc2626;">{v:.2f}%</span></div><div style="font-size:15px; color:#64748b;"><b>Under Pressure:</b> {", ".join(WATCHLIST.get(s, ["Major Index Components"]))}</div></div>''' for s, v in ranked.tail(3).items() if s != 'NIFTY 50'])}
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

if __name__ == "__main__": post()
