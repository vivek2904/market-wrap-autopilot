import os
import re
import requests
import base64
import io
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime
from bs4 import BeautifulSoup

#############################################
## MODULE 1: CONFIGURATION & US WATCHLIST
#############################################

WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# Main US Indices
MAIN_INDICES = {
    'S&P 500': '^GSPC',
    'Nasdaq 100': '^NDX',
    'Dow Jones': '^DJI',
    'CBOE VIX': '^VIX'
}

# Sector ETFs
SECTOR_INDICES = {
    'Technology': 'XLK',
    'Health Care': 'XLV',
    'Financials': 'XLF',
    'Cons. Discretionary': 'XLY',
    'Communication': 'XLC',
    'Industrials': 'XLI',
    'Cons. Staples': 'XLP',
    'Energy': 'XLE',
    'Materials': 'XLB',
    'Real Estate': 'XLRE',
    'Utilities': 'XLU'
}

# Complete US Sector Watchlist (Preserved)
WATCHLIST = {
    'Technology': ['Apple (AAPL)', 'Microsoft (MSFT)', 'Nvidia (NVDA)', 'Broadcom (AVGO)', 'Oracle (ORCL)', 'Adobe (ADBE)', 'Cisco (CSCO)', 'Salesforce (CRM)', 'AMD (AMD)', 'Qualcomm (QCOM)'],
    'Financials': ['JPMorgan Chase (JPM)', 'Visa (V)', 'Mastercard (MA)', 'Bank of America (BAC)', 'Goldman Sachs (GS)', 'Morgan Stanley (MS)', 'Wells Fargo (WFC)', 'BlackRock (BLK)', 'American Express (AXP)', 'Citigroup (C)'],
    'Energy': ['Exxon Mobil (XOM)', 'Chevron (CVX)', 'ConocoPhillips (COP)', 'Schlumberger (SLB)', 'EOG Resources (EOG)', 'Marathon Petroleum (MPC)', 'Phillips 66 (PSX)', 'Valero Energy (VLO)', 'Williams Companies (WMB)', 'Hess (HES)'],
    'Health Care': ['UnitedHealth (UNH)', 'Eli Lilly (LLY)', 'Johnson & Johnson (JNJ)', 'AbbVie (ABBV)', 'Merck (MRK)', 'Pfizer (PFE)', 'Amgen (AMGN)', 'Intuitive Surgical (ISRG)', 'Thermo Fisher (TMO)', 'Gilead Sciences (GILD)'],
    'Cons. Discretionary': ['Amazon (AMZN)', 'Tesla (TSLA)', 'Home Depot (HD)', 'McDonald\'s (MCD)', 'Nike (NKE)', "Lowe's (LOW)", 'Starbucks (SBUX)', 'Booking Holdings (BKNG)', 'TJX Companies (TJX)', 'Norwegian Cruise (NCLH)'],
    'Communication': ['Alphabet (GOOGL)', 'Meta (META)', 'Netflix (NFLX)', 'Disney (DIS)', 'T-Mobile (TMUS)', 'Verizon (VZ)', 'AT&T (T)', 'Comcast (CMCSA)', 'Charter (CHTR)', 'Snap (SNAP)'],
    'Industrials': ['Caterpillar (CAT)', 'Honeywell (HON)', 'GE Aerospace (GE)', 'Union Pacific (UNP)', 'UPS (UPS)', 'Boeing (BA)', 'Lockheed Martin (LMT)', 'RTX Corp (RTX)', 'John Deere (DE)', '3M (MMM)'],
    'Cons. Staples': ['Procter & Gamble (PG)', 'Coca-Cola (KO)', 'PepsiCo (PEP)', 'Costco (COST)', 'Walmart (WMT)', 'Philip Morris (PM)', 'Estee Lauder (EL)', 'Altria (MO)', 'Mondelez (MDLZ)', 'Colgate-Palmolive (CL)'],
    'Materials': ['Linde (LIN)', 'Air Products (APD)', 'Freeport-McMoRan (FCX)', 'Sherwin-Williams (SHW)', 'Newmont (NEM)', 'Corteva (CTVA)', 'Ecolab (ECL)', 'Vulcan Materials (VMC)', 'Dow (DOW)', 'Nucor (NUE)'],
    'Real Estate': ['Prologis (PLD)', 'American Tower (AMT)', 'Equinix (EQIX)', 'Crown Castle (CCI)', 'Public Storage (PSA)', 'Digital Realty (DLR)', 'Realty Income (O)', 'VICI Properties (VICI)', 'SBA Communications (SBAC)', 'Welltower (WELL)'],
    'Utilities': ['NextEra Energy (NEE)', 'Southern Co (SO)', 'Duke Energy (DUK)', 'American Electric (AEP)', 'Sempra (SRE)', 'Dominion Energy (D)', 'Exelon (EXC)', 'PG&E (PCG)', 'Xcel Energy (XEL)', 'Consolidated Edison (ED)']
}

