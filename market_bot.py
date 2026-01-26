import os, requests, base64, pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
from nselib import indices, capital_market

# --- SECURE CREDENTIALS ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

def get_fii_dii():
    """Fetches FII/DII Net Cash Market flow."""
    try:
        url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        tables = pd.read_html(response.text)
        df = tables[0]
        return df.iloc[0, 3], df.iloc[0, 6] # FII Net, DII Net
    except:
        return "N/A", "N/A"

def get_news_reason():
    """Fetches a market headline to explain the 'Why'."""
    try:
        rss = requests.get("https://www.moneycontrol.com/rss/marketreports.xml")
        root = ET.fromstring(rss.content)
        latest = root.find('.//item')
        return f"<strong>{latest.find('title').text}</strong>: {latest.find('description').text[:180]}..."
    except:
        return "Market sentiment was driven by institutional flows and global macro cues."

def build_report():
    try:
        # Use the updated indices module for live data
        idx_data = indices.live_index_performances()
        nifty = idx_data[idx_data['index'] == 'NIFTY 50'].iloc[0]
        
        # Sectoral winners/losers
        sorted_idx = idx_data.sort_values('pChange', ascending=False)
        winner = sorted_idx.iloc[0]
        loser = sorted_idx.iloc[-1]
        
        fii, dii = get_fii_dii()
        reason = get_news_reason()
    except Exception as e:
        print(f"Skipping: Market likely closed for Republic Day. Error: {e}")
        return None, None

    # --- PROFESSIONAL DASHBOARD HTML ---
    html = f"""
    <div style="background:linear-gradient(135deg, #1a2b48 0%, #34495e 100%); color:white; padding:45px; border-radius:20px; text-align:center; font-family:sans-serif;">
        <h1 style="color:white; margin:0; font-size:26px;">Daily Closing Wrap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="font-size:72px; font-weight:800; margin:15px 0;">{nifty['lastPrice']}</div>
        <div style="font-size:24px; color:{'#00ffbb' if float(nifty['pChange']) > 0 else '#ff6b6b'};">
            {nifty['pChange']}% {'▲' if float(nifty['pChange']) > 0 else '▼'}
        </div>
    </div>

    <h2 style="color:#1a2b48; border-bottom:2px solid #eee; padding-bottom:10px; margin-top:40px;">Institutional Flow (Net Cash)</h2>
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

    <div style="background:#fef9e7; padding:25px; border-radius:12px; border-left:6px solid #f1c40f; margin:30px 0;">
        <h3 style="margin-top:0; color:#9a7d0a;">The "Why" Behind Today's Move</h3>
        <p>{reason}</p>
    </div>

    <p style="margin-top:40px; font-size:14px; color:#888; border-top:1px solid #eee; padding-top:20px; text-align:center;">
        <em>Follow our <strong>India Stock Market PE Ratio</strong> dashboard for valuation context.</em>
    </p>
    """
    return html, nifty['pChange']

def run():
    content, change = build_report()
    if not content: return # Exit if no data (holiday)
    
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    payload = {
        'title': f"Market Wrap {datetime.now().strftime('%d %b')}: Nifty {'Advances' if float(change) > 0 else 'Retreats'} {change}%",
        'content': content,
        'status': 'publish',
        'categories': [CATEGORY_ID]
    }
    res = requests.post(WP_URL, headers={'Authorization': f'Basic {auth}'}, json=payload)
    print("Success!" if res.status_code == 201 else f"Error: {res.text}")

if __name__ == "__main__":
    run()
