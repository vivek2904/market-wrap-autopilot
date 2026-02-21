import os
import requests
import base64
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime
from bs4 import BeautifulSoup
import io
import re

# ==============================
# WORDPRESS CONFIG
# ==============================
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')   # Example: https://yoursite.com/wp-json/wp/v2/posts
CATEGORY_ID = 12

if not WP_URL:
    raise Exception("WP_URL not set")

SITE_URL = WP_URL.split("/wp-json")[0]

# ==============================
# SECTOR STOCK MAP (170+ Stocks)
# ==============================
SECTOR_MAP = {
    'Nifty Bank': ['HDFCBANK','ICICIBANK','SBIN','AXISBANK','KOTAKBANK','INDUSINDBK','BANKBARODA','PNB','IDFCFIRSTB','FEDERALBNK'],
    'IT Services': ['TCS','INFY','HCLTECH','WIPRO','TECHM','LTIM','PERSISTENT','COFORGE','MPHASIS','KPITTECH'],
    'Automobile': ['M&M','MARUTI','TATAMOTORS','BAJAJ-AUTO','EICHERMOT','TVSMOTOR','HEROMOTOCO','ASHOKLEY','MRF','BALKRISIND'],
    'FMCG': ['HINDUNILVR','ITC','NESTLEIND','BRITANNIA','GODREJCP','DABUR','MARICO','VBL','COLPAL','TATACONSUM'],
    'Metals': ['TATASTEEL','JSWSTEEL','HINDALCO','JINDALSTEL','VEDL','NMDC','SAIL','NATIONALUM','APLAPOLLO','RATNAMANI'],
    'Pharma': ['SUNPHARMA','CIPLA','DRREDDY','LUPIN','AUROPHARMA','ZYDUSLIFE','DIVISLAB','ALKEM','TORNTPHARM','ABBOTT'],
    'Energy': ['RELIANCE','NTPC','ONGC','POWERGRID','BPCL','ADANIGREEN','TATAPOWER','IOC','GAIL','ADANIENSOL'],
    'Financial Services': ['BAJFINANCE','HDFCBANK','ICICIBANK','BAJAJFINSV','CHOLAFIN','REC','PFC','SHRIRAMFIN','SBILIFE','HDFCLIFE'],
    'PSU Bank': ['SBIN','BANKBARODA','CANBK','UNIONBANK','IOB','PNB','INDIANB','BANKINDIA','UCOBANK','CENTRALBK'],
    'Realty': ['DLF','LODHA','GODREJPROP','OBEROIRLTY','PRESTIGE','PHOENIXLTD','BRIGADE','SOBHA','SIGNATURE','SUNTECK'],
    'Media': ['ZEEL','SUNTV','PVRINOX','NETWORK18','TV18BRDCST','NAZARA','DISHTV','HATHWAY','SAREGMAPA','TIPSINDLTD'],
    'Consumption': ['ITC','HINDUNILVR','TITAN','ASIANPAINT','NESTLEIND','TRENT','DMART','ZOMATO','BRITANNIA','PAGEIND'],
    'Infrastructure': ['RELIANCE','LT','BHARTIARTL','NTPC','ADANIPORTS','ULTRACEMCO','ONGC','GRASIM','IIFL','POWERGRID'],
    'PSE': ['NTPC','ONGC','POWERGRID','COALINDIA','BEL','HAL','BPCL','IOC','PFC','REC'],
    'CPSE': ['NTPC','ONGC','POWERGRID','COALINDIA','BEL','NHPC','SJVN','NBCC','OIL','COCHINSHIP'],
    'Commodities': ['RELIANCE','TATASTEEL','JSWSTEEL','HINDALCO','NTPC','ONGC','AMBUJACEM','GRASIM','VEDL','COALINDIA'],
    'Services': ['LT','ADANIPORTS','APOLLOHOSP','HDFCLIFE','SBILIFE','TRENT','INDIGO','VBL','TATACOMM','GMRINFRA']
}

# ==============================
# INDEX TICKERS
# ==============================
INDEX_TICKERS = {
    '^NSEI': 'NIFTY 50',
    '^NSEBANK': 'Nifty Bank',
    '^CNXIT': 'IT Services',
    '^CNXAUTO': 'Automobile',
    '^CNXFMCG': 'FMCG',
    '^CNXMETAL': 'Metals',
    '^CNXPHARMA': 'Pharma',
    '^CNXENERGY': 'Energy',
    '^CNXREALTY': 'Realty',
    '^CNXINFRA': 'Infrastructure',
    '^CNXFIN': 'Financial Services',
    '^CNXPSUBANK': 'PSU Bank',
    '^CNXMEDIA': 'Media',
    '^CNXCONSUMP': 'Consumption',
    '^CNXPSE': 'PSE',
    '^CNXCPSE': 'CPSE',
    '^CNXCOMMOD': 'Commodities',
    '^CNXSERVICE': 'Services'
}

# ==============================
# LINKS
# ==============================
def get_links(ticker):
    return (
        f"https://www.google.com/finance/quote/{ticker}:NSE",
        f"{SITE_URL}/?s={ticker}"
    )

# ==============================
# SCRAPE VALUATION DATA
# ==============================
def get_valuation_data():
    try:
        url = "https://worldperatio.com/area/india/"
        res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        tables = pd.read_html(io.StringIO(res.text))

        pe = "N/A"
        forecast = "N/A"
        table_html = ""

        for df in tables:
            cols = [str(c) for c in df.columns]

            for c in cols:
                if "vs Current" in c:
                    pe = re.sub(r"[^\d\.]", "", c.split("vs")[-1])

            if 'Period' in cols and 'Average P/E (μ)' in cols:
                table_html = df.head(5).to_html(index=False, border=0)

            if "1 Years" in str(df.values):
                forecast = re.sub(r"[^\d\.\-]", "", str(df.iloc[0,6])) + "%"

        return pe, forecast, table_html

    except:
        return "N/A", "N/A", ""

