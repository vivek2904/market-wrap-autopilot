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

# =========================
# CONFIG
# =========================
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')  # Must be full endpoint: https://yoursite.com/wp-json/wp/v2/posts
CATEGORY_ID = 12

if not WP_URL:
    raise Exception("WP_URL not set in environment variables")

# =========================
# SECTOR MAP (170+ STOCKS)
# =========================
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

# =========================
# NSE INDEX MAPPING
# =========================
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

# =========================
# LINK BUILDER
# =========================
def get_links(ticker):
    clean = ticker.upper()
    internal = f"{WP_URL.split('/wp-json')[0]}/?s={clean}"
    external = f"https://www.google.com/finance/quote/{clean}:NSE"
    return external, internal

# =========================
# SCRAPE LIVE P/E DATA
# =========================
def get_valuation_data():
    try:
        url = "https://worldperatio.com/area/india/"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

        tables = pd.read_html(io.StringIO(res.text))

        pe = "N/A"
        forecast = "N/A"
        table_html = ""

        for df in tables:
            cols = [str(c) for c in df.columns]

            # Extract Current PE
            for c in cols:
                if "vs Current" in c:
                    pe = re.sub(r"[^\d\.]", "", c.split("vs")[-1])

            # Extract Forecast
            if "1 Years" in str(df.values):
                try:
                    forecast = str(df.iloc[0, 6]) + "%"
                except:
                    pass

            # Extract Historical Table
            if 'Period' in cols and 'Average P/E (μ)' in cols:
                clean_df = df[['Period','Average P/E (μ)','vs Current P/E']].head(5)
                table_html = clean_df.to_html(index=False, border=0, classes='valuation-table')

        return pe, forecast, table_html

    except:
        return "N/A", "N/A", ""

# =========================
# FETCH STOCK DATA (Batch Optimized)
# =========================
def fetch_stock_data():
    unique = list(set([f"{t}.NS" for sub in SECTOR_MAP.values() for t in sub]))
    data = yf.download(unique, period="3mo", interval="1d", auto_adjust=True, progress=False)

    results = {}

    for ticker in unique:
        try:
            prices = data['Close'][ticker].dropna()
            if len(prices) < 25:
                continue

            curr = prices.iloc[-1]
            prev = prices.iloc[-2]

            sma20 = prices.rolling(20).mean().iloc[-1]
            rsi = ta.rsi(prices, length=14).iloc[-1]

            change = ((curr / prev) - 1) * 100

            results[ticker.replace(".NS","")] = {
                "price": round(curr,2),
                "change": round(change,2),
                "rsi": round(rsi,2),
                "trend": "Bullish" if curr > sma20 else "Bearish"
            }

        except:
            continue

    return results

# =========================
# BUILD HTML REPORT
# =========================
def build_report():

    # Index Data
    idx = yf.download(list(INDEX_TICKERS.keys()), period="5d")['Close'].dropna(axis=1)
    returns = ((idx.iloc[-1]/idx.iloc[-2])-1)*100
    returns = returns.dropna()

    nifty_price = idx.iloc[-1].get('^NSEI',0)
    nifty_change = returns.get('^NSEI',0)

    stock_data = fetch_stock_data()
    pe, forecast, val_table = get_valuation_data()

    performance_map = {INDEX_TICKERS[k]: v for k,v in returns.items() if k in INDEX_TICKERS}
    sorted_sectors = sorted(performance_map.items(), key=lambda x: x[1], reverse=True)

    today = datetime.now().strftime("%d %B %Y")

    html = f"""
    <style>
    .stock-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; }}
    .stock-card {{ border:1px solid #e5e7eb; padding:12px; border-radius:10px; }}
    .green {{ color:#16a34a; font-weight:700; }}
    .red {{ color:#dc2626; font-weight:700; }}
    .tag {{ font-size:10px; padding:2px 5px; border-radius:4px; font-weight:bold; }}
    </style>

    <h1>NSE Market Wrap – {today}</h1>

    <h2>NIFTY 50: {nifty_price:,.2f}
    <span class="{'green' if nifty_change>0 else 'red'}">
    {'▲' if nifty_change>0 else '▼'} {nifty_change:+.2f}%
    </span></h2>

    <h3>Market Valuation</h3>
    <p><b>Current P/E:</b> {pe}</p>
    <p><b>1Y Forecast:</b> {forecast}</p>
    {val_table}
    """

    for sector, s_return in sorted_sectors:
        if sector not in SECTOR_MAP:
            continue

        html += f"<h2>{sector} <span class='{'green' if s_return>0 else 'red'}'>{s_return:+.2f}%</span></h2>"
        html += "<div class='stock-grid'>"

        for t in SECTOR_MAP[sector]:
            s = stock_data.get(t)
            if not s:
                continue

            ext, internal = get_links(t)

            tag = ""
            if s["rsi"] > 70:
                tag = "<span class='tag' style='background:#fee2e2;color:#ef4444;'>Overbought</span>"
            elif s["rsi"] < 30:
                tag = "<span class='tag' style='background:#dcfce7;color:#16a34a;'>Oversold</span>"

            html += f"""
            <div class="stock-card">
                <b><a href="{internal}">{t}</a></b><br>
                <a href="{ext}" target="_blank">₹{s['price']:,.2f}</a><br>
                <span class="{'green' if s['change']>0 else 'red'}">{s['change']:+.2f}%</span><br>
                {tag}
            </div>
            """

        html += "</div>"

    return html, nifty_change

# =========================
# POST TO WORDPRESS
# =========================
def post():
    content, change = build_report()

    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

    title = f"India Market Wrap: Nifty {change:+.2f}% | Sector Leaders & 170+ Stock Analysis"
    seo_desc = f"Nifty ends {change:+.2f}%. Explore RSI, trend and sector rotation for 170+ NSE stocks with live valuation insights."

    payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [CATEGORY_ID],
        "aioseo_title": title,
        "aioseo_description": seo_desc
    }

    res = requests.post(WP_URL, headers=headers, json=payload)
    print("✅ Posted Successfully" if res.status_code==201 else f"❌ Error: {res.text}")

if __name__ == "__main__":
    post()