def get_ticker(s):
    match = re.search(r'\((.*?)\)', s)
    return match.group(1) if match else s

def get_name(s):
    return s.split('(')[0].strip()

ALL_TICKERS = list(set([get_ticker(s) for sublist in WATCHLIST.values() for s in sublist]))

#############################################
## MODULE 2: DATA EXTRACTION ENGINE
#############################################

class MarketDataEngine:
    @staticmethod
    def format_vol(n):
        """Formats numbers into US Million/Billion notation."""
        if pd.isna(n) or n is None or n == 0: return "-"
        if n >= 1e9: return f"{n/1e9:.2f}B"
        if n >= 1e6: return f"{n/1e6:.1f}M"
        if n >= 1e3: return f"{n/1e3:.0f}K"
        return f"{int(n):,}"

    @staticmethod
    def get_valuation():
        """Fetches US Valuation Data."""
        url = "https://worldperatio.com/area/united-states/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        data = {'pe': '26.9', 'status': 'Fair', 'avg_1y': '25.4', 'avg_5y': '24.1', 'avg_10y': '21.8'}
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                text = soup.get_text()
                
                pe_match = re.search(r'P/E Ratio:\s*([\d\.]+)', text)
                if pe_match: data['pe'] = pe_match.group(1)
                
                status_match = re.search(r'considered\s+([A-Za-z]+)', text, re.I)
                if status_match: data['status'] = status_match.group(1).capitalize()
                
                y1 = re.search(r'1Y Average:\s*([\d\.]+)', text)
                if y1: data['avg_1y'] = y1.group(1)
                y5 = re.search(r'Last 5Y.*?([\d\.]+)', text, re.DOTALL)
                if y5: data['avg_5y'] = y5.group(1)
                y10 = re.search(r'Last 10Y.*?([\d\.]+)', text, re.DOTALL)
                if y10: data['avg_10y'] = y10.group(1)
        except Exception as e:
            print(f"Valuation notice: {e}")
        return data

    @staticmethod
    def fetch_market_overview():
        # 1. Main Benchmarks
        bench_data = []
        for name, ticker in MAIN_INDICES.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="5d")
                if len(hist) >= 2:
                    curr = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = curr - prev
                    pct = (change / prev) * 100
                    bench_data.append({
                        'name': name,
                        'price': f"{curr:,.2f}",
                        'change': change,
                        'pct_change': pct
                    })
            except Exception: continue

        # 2. Sector Returns
        sector_data = []
        for name, ticker in SECTOR_INDICES.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="5d")
                if len(hist) >= 2:
                    curr = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    pct = ((curr - prev) / prev) * 100
                    sector_data.append({'name': name, 'pct_change': pct})
            except Exception: continue

        # Sort sectors by highest performance
        sector_data = sorted(sector_data, key=lambda x: x['pct_change'], reverse=True)

        # 3. Stock Watchlist Stats
        stock_raw = yf.download(ALL_TICKERS, period="30d", interval="1d", auto_adjust=True, threads=True)
        stock_stats = {}
        for cat, items in WATCHLIST.items():
            stock_stats[cat] = []
            for item in items:
                t = get_ticker(item)
                c_name = get_name(item)
                try:
                    if isinstance(stock_raw.columns, pd.MultiIndex):
                        subset = stock_raw.iloc[:, stock_raw.columns.get_level_values(1) == t]
                        subset.columns = subset.columns.get_level_values(0)
                    else:
                        subset = stock_raw

                    prices = subset['Close'].dropna()
                    vol = subset['Volume'].dropna()
                    if len(prices) < 15: continue

                    curr_p = prices.iloc[-1]
                    prev_p = prices.iloc[-2]
                    chg = curr_p - prev_p
                    pct_chg = (chg / prev_p) * 100

                    curr_v = vol.iloc[-1]
                    avg_v = vol.iloc[-21:-1].mean()
                    is_spike = curr_v > (avg_v * 1.5) if avg_v > 0 else False

                    stock_stats[cat].append({
                        'name': c_name,
                        'ticker': t,
                        'price': curr_p,
                        'change': chg,
                        'pct_change': pct_chg,
                        'volume': curr_v,
                        'vol_spike': is_spike
                    })
                except Exception: continue

        return bench_data, sector_data, stock_stats

#############################################
## MODULE 3: PRECISE UI BUILDER (MATCHING REFERENCE)
#############################################