# ==============================
# FETCH STOCK DATA
# ==============================
def fetch_stock_data():
    tickers = list(set([f"{t}.NS" for sub in SECTOR_MAP.values() for t in sub]))
    data = yf.download(tickers, period="3mo", interval="1d", auto_adjust=True, progress=False)

    results = {}

    for t in tickers:
        try:
            prices = data['Close'][t].dropna()
            if len(prices) < 25:
                continue

            curr = prices.iloc[-1]
            prev = prices.iloc[-2]
            change = ((curr/prev)-1)*100
            sma20 = prices.rolling(20).mean().iloc[-1]
            rsi = ta.rsi(prices, length=14).iloc[-1]

            results[t.replace(".NS","")] = {
                "price": round(curr,2),
                "change": round(change,2),
                "rsi": round(rsi,2),
                "trend": "Bullish" if curr > sma20 else "Bearish"
            }

        except:
            continue

    return results

# ==============================
# BUILD HTML REPORT
# ==============================
def build_report():
    idx = yf.download(list(INDEX_TICKERS.keys()), period="5d")['Close'].dropna(axis=1)
    returns = ((idx.iloc[-1]/idx.iloc[-2])-1)*100

    nifty_price = idx.iloc[-1].get('^NSEI',0)
    nifty_change = returns.get('^NSEI',0)

    pe, forecast, val_table = get_valuation_data()
    stock_data = fetch_stock_data()

    performance_map = {INDEX_TICKERS[k]: v for k,v in returns.items()}
    sorted_sectors = sorted(performance_map.items(), key=lambda x: x[1], reverse=True)

    today = datetime.now().strftime("%d %B %Y")

    html = f"""
    <style>
    body {{font-family:Inter,system-ui;background:#f5f7fb;}}
    .hero {{
        background:linear-gradient(135deg,#0f172a,#1e293b);
        color:white;padding:60px;border-radius:18px;
        text-align:center;margin-bottom:40px;
    }}
    .hero h1 {{font-size:14px;letter-spacing:2px;opacity:.7;}}
    .hero .price {{font-size:60px;font-weight:800;}}
    .up {{color:#22c55e;font-weight:600;}}
    .down {{color:#ef4444;font-weight:600;}}
    .valuation-box {{background:white;padding:30px;border-radius:16px;margin-bottom:40px;}}
    .sector {{margin-bottom:50px;}}
    .sector-header {{display:flex;justify-content:space-between;border-bottom:1px solid #e5e7eb;margin-bottom:20px;}}
    .stock-grid {{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;}}
    .stock-card {{background:white;padding:18px;border-radius:14px;box-shadow:0 4px 15px rgba(0,0,0,.05);}}
    .tag {{font-size:10px;padding:4px 6px;border-radius:6px;}}
    .overbought {{background:#fee2e2;color:#b91c1c;}}
    .oversold {{background:#dcfce7;color:#166534;}}
    </style>

    <div class="hero">
        <h1>DAILY NIFTY 50 INSIGHTS</h1>
        <div class="price">{nifty_price:,.2f}</div>
        <div class="{'up' if nifty_change>0 else 'down'}">
            {'▲' if nifty_change>0 else '▼'} {nifty_change:+.2f}%
        </div>
    </div>

    <div class="valuation-box">
        <h2>📊 Valuation Analysis & Forecast</h2>
        <p><b>Current P/E:</b> {pe}</p>
        <p><b>1Y Forecast:</b> {forecast}</p>
        {val_table}
    </div>
    """

    for sector, s_return in sorted_sectors:
        if sector not in SECTOR_MAP:
            continue

        html += f"""
        <div class="sector">
            <div class="sector-header">
                <h2>{sector}</h2>
                <span class="{'up' if s_return>0 else 'down'}">{s_return:+.2f}%</span>
            </div>
            <div class="stock-grid">
        """

        for t in SECTOR_MAP[sector]:
            s = stock_data.get(t)
            if not s:
                continue

            ext, internal = get_links(t)

            tag = ""
            if s["rsi"] > 70:
                tag = "<span class='tag overbought'>Overbought</span>"
            elif s["rsi"] < 30:
                tag = "<span class='tag oversold'>Oversold</span>"

            html += f"""
            <div class="stock-card">
                <a href="{internal}"><b>{t}</b></a><br>
                <a href="{ext}" target="_blank">₹{s['price']:,.2f}</a><br>
                <span class="{'up' if s['change']>0 else 'down'}">{s['change']:+.2f}%</span><br>
                {tag}
            </div>
            """

        html += "</div></div>"

    return html, nifty_change

# ==============================
# POST TO WORDPRESS
# ==============================
def post():
    content, change = build_report()

    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}','Content-Type':'application/json'}

    title = f"NSE Market Wrap: Nifty {change:+.2f}% | Sector Leaders & 170+ Stock Insights"
    seo_desc = f"Nifty closes {change:+.2f}%. Full sector analysis, RSI scan and valuation insights for 170+ NSE stocks."

    payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [CATEGORY_ID],
        "aioseo_title": title,
        "aioseo_description": seo_desc
    }

    res = requests.post(WP_URL, headers=headers, json=payload)
    print("Posted Successfully" if res.status_code==201 else res.text)

if __name__ == "__main__":
    post()
