import os, requests, base64, pandas as pd
from datetime import datetime
from nsepython import nse_get_fii_dii, nse_get_index_quote

# --- SECURE CREDENTIALS ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

def get_fii_dii():
    """Fetches FII/DII Net Cash Market flow."""
    try:
        data = nse_get_fii_dii()
        # Finding the cash market row
        for item in data:
            if item['category'] == 'FII/FPI' and 'Cash' in item['index']:
                fii_net = item['net']
            if item['category'] == 'DII' and 'Cash' in item['index']:
                dii_net = item['net']
        return fii_net, dii_net
    except:
        return "N/A", "N/A"

def build_report():
    try:
        # Fetch Live Nifty 50 Data
        nifty_data = nse_get_index_quote("NIFTY 50")
        last_price = nifty_data['lastPrice']
        p_change = nifty_data['pChange']
        
        fii, dii = get_fii_dii()
    except Exception as e:
        print(f"Skipping: Market likely closed for Republic Day. Details: {e}")
        return None, None

    # --- PROFESSIONAL DASHBOARD HTML ---
    html = f"""
    <div style="background:linear-gradient(135deg, #1a2b48 0%, #34495e 100%); color:white; padding:45px; border-radius:20px; text-align:center; font-family:sans-serif;">
        <h1 style="color:white; margin:0; font-size:26px;">Daily Closing Wrap: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="font-size:72px; font-weight:800; margin:15px 0;">{last_price}</div>
        <div style="font-size:24px; color:{'#00ffbb' if float(p_change) > 0 else '#ff6b6b'};">
            {p_change}% {'▲' if float(p_change) > 0 else '▼'}
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
        <p>Today's market sentiment was primarily driven by institutional flows and sectoral rotation. For a deeper look at valuations, visit our <strong>India Stock Market PE Ratio</strong> dashboard.</p>
    </div>
    """
    return html, p_change

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
