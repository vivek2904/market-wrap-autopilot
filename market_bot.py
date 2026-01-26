import os, requests, base64, pandas as pd
from datetime import datetime

# --- SECURE CREDENTIALS (Pulls from your GitHub Secrets) ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

def get_test_data():
    """Generates mock data because the market is closed today."""
    price = "24,560.45"
    change = "+0.85"
    fii = "+1,240.50"
    dii = "-450.20"
    reason = "Strong domestic sentiment and positive global cues ahead of the budget."
    return price, change, fii, dii, reason

def build_html():
    price, change, fii, dii, reason = get_test_data()
    
    html = f"""
    <div style="background:linear-gradient(135deg, #1a2b48 0%, #34495e 100%); color:white; padding:45px; border-radius:20px; text-align:center; font-family:sans-serif;">
        <h1 style="color:white; margin:0; font-size:26px;">Market Connection Test: {datetime.now().strftime('%d %b %Y')}</h1>
        <div style="font-size:68px; font-weight:800; margin:15px 0;">{price}</div>
        <div style="font-size:24px; color:#00ffbb;">{change}% ▲</div>
    </div>

    <h2 style="color:#1a2b48; border-bottom:2px solid #eee; padding-bottom:10px; margin-top:40px;">Institutional Cash Flow (Simulated)</h2>
    <div style="display:flex; gap:15px; margin:20px 0; font-family:sans-serif;">
        <div style="flex:1; border:2px solid #eee; border-radius:12px; padding:20px; text-align:center;">
            <p style="margin:0; color:#666;">FII Net Flow</p>
            <h3 style="color:#1e8e3e;">₹ {fii} Cr</h3>
        </div>
        <div style="flex:1; border:2px solid #eee; border-radius:12px; padding:20px; text-align:center;">
            <p style="margin:0; color:#666;">DII Net Flow</p>
            <h3 style="color:#d93025;">₹ {dii} Cr</h3>
        </div>
    </div>

    <div style="background:#fef9e7; padding:25px; border-radius:12px; border-left:6px solid #f1c40f; margin:30px 0; font-family:sans-serif;">
        <h3 style="margin-top:0; color:#9a7d0a;">Why this post appeared?</h3>
        <p>This is a <strong>successful connection test</strong>. Your GitHub Bot is now talking to longniftyshort.com. Real market data will start flowing tomorrow at 5:30 PM IST.</p>
    </div>
    """
    return html, change

def run():
    print("Starting Force-Post Test...")
    content, change = build_html()
    
    # Create the secure Authorization header
    auth_string = f"{WP_USER}:{WP_PASS}"
    token = base64.b64encode(auth_string.encode()).decode('utf-8')
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'title': f"Connection Verified: Market Bot is Live ({datetime.now().strftime('%d %b')})",
        'content': content,
        'status': 'publish',
        'categories': [CATEGORY_ID]
    }
    
    response = requests.post(WP_URL, headers=headers, json=payload)
    
    if response.status_code == 201:
        print("✅ SUCCESS! Check your WordPress 'All Posts' section.")
    else:
        print(f"❌ FAILED! Error code: {response.status_code}")
        print(f"Message: {response.text}")

if __name__ == "__main__":
    run()
