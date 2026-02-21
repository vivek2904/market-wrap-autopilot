import os, requests, base64, pandas as pd, yfinance as yf, pandas_ta as ta
from datetime import datetime
from bs4 import BeautifulSoup
import io, re

#############################################
## MODULE 1: CONFIGURATION & WATCHLIST
#############################################

WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

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

INDEX_MAP = {
    '^GSPC': 'S&P 500', 'XLK': 'Technology', 'XLV': 'Health Care', 'XLF': 'Financials', 
    'XLY': 'Cons. Discretionary', 'XLC': 'Communication', 'XLI': 'Industrials', 
    'XLP': 'Cons. Staples', 'XLE': 'Energy', 'XLB': 'Materials', 'XLRE': 'Real Estate', 'XLU': 'Utilities'
}

def get_ticker(s):
    match = re.search(r'\((.*?)\)', s)
    return match.group(1) if match else s

ALL_TICKERS = list(set([get_ticker(s) for sublist in WATCHLIST.values() for s in sublist]))

#############################################
## MODULE 2: DATA EXTRACTION ENGINE
#############################################

class MarketDataEngine:
    @staticmethod
    def get_valuation():
        url = "https://worldperatio.com/area/united-states/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            summary = " ".join([p.get_text() for p in soup.find_all('p', limit=3) if len(p.get_text()) > 50])
            tables = pd.read_html(io.StringIO(res.text))
            pe, forward_ret, table_html = "26.94", "3.26%", ""
            
            for df in tables:
                if 'Period' in df.columns and any('Average P/E' in col for col in df.columns):
                    pe_cols = [c for c in df.columns if "vs Current P/E" in str(c)]
                    if pe_cols:
                        match = re.search(r'\((.*?)\)', str(pe_cols[0]))
                        if match: pe = match.group(1)
                    table_html = df[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'Valuation']].head(5).to_html(index=False, border=0, classes='valuation-table')
                if not df.empty and '1 Years' in str(df.iloc[:, 0].values):
                    forward_ret = f"{df.iloc[0, 6]}%"
            return summary, pe, forward_ret, table_html
        except: return "US Market Valuation Analysis.", "26.94", "3.26%", ""

    @staticmethod
    def get_stock_stats():
        """Fixed method name to match main() call."""
        data = yf.download(ALL_TICKERS, period="60d", interval="1d", auto_adjust=True, threads=True)
        results = {}
        for t in ALL_TICKERS:
            try:
                subset = data.iloc[:, data.columns.get_level_values(1)==t]
                subset.columns = subset.columns.get_level_values(0)
                prices, vol = subset['Close'].dropna(), subset['Volume'].dropna()
                if len(prices) < 20: continue
                results[t] = {
                    'price': prices.iloc[-1],
                    'change': ((prices.iloc[-1]/prices.iloc[-2])-1)*100,
                    'rsi': ta.rsi(prices, length=14).iloc[-1],
                    'vol_ratio': vol.iloc[-1] / vol.iloc[-21:-1].mean(),
                    'curr_vol': vol.iloc[-1],
                    'avg_vol': vol.iloc[-21:-1].mean()
                }
            except: continue
        return results

#############################################
## MODULE 3: SENSATIONAL UI BUILDER
#############################################

