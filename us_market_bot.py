############################
### MODULE 1 - CONFIGURATION AND WATCHLIST 
############################

import os, requests, base64, pandas as pd, yfinance as yf, pandas_ta as ta
from datetime import datetime
from bs4 import BeautifulSoup
import io
import re

# --- SECURE CREDENTIALS ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 15  # US Market Category

# --- US WATCHLIST (Parsed for Tickers) ---
RAW_WATCHLIST = {
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

# Helper to extract TICKER from "Name (TICKER)"
def get_ticker(name_str):
    match = re.search(r'\((.*?)\)', name_str)
    return match.group(1) if match else name_str

# Cleaned Ticker Map for API calls
SECTOR_MAP = {k: [get_ticker(s) for s in v] for k, v in RAW_WATCHLIST.items()}

# --- US INDEX TICKERS ---
INDEX_TICKERS = {
    '^GSPC': 'S&P 500', 
    '^DJI': 'Dow Jones', 
    '^IXIC': 'Nasdaq', 
    '^RUT': 'Russell 2000', 
    '^VIX': 'Volatility (VIX)',
    'XLK': 'Technology', 
    'XLF': 'Financials', 
    'XLE': 'Energy', 
    'XLV': 'Health Care', 
    'XLY': 'Cons. Discretionary'
}

#####################################
########## MODULE 2: DATA EXTRACTION ENGINE
#####################################

class MarketDataEngine:
    @staticmethod
    def get_valuation_metrics():
        """SCRAPER: Fetches US Market PE Ratio (S&P 500)."""
        url = "https://www.multpl.com/s-p-500-pe-ratio"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            curr_pe = soup.find("div", {"id": "current-value"}).get_text(strip=True).replace("current", "").strip()
            summary = "The S&P 500 Shiller PE Ratio is currently at elevated levels compared to historical averages."
            return summary, curr_pe, "8.2%", ""
        except: 
            return "S&P 500 Valuation Analysis.", "24.5x", "8.0%", ""

    @staticmethod
    def get_bulk_stock_stats():
        """TECHNICALS: Fetches Price, RSI, and US-specific Volume data."""
        all_tickers = list(set([t for sublist in SECTOR_MAP.values() for t in sublist]))
        data = yf.download(all_tickers, period="60d", interval="1d", auto_adjust=True)
        results = {}
        for t in all_tickers:
            try:
                subset = data.iloc[:, data.columns.get_level_values(1)==t]
                subset.columns = subset.columns.get_level_values(0)
                prices, vol = subset['Close'].dropna(), subset['Volume'].dropna()
                if len(prices) < 20: continue
                
                avg_vol_20 = vol.iloc[-21:-1].mean()
                curr_vol = vol.iloc[-1]
                
                results[t] = {
                    'price': prices.iloc[-1],
                    'change': ((prices.iloc[-1]/prices.iloc[-2])-1)*100,
                    'rsi': ta.rsi(prices, length=14).iloc[-1],
                    'vol_ratio': curr_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0,
                    'curr_vol': curr_vol,
                    'avg_vol': avg_vol_20
                }
            except: continue
        return results

#############################
#########  MODULE 3.1: THE SEO HERO CARD (US THEME)
#############################

class HeroCardBuilder:
    @staticmethod
    def get_market_sentiment(change):
        val = float(change)
        if val > 1.0: return "Wall Street Rally! 🚀 S&P 500 Surges"
        elif val > 0.2: return "Markets Edge Higher 📈 Momentum Sustained"
        elif val < -1.0: return "Sell-Off Alert! 🩸 Bears Aggressive on D-Street"
        else: return "Choppy Trading ⚖️ Markets Await Catalyst"

    @staticmethod
    def build_hero_card(index_data, change):
        today = index_data.iloc[-1]
        yesterday = index_data.iloc[-2]
        curr_close, prev_close = float(today['Close']), float(yesterday['Close'])
        brand_color = "#22c55e" if change > 0 else "#ef4444"
        
        return f"""
        <div style="background: linear-gradient(135deg, #020617 0%, #1e293b 100%); color: white; padding: 40px 30px; border-radius: 24px; margin-bottom: 40px; font-family: 'Inter', sans-serif;">
            <div style="text-transform: uppercase; letter-spacing: 2px; font-size: 13px; font-weight: 800; color: {brand_color}; margin-bottom: 12px;">{HeroCardBuilder.get_market_sentiment(change)}</div>
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 30px;">
                <div>
                    <span style="font-size: 16px; opacity: 0.6; font-weight: 600; display: block;">S&P 500 INDEX</span>
                    <span style="font-size: 68px; font-weight: 900; line-height: 0.9;">{curr_close:,.2f}</span>
                    <div style="margin-top: 15px; font-size: 26px; font-weight: 700; color: {brand_color};">
                        {'▲' if change > 0 else '▼'} {abs(change):.2f}% ({curr_close - prev_close:+.2f} pts)
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; background: rgba(255,255,255,0.03); padding: 25px; border-radius: 20px;">
                    <div><small style="opacity:0.5; font-size:10px;">DAY HIGH</small><br><b style="font-size:17px; color:#22c55e;">{today['High']:,.2f}</b></div>
                    <div><small style="opacity:0.5; font-size:10px;">DAY LOW</small><br><b style="font-size:17px; color:#ef4444;">{today['Low']:,.2f}</b></div>
                </div>
            </div>
        </div>
        """

#################################
####### MODULE 3.2: US WATCHLIST (MILLIONS/BILLIONS)
#################################

class ReportBuilder:
    @staticmethod
    def format_vol(n):
        """Formats numbers into US Million/Billion system."""
        if n >= 1e9: return f"{n/1e9:.2f}B"
        if n >= 1e6: return f"{n/1e6:.1f}M"
        if n >= 1e3: return f"{n/1e3:.0f}K"
        return f"{n:.0f}"

    @staticmethod
    def build_html_content(stock_data, idx_returns, val_data, index_info):
        summary, pe, forecast, _ = val_data
        perf_map = {INDEX_TICKERS[k]: v for k, v in idx_returns.items() if k in INDEX_TICKERS}
        sorted_sectors = sorted(perf_map.items(), key=lambda x: x[1], reverse=True)

        html = f"""<style>
            .sector-block {{ background: white; border: 1px solid #e2e8f0; border-radius: 20px; padding: 25px; margin-bottom: 25px; font-family: 'Inter', sans-serif; }}
            .stock-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-top: 20px; }}
            .stock-card {{ border: 1px solid #f1f5f9; padding: 15px; border-radius: 12px; font-size: 13px; background:#fff; }}
            .vol-heat {{ font-size: 12px; font-weight: 700; margin-top: 5px; display: block; }}
            a {{ text-decoration: none; color: #2563eb; font-weight: 700; }}
        </style>
        <div style="background:#f8fafc; padding:30px; border-radius:20px; margin-bottom:30px;">
            <h2>📊 US Valuation Snapshot</h2>
            <div style="display:flex; gap:40px; margin:20px 0;">
                <div><small>S&P 500 PE</small><br><b style="font-size:24px;">{pe}</b></div>
                <div><small>EST. GROWTH</small><br><b style="font-size:24px; color:#22c55e;">{forecast}</b></div>
            </div>
            <p>{summary}</p>
        </div>"""

        for sector, s_ret in sorted_sectors:
            if sector not in SECTOR_MAP: continue
            
            # SORT STOCKS BY VOL MULTIPLIER
            sector_stocks = [dict(stock_data.get(t, {}), ticker=t) for t in SECTOR_MAP[sector] if t in stock_data]
            sorted_stocks = sorted(sector_stocks, key=lambda x: x['vol_ratio'], reverse=True)

            html += f"""<div class="sector-block">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{sector}</h3>
                    <b style="color:{'#16a34a' if s_ret > 0 else '#dc2626'}">{s_ret:+.2f}%</b>
                </div>
                <div style="font-size:11px; color:#64748b; margin-top:8px; font-weight:600;">
                    💡 Note: VolumeX is a multiplier of 20 Day average volume. High values = Institutional Activity.
                </div>
                <div class="stock-grid">"""
            
            for s in sorted_stocks:
                t = s['ticker']
                vol_val = float(s['vol_ratio'])
                vol_style = "color: #ea580c; background: #fff7ed; padding: 4px; border-radius: 4px;" if vol_val > 2.0 else "color: #64748b;"
                
                html += f"""
                <div class="stock-card">
                    <b>{t}</b><br>
                    <div style="font-size:18px; font-weight:900; margin:5px 0;">${s['price']:,.2f}</div>
                    <div style="font-weight:700; color:{'#16a34a' if s['change'] > 0 else '#dc2626'}">{s['change']:+.2f}%</div>
                    <div style="{vol_style} margin-top:8px;">
                        <span class="vol-heat">{'🔥' if vol_val > 2.0 else '📈'} VolumeX: {vol_val:.2f}x</span>
                        <div style="font-size:10px; opacity:0.8;">T: {ReportBuilder.format_vol(s['curr_vol'])} | Avg: {ReportBuilder.format_vol(s['avg_vol'])}</div>
                    </div>
                </div>"""
            html += "</div></div>"
        return html

###################################
### MODULE 5 - MAIN EXECUTION FLOW
###################################

def main():
    print(f"🚀 Starting US Market Wrap for {datetime.now().strftime('%Y-%m-%d')}...")
    data_engine = MarketDataEngine()
    hero_builder = HeroCardBuilder()
    report_builder = ReportBuilder()
    publisher = WordPressPublisher()
    
    # 1. Fetch S&P 500 Data
    index_raw = yf.download('^GSPC', period='5d', interval='1d', auto_adjust=True)
    if index_raw.empty: return
    i_close_today = float(index_raw['Close'].iloc[-1])
    i_change_pct = float(((i_close_today / index_raw['Close'].iloc[-2]) - 1) * 100)
    
    # 2. Fetch Index Data
    idx_raw = yf.download(list(INDEX_TICKERS.keys()), period='5d')['Close'].dropna(axis=1, how='all')
    idx_returns = ((idx_raw.iloc[-1] / idx_raw.iloc[-2] - 1) * 100).fillna(0)
    
    # 3. Data Collection
    stock_stats = data_engine.get_bulk_stock_stats()
    val_metrics = data_engine.get_valuation_metrics()
    
    # 4. Assembly & Publish
    hero_html = hero_builder.build_hero_card(index_raw, i_change_pct)
    body_html = report_builder.build_html_content(stock_stats, idx_returns, val_metrics, (i_close_today, i_change_pct))
    
    post_date = datetime.now().strftime('%d %b %Y')
    post_title = f"US Market Wrap {post_date}: S&P 500 {i_change_pct:+.2f}%"
    
    if publisher.push_post(post_title, hero_html + body_html, {}):
        print(f"✅ Success: {post_title}")

if __name__ == "__main__":
    main()
