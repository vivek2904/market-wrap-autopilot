############################
### MODULE 1 - CONFIGURATION AND WATCHLIST 
############################

import os, requests, base64, pandas as pd, yfinance as yf, pandas_ta as ta
from datetime import datetime
from bs4 import BeautifulSoup
import io, re

# --- CREDENTIALS ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 15  # US Market

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

def process_watchlist(raw):
    t_map, s_map = {}, {}
    for sector, stocks in raw.items():
        tickers = []
        for s in stocks:
            match = re.search(r'(.*?)\s\((.*?)\)', s)
            if match:
                name, ticker = match.groups()
                tickers.append(ticker)
                t_map[ticker] = name
            else:
                tickers.append(s)
                t_map[s] = s
        s_map[sector] = tickers
    return s_map, t_map

SECTOR_MAP, NAME_MAP = process_watchlist(RAW_WATCHLIST)
INDEX_TICKERS = {'^GSPC': 'S&P 500', '^DJI': 'Dow Jones', '^IXIC': 'Nasdaq', '^RUT': 'Russell 2000', '^VIX': 'Volatility (VIX)'}

#####################################
########## MODULE 2: DATA EXTRACTION ENGINE
#####################################

class MarketDataEngine:
    @staticmethod
    def get_valuation_metrics():
        url = "https://www.multpl.com/s-p-500-pe-ratio"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            curr_pe = soup.find("div", {"id": "current-value"}).get_text(strip=True).replace("current", "").strip()
            return "The S&P 500 PE ratio is a primary measure of US equity valuation.", curr_pe, "8.2%", ""
        except: return "US Valuation Snapshot.", "24.5x", "8.1%", ""

    @staticmethod
    def get_bulk_stock_stats():
        all_tickers = list(NAME_MAP.keys())
        data = yf.download(all_tickers, period="60d", interval="1d", auto_adjust=True, threads=True)
        results = {}
        for t in all_tickers:
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
        if n >= 1e9: return f"{n/1e9:.2f}B"
        if n >= 1e6: return f"{n/1e6:.1f}M"
        return f"{n/1e3:.0f}K"

    @staticmethod
    def build_html_content(stock_data, idx_returns, val_data):
        summary, pe, forecast, _ = val_data
        html = f"<div style='background:#f8fafc; padding:30px; border-radius:20px; margin-bottom:30px;'><h2>📊 US Valuation Snapshot</h2><p>{summary}</p><b>PE: {pe} | Growth: {forecast}</b></div>"
        
        perf_map = {INDEX_TICKERS[k]: v for k, v in idx_returns.items() if k in INDEX_TICKERS}
        for sector, s_ret in sorted(perf_map.items(), key=lambda x: x[1], reverse=True):
            if sector not in SECTOR_MAP: continue
            
            # SORT STOCKS BY VOL RATIO
            sector_stocks = [dict(stock_data.get(t, {}), ticker=t) for t in SECTOR_MAP[sector] if t in stock_data]
            sorted_stocks = sorted(sector_stocks, key=lambda x: x.get('vol_ratio', 0), reverse=True)

            html += f"<div style='background:white; border:1px solid #e2e8f0; border-radius:20px; padding:25px; margin-bottom:25px;'>"
            html += f"<h3 style='margin:0;'>{sector} <span style='color:{'#16a34a' if s_ret > 0 else '#dc2626'}'>{s_ret:+.2f}%</span></h3>"
            html += "<div style='display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:15px; margin-top:20px;'>"
            
            for s in sorted_stocks:
                vol_x = s['vol_ratio']
                html += f"""
                <div style='border:1px solid #f1f5f9; padding:15px; border-radius:12px;'>
                    <small style='color:#64748b; text-transform:uppercase; font-size:10px;'>{NAME_MAP.get(s['ticker'])}</small><br>
                    <b>{s['ticker']}</b><br>
                    <span style='font-size:18px; font-weight:900;'>${s['price']:,.2f}</span><br>
                    <span style='color:{'#16a34a' if s['change']>0 else '#dc2626'}'>{s['change']:+.2f}%</span><br>
                    <div style='margin-top:10px; font-size:11px; {'color:#ea580c; font-weight:bold' if vol_x > 2.0 else 'color:#64748b'}'>
                        {'🔥' if vol_x > 2.0 else '📈'} VolX: {vol_x:.2f}x
                    </div>
                </div>"""
            html += "</div></div>"
        return html

###################################
### MODULE 4 - WORDPRESS PUBLISHER
###################################
class WordPressPublisher:
    @staticmethod
    def push_post(title, content):
        auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
        payload = {'title': title, 'content': content, 'status': 'publish', 'categories': [CATEGORY_ID]}
        res = requests.post(WP_URL, headers=headers, json=payload)
        return res.status_code == 201

###################################
### MODULE 5 - MAIN EXECUTION FLOW
###################################

def main():
    print(f"🚀 Starting US Market Wrap for {datetime.now().strftime('%Y-%m-%d')}...")
    data_engine = MarketDataEngine()
    hero_builder = HeroCardBuilder()
    report_builder = ReportBuilder()
    publisher = WordPressPublisher()
    
    # 1. Fetch Benchmarks
    bench_raw = yf.download(['^GSPC', '^VIX'], period='5d')['Close']
    i_change = ((bench_raw['^GSPC'].iloc[-1] / bench_raw['^GSPC'].iloc[-2]) - 1) * 100
    vix_val = bench_raw['^VIX'].iloc[-1]
    
    # 2. Sector Performance
    idx_raw = yf.download(list(INDEX_TICKERS.keys()), period='5d')['Close']
    idx_returns = ((idx_raw.iloc[-1] / idx_raw.iloc[-2] - 1) * 100).fillna(0)
    
    # 3. Bulk Stats
    stock_stats = data_engine.get_bulk_stock_stats()
    val_metrics = data_engine.get_valuation_metrics()
    
    # 4. Assembly
    hero_html = hero_builder.build_hero_card(bench_raw[['^GSPC']].rename(columns={'^GSPC': 'Close'}), i_change, vix_val)
    body_html = report_builder.build_html_content(stock_stats, idx_returns, val_metrics)
    
    post_title = f"US Market Wrap {datetime.now().strftime('%d %b %Y')}: S&P 500 {i_change:+.2f}%"
    if publisher.push_post(post_title, hero_html + body_html):
        print(f"✅ Post Successful: {post_title}")

if __name__ == "__main__":
    main()