class UIBuilder:
    @staticmethod
    def format_vol(n):
        if n >= 1e9: return f"{n/1e9:.2f}B"
        if n >= 1e6: return f"{n/1e6:.1f}M"
        return f"{n/1e3:.0f}K"

    @staticmethod
    def build_hero(gspc_data, change, vix):
        curr = float(gspc_data['Close'].iloc[-1])
        prev = float(gspc_data['Close'].iloc[-2])
        color = "#22c55e" if change > 0 else "#ef4444"
        vix_color = "#ef4444" if vix > 20 else "#22c55e"
        return f"""
        <div style="background: linear-gradient(135deg, #020617 0%, #0f172a 100%); color: white; padding: 40px; border-radius: 24px; font-family: sans-serif; margin-bottom: 30px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
                <div>
                    <span style="opacity: 0.6; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">S&P 500 Index</span>
                    <h1 style="font-size: 64px; margin: 10px 0;">{curr:,.2f}</h1>
                    <div style="font-size: 24px; font-weight: 700; color: {color};">
                        {'▲' if change > 0 else '▼'} {abs(change):.2f}% <span style="font-size:16px; opacity:0.8; color:white;">({curr-prev:+.2f} pts)</span>
                    </div>
                </div>
                <div style="text-align: right; background: rgba(255,255,255,0.05); padding: 20px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
                    <small style="opacity:0.6; text-transform:uppercase;">Fear Index (VIX)</small><br>
                    <b style="font-size: 32px; color: {vix_color};">{vix:.2f}</b><br>
                    <small style="opacity:0.8;">{'High Risk' if vix > 20 else 'Stable Market'}</small>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def build_body(stock_data, sector_returns, val_data):
        summary, pe, forward, table = val_data
        html = f"""
        <style>
            .valuation-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-family: sans-serif; font-size: 14px; }}
            .valuation-table th {{ background: #f8fafc; padding: 12px; border: 1px solid #e2e8f0; text-align: left; }}
            .valuation-table td {{ padding: 12px; border: 1px solid #e2e8f0; }}
            .sector-block {{ background: white; border: 1px solid #e2e8f0; border-radius: 20px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .stock-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }}
            .stock-card {{ border: 1px solid #f1f5f9; padding: 15px; border-radius: 12px; background:#fff; transition: 0.2s; }}
        </style>
        <div style="background:#f8fafc; border:1px solid #e1e4e8; padding:25px; border-radius:15px; font-family:sans-serif; margin-bottom:30px;">
            <h2 style="margin-top:0; color:#1a2b48;">Market Summary & Valuation</h2>
            <p>{summary}</p>
            <div style="display:flex; gap:40px; margin:20px 0; background:#fff; padding:15px; border-radius:10px; border:1px solid #e2e8f0;">
                <div><strong>Current P/E:</strong> <span style="color:#2563eb; font-size:18px;">{pe}</span></div>
                <div><strong>Exp. 1Y Return:</strong> <span style="color:#16a34a; font-size:18px;">{forward}</span></div>
            </div>
            {table}
        </div>
        """
        sorted_sectors = sector_returns.sort_values(ascending=False)
        for sector, s_ret in sorted_sectors.items():
            if sector not in WATCHLIST: continue
            html += f"""<div class="sector-block">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px;">
                    <h3 style="margin:0; font-family:sans-serif;">{sector}</h3>
                    <b style="font-size:20px; color:{'#16a34a' if s_ret > 0 else '#dc2626'}">{s_ret:+.2f}%</b>
                </div>
                <div class="stock-grid">"""
            sec_stocks = []
            for name_with_ticker in WATCHLIST.get(sector, []):
                ticker = get_ticker(name_with_ticker)
                if ticker in stock_data:
                    sec_stocks.append({'full_name': name_with_ticker, 'ticker': ticker, **stock_data[ticker]})
            sorted_stocks = sorted(sec_stocks, key=lambda x: x['vol_ratio'], reverse=True)
            for s in sorted_stocks:
                vol_x = float(s['vol_ratio'])
                vol_style = "color: #ea580c; background: #fff7ed; border:1px solid #ffedd5;" if vol_x > 2.0 else "color: #64748b;"
                html += f"""
                <div class="stock-card">
                    <small style="color:#64748b; font-size:10px; text-transform:uppercase;">{s['full_name'].split('(')[0]}</small><br>
                    <b>{s['ticker']}</b>
                    <div style="font-size:22px; font-weight:900; margin:5px 0;">${s['price']:,.2f}</div>
                    <div style="font-weight:700; color:{'#16a34a' if s['change']>0 else '#dc2626'}">{s['change']:+.2f}%</div>
                    <div style='margin-top:10px; padding:5px; border-radius:6px; font-size:11px; {vol_style}'>
                        {'🔥' if vol_x > 2.0 else '📈'} VolX: {vol_x:.2f}x
                        <div style="font-size:9px; opacity:0.8; margin-top:2px;">Today: {UIBuilder.format_vol(s['curr_vol'])}</div>
                    </div>
                </div>"""
            html += "</div></div>"
        return html

#############################################
## MODULE 4: EXECUTION & POST
#############################################

def main():
    print("🚀 Starting Wall Street Wrap...")
    engine = MarketDataEngine()
    
    # 1. Benchmarks
    bench_raw = yf.download(['^GSPC', '^VIX'] + list(INDEX_MAP.keys()), period='7d')['Close']
    sp_series = bench_raw['^GSPC'].dropna()
    sp_change = ((sp_series.iloc[-1] / sp_series.iloc[-2]) - 1) * 100
    vix_val = float(bench_raw['^VIX'].iloc[-1])
    
    # 2. Sector Returns
    sector_returns = ((bench_raw[list(INDEX_MAP.keys())].iloc[-1] / bench_raw[list(INDEX_MAP.keys())].iloc[-2]) - 1) * 100
    sector_returns = sector_returns.rename(INDEX_MAP).drop(labels=['S&P 500'], errors='ignore')

    # 3. Stats & Valuation
    stock_stats = engine.get_stock_stats() # Name fixed
    val_data = engine.get_valuation()

    # 4. Build HTML
    hero_html = UIBuilder.build_hero(pd.DataFrame(sp_series).rename(columns={'^GSPC': 'Close'}), sp_change, vix_val)
    body_html = UIBuilder.build_body(stock_stats, sector_returns, val_data)

    # 5. Push to WordPress
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
    payload = {
        'title': f"Wall Street Wrap: S&P 500 {'Gains' if sp_change > 0 else 'Slips'} {sp_change:.2f}% ({datetime.now().strftime('%d %b')})",
        'content': hero_html + body_html, 'status': 'publish', 'categories': [CATEGORY_ID]
    }
    res = requests.post(WP_URL, headers=headers, json=payload)
    print("✅ Success!" if res.status_code == 201 else f"❌ Error: {res.text}")

if __name__ == "__main__":
    main()
