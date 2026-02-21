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
        """Formats numbers into US Million/Billion system for professional readability."""
        if n >= 1e9: return f"{n/1e9:.2f}B"
        if n >= 1e6: return f"{n/1e6:.1f}M"
        if n >= 1e3: return f"{n/1e3:.0f}K"
        return f"{n:.0f}"

    @staticmethod
    def build_hero(gspc_data, change, vix):
        """Creates the high-impact dashboard header with the VIX Fear Gauge."""
        curr = float(gspc_data['Close'].iloc[-1])
        prev = float(gspc_data['Close'].iloc[-2])
        color = "#22c55e" if change > 0 else "#ef4444"
        vix_color = "#ef4444" if vix > 20 else "#22c55e"
        
        return f"""
        <div style="background: linear-gradient(135deg, #020617 0%, #0f172a 100%); color: white; padding: 45px; border-radius: 24px; font-family: 'Inter', sans-serif; margin-bottom: 30px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 30px;">
                <div>
                    <span style="opacity: 0.6; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; font-size: 14px;">S&P 500 Index Baseline</span>
                    <h1 style="font-size: 72px; margin: 10px 0; font-weight: 900; line-height: 1;">{curr:,.2f}</h1>
                    <div style="font-size: 28px; font-weight: 800; color: {color};">
                        {'▲' if change > 0 else '▼'} {abs(change):.2f}% 
                        <span style="font-size: 18px; opacity: 0.7; color: white; margin-left: 10px;">({curr-prev:+.2f} pts)</span>
                    </div>
                </div>
                <div style="text-align: right; background: rgba(255,255,255,0.05); padding: 25px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); min-width: 200px;">
                    <small style="opacity:0.6; text-transform:uppercase; font-weight: 700; letter-spacing: 1px;">VIX Fear Index</small><br>
                    <b style="font-size: 42px; color: {vix_color}; line-height: 1;">{vix:.2f}</b><br>
                    <div style="margin-top: 10px; font-weight: 600; font-size: 14px; color: {vix_color};">
                        {'⚠️ High Volatility' if vix > 20 else '✅ Market Calm'}
                    </div>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def build_body(stock_data, sector_returns, val_data):
        """Builds the main report body with large fonts and institutional volume logic."""
        summary, pe, forward, table = val_data
        
        html = f"""
        <style>
            .valuation-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-family: 'Inter', sans-serif; font-size: 15px; }}
            .valuation-table th {{ background: #f8fafc; padding: 15px; border: 1px solid #e2e8f0; text-align: left; font-weight: 800; }}
            .valuation-table td {{ padding: 15px; border: 1px solid #e2e8f0; color: #475569; }}
            
            .sector-block {{ background: white; border: 1px solid #e2e8f0; border-radius: 24px; padding: 30px; margin-bottom: 35px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .stock-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; margin-top: 25px; }}
            
            .stock-card {{ border: 1px solid #f1f5f9; padding: 22px; border-radius: 18px; background:#fff; transition: 0.3s; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
            .stock-card:hover {{ transform: translateY(-5px); box-shadow: 0 12px 20px -5px rgba(0,0,0,0.1); border-color: #3b82f6; }}
            
            .company-name {{ font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 4px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }}
            .ticker-label {{ font-size: 22px; font-weight: 900; color: #1e293b; line-height: 1.2; }}
            .price-main {{ font-size: 32px; font-weight: 900; color: #0f172a; margin: 10px 0; letter-spacing: -1px; }}
            .change-text {{ font-size: 18px; font-weight: 800; }}
            
            .vol-badge {{ margin-top: 15px; padding: 12px; border-radius: 12px; border: 1px solid #f1f5f9; }}
            .vol-x-val {{ font-size: 15px; font-weight: 800; display: block; margin-bottom: 4px; }}
            .vol-raw-stats {{ font-size: 12px; color: #64748b; line-height: 1.5; font-weight: 500; }}
        </style>

        <div style="background: #eff6ff; border-left: 6px solid #3b82f6; padding: 20px; border-radius: 12px; margin-bottom: 35px; font-family: 'Inter', sans-serif;">
            <strong style="color: #1e40af; font-size: 18px; display: block; margin-bottom: 5px;">📊 Institutional Volume Radar</strong>
            <span style="color: #1e3a8a; font-size: 15px; line-height: 1.6;">
                <strong>VolX (Volume Multiplier):</strong> Measures current session activity vs. the 20-day average. 
                Spikes above 2.0x (🔥) signal high-conviction institutional accumulation or distribution.
            </span>
        </div>

        <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:30px; border-radius:20px; font-family: sans-serif; margin-bottom:40px;">
            <h2 style="margin-top:0; color:#1e293b; font-size: 26px; font-weight: 800;">US Market Summary & Valuation</h2>
            <p style="font-size: 17px; color: #475569; line-height: 1.7;">{summary}</p>
            <div style="display:flex; gap:50px; margin:25px 0; background:#fff; padding:20px; border-radius:15px; border:1px solid #e2e8f0;">
                <div><small style="text-transform: uppercase; font-weight: 700; color: #94a3b8; font-size: 12px;">Current P/E Ratio</small><br><b style="color:#2563eb; font-size: 28px; font-weight: 900;">{pe}</b></div>
                <div><small style="text-transform: uppercase; font-weight: 700; color: #94a3b8; font-size: 12px;">Exp. 1Y Forward Return</small><br><b style="color:#16a34a; font-size: 28px; font-weight: 900;">{forward}</b></div>
            </div>
            <div style="overflow-x: auto;">{table}</div>
        </div>
        """

        # Sorted sectors loop
        sorted_sectors = sector_returns.sort_values(ascending=False)
        for sector, s_ret in sorted_sectors.items():
            if sector not in WATCHLIST: continue
            
            html += f"""<div class="sector-block">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #f1f5f9; padding-bottom: 15px;">
                    <h3 style="margin:0; font-family: sans-serif; font-size: 26px; font-weight: 800; color: #0f172a;">{sector}</h3>
                    <b style="font-size:24px; font-weight: 900; color:{'#16a34a' if s_ret > 0 else '#dc2626'}">{s_ret:+.2f}%</b>
                </div>
                <div class="stock-grid">"""
            
            # Stock Logic: Sorted by vol_ratio inside build_body
            sec_stocks = []
            for name_with_ticker in WATCHLIST.get(sector, []):
                ticker = re.search(r'\((.*?)\)', name_with_ticker).group(1) if '(' in name_with_ticker else name_with_ticker
                if ticker in stock_data:
                    sec_stocks.append({'full_name': name_with_ticker, 'ticker': ticker, **stock_data[ticker]})
            
            sorted_stocks = sorted(sec_stocks, key=lambda x: x['vol_ratio'], reverse=True)

            for s in sorted_stocks:
                vx = float(s['vol_ratio'])
                v_color = "#ea580c" if vx > 2.0 else "#1e293b"
                v_bg = "#fff7ed" if vx > 2.0 else "#f8fafc"
                
                html += f"""
                <div class="stock-card">
                    <div class="company-name">{s['full_name'].split('(')[0].strip()}</div>
                    <div class="ticker-label">{s['ticker']}</div>
                    
                    <div class="price-main">${s['price']:,.2f}</div>
                    <div class="change-text" style="color:{'#16a34a' if s['change']>0 else '#dc2626'}">
                        {'▲' if s['change'] > 0 else '▼'} {abs(s['change']):.2f}%
                    </div>

                    <div class="vol-badge" style="background: {v_bg};">
                        <span class="vol-x-val" style="color: {v_color};">
                            {'🔥' if vx > 2.0 else '📈'} VolX: {vx:.2f}x
                        </span>
                        <div class="vol-raw-stats">
                            <strong>Today:</strong> {UIBuilder.format_vol(s['curr_vol'])}<br>
                            <strong>20D Avg:</strong> {UIBuilder.format_vol(s.get('avg_vol', 0))}
                        </div>
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
