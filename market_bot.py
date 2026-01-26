import os, requests, base64, pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
from nselib import capital_market

# --- SECURE CREDENTIALS ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

def get_market_intelligence():
    """Fetches real-time news to explain the move."""
    try:
        rss = requests.get("https://www.moneycontrol.com/rss/marketreports.xml")
        root = ET.fromstring(rss.content)
        latest = root.find('.//item')
        return f"<strong>{latest.find('title').text}</strong>: {latest.find('description').text[:180]}..."
    except:
        return "The market moved today based on institutional flow and sectoral rotation."

def fetch_fii_dii():
    """Scrapes End-of-Day institutional cash flow."""
    try:
        url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
        df = pd.read_html(url)[0]
        return df.iloc[0, 3], df.iloc[0, 6] # FII Net, DII Net
    except:
        return "N/A", "N/A"

def build_report():
    indices = capital_market.live_index_performances()
    nifty = indices[indices['index'] == 'NIFTY 50'].iloc[0]
    fii, dii = fetch_fii_dii()
    reason = get_market_intelligence()
    
    # Sort sectors to find biggest winner/loser
    sector_data = indices[indices['index'].str.contains('NIFTY', na=False)].sort_values('pChange', ascending=False)
    winner, loser = sector_data.iloc[0], sector_data.iloc[-1]

    html = f"""
    <div style="background:linear-gradient(135deg, #1a2b48 0%, #34495e 100%); color:white; padding:45px; border-radius:20px; text-align:center; font-family:sans-serif;">
        <h1 style="color:white; margin:0;">Daily Closing Wrap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="font-size:68px; font-weight:800; margin:15px 0;">{nifty['lastPrice']}</div>
        <div style="font-size:24px; color:{'#00ffbb' if float(nifty['pChange']) > 0 else '#ff5e5e'};">
            {nifty['pChange']}% {'▲' if float(nifty['pChange']) > 0 else '▼'}
        </div>
    </div>

    <h2 style="margin-top:40px; color:#1a2b48; border-bottom:2px solid #eee; padding-bottom:10px;">Institutional Cash Flow</h2>
    <div style="display:flex; gap:15px; margin-top:15px; font-family:sans-serif;">
        <div style="flex:1; border:1px solid #ddd; border-radius:10px; padding:15px; text-align:center;">
            <p style="margin:0; color:#666;">FII Net</p>
            <h3 style="margin:5px 0; color:{'#1e8e3e' if '-' not in str(fii) else '#d93025'};">₹ {fii} Cr</h3>
        </div>
        <div style="flex:1; border:1px solid #ddd; border-radius:10px; padding:15px; text-align:center;">
            <p style="margin:0; color:#666;">DII Net</p>
            <h3 style="margin:5px 0; color:{'#1e8e3e' if '-' not in str(dii) else '#d93025'};">₹ {dii} Cr</h3>
        </div>
    </div>

    <div style="display: flex; gap: 20px; margin-top:30px; font-family:sans-serif;">
        <div style="flex:1; background:#ebf9f1; padding:20px; border-radius:15px; border:1px solid #c3e6cb;">
            <h3 style="color:#1e8e3e; margin-top:0;">🚀 Top Gainer: {winner['index']}</h3>
            <p>Today's gain was fueled by strong sectoral demand and bullish quarterly outlooks.</p>
        </div>
        <div style="flex:1; background:#fdf2f2; padding:20px; border-radius:15px; border:1px solid #f5c6cb;">
            <h3 style="color:#d93025; margin-top:0;">🔻 Top Loser: {loser['index']}</h3>
            <p>This sector faced pressure due to profit booking and cautious global macroeconomic cues.</p>
        </div>
    </div>

    <div style="background:#fef9e7; padding:25px; border-radius:12px; border-left:6px solid #f1c40f; margin:30px 0;">
        <h3 style="margin-top:0; color:#9a7d0a;">The "Why" Behind Today's Move</h3>
        <p>{reason}</p>
    </div>
    """
    return html, nifty['pChange']

def run():
    content, change = build_report()
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    payload = {
        'title': f"Market Wrap {datetime.now().strftime('%d %b')}: Nifty {'Advances' if float(change) > 0 else 'Dips'} {change}%",
        'content': content, 'status': 'publish', 'categories': [CATEGORY_ID]
    }
    requests.post(WP_URL, headers={'Authorization': f'Basic {auth}'}, json=payload)

if __name__ == "__main__":
    run()