class UIBuilder:
    @staticmethod
    def generate_html(benchmarks, sectors, watchlist, val_data):
        today_str = datetime.today().strftime('%d %B %Y')
        
        # Valuation badge styling
        status_lower = val_data['status'].lower()
        val_badge_cls = 'badge-green' if 'cheap' in status_lower or 'undervalued' in status_lower else ('badge-red' if 'expensive' in status_lower or 'overvalued' in status_lower else 'badge-blue')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wall Street Wrap</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background-color: #f8fafc;
        color: #0f172a;
        line-height: 1.5;
        padding: 24px 12px;
        font-variant-numeric: tabular-nums;
    }}
    .container {{ max-width: 1100px; margin: 0 auto; }}

    /* HEADER BANNER */
    .header {{
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }}
    .header-title h1 {{ font-size: 26px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff; }}
    .header-title p {{ color: #94a3b8; font-size: 14px; margin-top: 4px; font-weight: 500; }}
    .header-date {{
        background: rgba(255,255,255,0.1);
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.3px;
        border: 1px solid rgba(255,255,255,0.15);
    }}

    /* CARDS */
    .card {{
        background: #ffffff;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .section-title {{
        font-size: 18px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 10px;
    }}

    /* BENCHMARKS GRID */
    .indices-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
    }}
    .index-card {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .index-name {{ font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }}
    .index-price {{ font-size: 24px; font-weight: 800; color: #0f172a; margin: 8px 0 4px 0; }}
    .change-indicator {{ font-size: 13px; font-weight: 700; display: inline-flex; align-items: center; gap: 4px; }}

    /* COLOR UTILITIES */
    .text-green {{ color: #16a34a; }}
    .text-red {{ color: #dc2626; }}
    .bg-green {{ background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }}
    .bg-red {{ background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }}

    /* VALUATION BAR */
    .valuation-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        background: #f1f5f9;
        padding: 18px;
        border-radius: 12px;
    }}
    .val-item {{ display: flex; flex-direction: column; }}
    .val-label {{ font-size: 12px; color: #64748b; font-weight: 600; margin-bottom: 4px; }}
    .val-val {{ font-size: 18px; font-weight: 700; color: #0f172a; }}

    /* SECTOR PILLS */
    .sector-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
    }}
    .sector-pill {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 12px 16px;
        border-radius: 10px;
    }}
    .sector-name {{ font-size: 14px; font-weight: 600; color: #334155; }}

    /* TABLES & ALIGNMENT */
    .table-container {{ width: 100%; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 8px; }}
    th {{
        background-color: #f8fafc;
        color: #475569;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 16px;
        border-bottom: 2px solid #e2e8f0;
    }}
    td {{
        padding: 14px 16px;
        border-bottom: 1px solid #f1f5f9;
        font-size: 14px;
        color: #1e293b;
        vertical-align: middle;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background-color: #f8fafc; }}

    .text-left {{ text-align: left; }}
    .text-right {{ text-align: right; }}

    /* BADGES */
    .badge {{
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }}
    .badge-vol {{ background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; margin-left: 8px; }}
    .badge-green {{ background-color: #dcfce7; color: #15803d; }}
    .badge-red {{ background-color: #fee2e2; color: #b91c1c; }}
    .badge-blue {{ background-color: #dbeafe; color: #1e40af; }}

    .symbol-cell {{ display: flex; align-items: center; font-weight: 700; color: #0f172a; }}
    .sub-symbol {{ font-size: 11px; color: #94a3b8; font-weight: 500; margin-left: 6px; }}
</style>
</head>
<body>

<div class="container">

    <!-- HEADER -->
    <div class="header">
        <div class="header-title">
            <h1>Wall Street Market Wrap</h1>
            <p>US Equity Market Intelligence & Sector Performance</p>
        </div>
        <div class="header-date">{today_str}</div>
    </div>

    <!-- MAIN BENCHMARKS -->
    <div class="card">
        <div class="section-title">Key US Benchmark Indices</div>
        <div class="indices-grid">
"""
        for b in benchmarks:
            is_pos = b['pct_change'] >= 0
            color_cls = "text-green" if is_pos else "text-red"
            arrow = "▲" if is_pos else "▼"
            sign = "+" if is_pos else ""
            
            html += f"""
            <div class="index-card">
                <div class="index-name">{b['name']}</div>
                <div class="index-price">{b['price']}</div>
                <div class="change-indicator {color_cls}">
                    {arrow} {sign}{b['change']:,.2f} ({sign}{b['pct_change']:.2f}%)
                </div>
            </div>
"""

        html += f"""
        </div>
    </div>

    <!-- US VALUATION METRICS -->
    <div class="card">
        <div class="section-title">
            US Market Valuation (S&P 500 P/E Analysis)
            <span class="badge {val_badge_cls}">{val_data['status']}</span>
        </div>
        <div class="valuation-grid">
            <div class="val-item">
                <span class="val-label">Current P/E Ratio</span>
                <span class="val-val">{val_data['pe']}</span>
            </div>
            <div class="val-item">
                <span class="val-label">1-Year Avg P/E</span>
                <span class="val-val">{val_data['avg_1y']}</span>
            </div>
            <div class="val-item">
                <span class="val-label">5-Year Avg P/E</span>
                <span class="val-val">{val_data['avg_5y']}</span>
            </div>
            <div class="val-item">
                <span class="val-label">10-Year Avg P/E</span>
                <span class="val-val">{val_data['avg_10y']}</span>
            </div>
        </div>
    </div>

    <!-- SECTOR PERFORMANCE PILLS -->
    <div class="card">
        <div class="section-title">Sector ETF Performance</div>
        <div class="sector-grid">
"""
        for sec in sectors:
            is_pos = sec['pct_change'] >= 0
            pill_cls = "bg-green" if is_pos else "bg-red"
            sign = "+" if is_pos else ""
            html += f"""
            <div class="sector-pill {pill_cls}">
                <span class="sector-name">{sec['name']}</span>
                <span style="font-weight:700;">{sign}{sec['pct_change']:.2f}%</span>
            </div>
"""

        html += f"""
        </div>
    </div>

    <!-- CATEGORIZED US WATCHLIST TABLES -->
    <div class="card">
        <div class="section-title">Sector Watchlist & Institutional Volume Insights</div>
"""

        for cat, stocks in watchlist.items():
            if not stocks: continue
            html += f"""
        <h3 style="font-size:15px; font-weight:700; color:#334155; margin: 24px 0 10px 0;">{cat}</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="text-left">Company</th>
                        <th class="text-right">Price ($)</th>
                        <th class="text-right">Change</th>
                        <th class="text-right">Volume</th>
                    </tr>
                </thead>
                <tbody>
"""
            for s in stocks:
                is_pos = s['pct_change'] >= 0
                color_cls = "text-green" if is_pos else "text-red"
                sign = "+" if is_pos else ""
                vol_str = MarketDataEngine.format_vol(s['volume'])
                vol_badge = '<span class="badge badge-vol">Vol Breakout</span>' if s['vol_spike'] else ''

                html += f"""
                    <tr>
                        <td class="text-left">
                            <div class="symbol-cell">
                                {s['name']}
                                <span class="sub-symbol">{s['ticker']}</span>
                                {vol_badge}
                            </div>
                        </td>
                        <td class="text-right" style="font-weight:700;">${s['price']:,.2f}</td>
                        <td class="text-right {color_cls}" style="font-weight:700;">
                            {sign}{s['change']:.2f} ({sign}{s['pct_change']:.2f}%)
                        </td>
                        <td class="text-right" style="color:#475569;">{vol_str}</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
        </div>
"""

        html += """
    </div>

</div>

</body>
</html>
"""
        return html

#############################################
## MODULE 4: EXECUTION & WORDPRESS PUBLISHING
#############################################

def main():
    print("🚀 Running US Market Wrap with Reference Styling...")
    
    # 1. Fetch Engine Data
    val_data = MarketDataEngine.get_valuation()
    benchmarks, sectors, watchlist = MarketDataEngine.fetch_market_overview()
    
    # 2. Build HTML with Inter typography & Tabular alignments
    html_content = UIBuilder.generate_html(benchmarks, sectors, watchlist, val_data)
    
    # Save locally as reference
    with open("us_market_wrap.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ Local preview generated as 'us_market_wrap.html'")

    # 3. Post to WordPress if credentials exist
    if WP_USER and WP_PASS and WP_URL:
        auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
        sp_change = benchmarks[0]['pct_change'] if benchmarks else 0.0
        payload = {
            'title': f"Wall Street Wrap: S&P 500 {'Gains' if sp_change > 0 else 'Slips'} {sp_change:.2f}% ({datetime.now().strftime('%d %b')})",
            'content': html_content,
            'status': 'publish',
            'categories': [CATEGORY_ID]
        }
        try:
            res = requests.post(WP_URL, headers=headers, json=payload, timeout=20)
            print("✅ Successfully published to WordPress!" if res.status_code == 201 else f"❌ WP Error: {res.text}")
        except Exception as e:
            print(f"❌ Failed publishing to WP: {e}")

if __name__ == "__main__":
    main()
