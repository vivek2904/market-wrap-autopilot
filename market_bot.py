import os, requests, base64, pandas as pd
from datetime import datetime

# --- SECURE CREDENTIALS ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

def get_nifty_data():
    """Fetches Nifty 50 data directly using NSE's API headers."""
    url = "https://www.nseindia.com/api/allIndices"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br"
    }
    try:
        # We start a session to handle cookies which NSE requires
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        response = session.get(url, headers=headers, timeout=10)
        data = response.json()
        
        # Find Nifty 50 in the list
        for item in data['data']:
            if item['index'] == "NIFTY 50":
                return item['last'], item['percentChange']
    except Exception as e:
        print(f"NSE Fetch Error: {e}")
        return None, None

def get_fii_dii():
    """Scrapes Institutional activity from Moneycontrol."""
    try:
        url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        df = pd.read_html(response.text)[0]
        # Net values for FII and DII
        return df.iloc[0, 3], df.iloc[0, 6] 
    except:
        return "N/A", "N/A"

def build_report():
    price, change = get_nifty_data()
    if price is None:
        print("Market data unavailable (likely due to Republic Day holiday).")
        return None, None
    
    fii, dii = get_fii_dii()

    html = f"""
    <div style="background:linear-gradient(135deg, #1a2b48 0%, #34495e 100%); color:white; padding:45px; border-radius:20px; text-align:center; font-family:sans-serif;">
        <h1 style="color:white; margin:0; font-size:26px;">Daily Closing Wrap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="font-size:72px; font-weight:800; margin:15px 0;">{price}</div>
        <div style="font-size:24px; color:{'#00ffbb' if float(change) > 0 else '#ff6b6b'};">
            {change}% {'▲' if float(change) > 0 else '▼'}
        </div>
    </div>

    <h2 style="color:#1a2b48; border-bottom:2px solid #eee; padding-bottom:10px; margin-top:40px;">Institutional Cash Flow (FII/DII)</h2>
    <div style="display:flex; gap:15px; margin:20px 0; font-family:sans-serif;">
        <div style="flex:1; border:2px solid #eee; border-radius:12px; padding:20px; text-align:center;">
            <p style="margin:0; color:#666;">FII Net Flow</p>
            <h3 style="margin:5px 0; color:{'#1e8e3e' if '-' not in str(fii) else '#d93025'};">₹ {fii} Cr</h3>
        </div>
        <div style="flex:1; border:2px solid #eee; border-radius:12px; padding:20px; text-align:center;">
            <p style="margin:0; color:#666;">DII Net Flow</p>
            <h3 style="margin:5px 0; color:{'#1e8e3e' if '-' not in str(dii) else '#d93025'};">₹ {dii} Cr</h3>
        </div>
    </div>

    <div style="background:#fef9e7; padding:25px; border-radius:12px; border-left:6px solid #f1c40f; margin:30px 0; font-family:sans-serif;">
        <h3 style="margin-top:0; color:#9a7d0a;">Human-Like Insight</h3>
        <p>Market sentiment today was primarily driven by institutional activity. For long-term valuation insights, don't forget to check our <strong>India Stock Market PE Ratio</strong> analysis.</p>
    </div>
    """
    return html, change

def run():
    content, change = build_report()
    if not content: return # Exit if holiday
    
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    payload = {
        'title': f"Market Wrap {datetime.now().strftime('%d %b')}: Nifty {'Advances' if float(change) > 0 else 'Dips'} {change}%",
        'content': content,
        'status': 'publish',
        'categories': [CATEGORY_ID]
    }
    res = requests.post(WP_URL, headers={'Authorization': f'Basic {auth}'}, json=payload)
    print("Success!" if res.status_code == 201 else f"Error: {res.text}")

if __name__ == "__main__":
    run()
