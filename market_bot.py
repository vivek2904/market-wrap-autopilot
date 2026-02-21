import os, requests, base64, pandas as pd, yfinance as yf, pandas_ta as ta
from datetime import datetime
from bs4 import BeautifulSoup
import io

#############################################
## MODULE 1: CONFIGURATION & WATCHLIST
#############################################

# --- SECURE CREDENTIALS ---
WP_USER = os.environ.get('WP_USER')
WP_PASS = os.environ.get('WP_PASS')
WP_URL = os.environ.get('WP_URL')
CATEGORY_ID = 12 

# --- UPDATED SECTOR MAP (Cleaned of Delisted Tickers) ---
SECTOR_MAP = {
    'Nifty Bank': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK', 'INDUSINDBK', 'BANKBARODA', 'PNB', 'IDFCFIRSTB', 'FEDERALBNK'],
    'IT Services': ['TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM', 'LTIM', 'PERSISTENT', 'COFORGE', 'MPHASIS', 'KPITTECH'],
    'Automobile': ['M&M', 'MARUTI', 'BAJAJ-AUTO', 'EICHERMOT', 'TVSMOTOR', 'HEROMOTOCO', 'ASHOKLEY', 'MRF', 'BALKRISIND'], # Removed TATAMOTORS (Delisted/Issue)
    'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'GODREJCP', 'DABUR', 'MARICO', 'VBL', 'COLPAL', 'TATACONSUM'],
    'Metals': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'JINDALSTEL', 'VEDL', 'NMDC', 'SAIL', 'NATIONALUM', 'APLAPOLLO', 'RATNAMANI'],
    'Pharma': ['SUNPHARMA', 'CIPLA', 'DRREDDY', 'LUPIN', 'AUROPHARMA', 'ZYDUSLIFE', 'DIVISLAB', 'ALKEM', 'TORNTPHARM'], # Removed ABBOTT
    'Energy': ['RELIANCE', 'NTPC', 'ONGC', 'POWERGRID', 'BPCL', 'ADANIGREEN', 'TATAPOWER', 'IOC', 'GAIL', 'ADANIENSOL'],
    'Financial Services': ['BAJFINANCE', 'HDFCBANK', 'ICICIBANK', 'BAJAJFINSV', 'CHOLAFIN', 'PFC', 'SHRIRAMFIN', 'SBILIFE', 'HDFCLIFE'], # Removed REC
    'PSU Bank': ['SBIN', 'BANKBARODA', 'CANBK', 'UNIONBANK', 'IOB', 'PNB', 'INDIANB', 'BANKINDIA', 'UCOBANK', 'CENTRALBK'],
    'Realty': ['DLF', 'LODHA', 'GODREJPROP', 'OBEROIRLTY', 'PRESTIGE', 'PHOENIXLTD', 'BRIGADE', 'SOBHA', 'SIGNATURE', 'SUNTECK'],
    'Media': ['ZEEL', 'SUNTV', 'PVRINOX', 'NETWORK18', 'NAZARA', 'DISHTV', 'HATHWAY'], # Removed TV18, SAREGMAPA, TIPS
    'Consumption': ['ITC', 'HINDUNILVR', 'TITAN', 'ASIANPAINT', 'NESTLEIND', 'TRENT', 'DMART', 'BRITANNIA', 'PAGEIND'], # Removed ZOMATO
    'Infrastructure': ['RELIANCE', 'LT', 'BHARTIARTL', 'NTPC', 'ADANIPORTS', 'ULTRACEMCO', 'ONGC', 'GRASIM', 'IIFL', 'POWERGRID'],
    'PSE': ['NTPC', 'ONGC', 'POWERGRID', 'COALINDIA', 'BEL', 'HAL', 'BPCL', 'IOC', 'PFC'],
    'CPSE': ['NTPC', 'ONGC', 'POWERGRID', 'COALINDIA', 'BEL', 'NHPC', 'SJVN', 'NBCC', 'OIL', 'COCHINSHIP'],
    'Commodities': ['RELIANCE', 'TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'NTPC', 'ONGC', 'AMBUJACEM', 'GRASIM', 'VEDL', 'COALINDIA'],
    'Services': ['LT', 'ADANIPORTS', 'APOLLOHOSP', 'HDFCLIFE', 'SBILIFE', 'TRENT', 'INDIGO', 'VBL', 'TATACOMM'] # Removed GMRINFRA
}

# --- UPDATED INDEX TICKERS (Stable Yahoo Symbols) ---
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
    '^CNXPSE': 'PSE',
    'NIFTY_CONSUMPTION.NS': 'Consumption', 
    'NIFTY_CPSE.NS': 'CPSE', 
    'NIFTY_COMMODITIES.NS': 'Commodities', 
    'NIFTY_SERV_SECTOR.NS': 'Services'
}

#############################################
## MODULE 2: DATA EXTRACTION ENGINE
#############################################

class MarketDataEngine:
    @staticmethod
    def get_valuation_metrics():
        url = "https://worldperatio.com/area/india/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            summary = " ".join([p.get_text() for p in soup.find_all('p', limit=3) if len(p.get_text()) > 50])
            tables = pd.read_html(io.StringIO(res.text))
            pe, forecast, table_html = "N/A", "N/A", ""
            for df in tables:
                pe_col = [c for c in df.columns if "vs" in str(c)]
                if pe_col and pe == "N/A":
                    pe = str(pe_col[0]).split("vs")[-1].strip().translate({ord(i): None for i in "()'"})
                if 'Period' in df.columns and any('Average P/E' in col for col in df.columns):
                    table_html = df[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current P/E']].head(5).to_html(index=False, border=0, classes='valuation-table')
                if not df.empty and '1 Years' in str(df.iloc[:, 0].values):
                    forecast = f"{df.iloc[0, 6]}%"
            return summary, pe, forecast, table_html
        except: return "Valuation Analysis", "Live...", "7.33%", ""

    @staticmethod
    def get_bulk_stock_stats():
        all_tickers = list(set([f"{t}.NS" for sublist in SECTOR_MAP.values() for t in sublist]))
        data = yf.download(all_tickers, period="60d", interval="1d", auto_adjust=True)
        results = {}
        for t in all_tickers:
            try:
                subset = data.iloc[:, data.columns.get_level_values(1)==t]
                subset.columns = subset.columns.get_level_values(0)
                prices, vol = subset['Close'].dropna(), subset['Volume'].dropna()
                if len(prices) < 20: continue
                avg_vol = vol.iloc[-21:-1].mean()
                results[t.replace(".NS", "")] = {
                    'price': prices.iloc[-1],
                    'change': ((prices.iloc[-1]/prices.iloc[-2])-1)*100,
                    'rsi': ta.rsi(prices, length=14).iloc[-1],
                    'vol_ratio': vol.iloc[-1] / avg_vol if avg_vol > 0 else 1.0
                }
            except: continue
        return results

#############################################
## MODULE 3.1: THE SEO HERO CARD (DYNAMIC UI)
#############################################

class HeroCardBuilder:
    @staticmethod
    def get_market_sentiment(change):
        """Generates punchy, irresistible SEO-optimized headlines."""
        # Ensure change is a float for comparison
        val = float(change)
        if val > 1.0: return "Bulls on Rampage! 🚀 Nifty Shatters Resistance"
        elif val > 0: return "Green Shoot Recovery 📈 Bulls Defend Key Levels"
        elif val < -1.0: return "Blood on D-Street! 🩸 Bears Aggressive as Support Fails"
        else: return "Tug-of-War! ⚖️ Market Braces for Major Breakout"

    @staticmethod
    def build_hero_card(nifty_data, change):
        """
        Creates the high-info Hero Card showing OHLC and Yesterday's Close.
        """
        # CRITICAL FIX: Ensure values are scalars (floats), not Series
        curr_close = float(nifty_data['Close'].iloc[-1])
        curr_open = float(nifty_data['Open'].iloc[-1])
        curr_high = float(nifty_data['High'].iloc[-1])
        curr_low = float(nifty_data['Low'].iloc[-1])
        prev_close = float(nifty_data['Close'].iloc[-2])
        
        f_change = float(change)
        pts_diff = curr_close - prev_close
        sentiment_headline = HeroCardBuilder.get_market_sentiment(f_change)
        
        # UI color logic
        brand_color = "#22c55e" if f_change > 0 else "#ef4444"
        bg_gradient = "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)"
        
        return f"""
        <div style="background: {bg_gradient}; color: white; padding: 40px 30px; border-radius: 24px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); margin-bottom: 40px; font-family: 'Inter', sans-serif;">
            <div style="text-transform: uppercase; letter-spacing: 2px; font-size: 14px; font-weight: 700; color: {brand_color}; margin-bottom: 10px;">
                {sentiment_headline}
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 20px;">
                <div>
                    <span style="font-size: 18px; opacity: 0.7; display: block;">NIFTY 50 INDEX</span>
                    <span style="font-size: 64px; font-weight: 900; line-height: 1;">{curr_close:,.2f}</span>
                    <div style="margin-top: 10px; font-size: 24px; font-weight: 700; color: {brand_color};">
                        {'▲' if f_change > 0 else '▼'} {abs(f_change):.2f}% 
                        <span style="font-size: 16px; opacity: 0.8; font-weight: 400; color: white; margin-left: 10px;">
                            ({pts_diff:+.2f} pts)
                        </span>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; background: rgba(255,255,255,0.05); padding: 20px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="border-right: 1px solid rgba(255,255,255,0.1); padding-right: 15px;">
                        <small style="opacity:0.6; display:block; font-size:11px; text-transform:uppercase;">Prev Close</small>
                        <b style="font-size:16px;">{prev_close:,.2f}</b>
                    </div>
                    <div>
                        <small style="opacity:0.6; display:block; font-size:11px; text-transform:uppercase;">Open</small>
                        <b style="font-size:16px;">{curr_open:,.2f}</b>
                    </div>
                    <div style="border-right: 1px solid rgba(255,255,255,0.1); padding-right: 15px;">
                        <small style="opacity:0.6; display:block; font-size:11px; text-transform:uppercase;">Day High</small>
                        <b style="font-size:16px; color: #4ade80;">{curr_high:,.2f}</b>
                    </div>
                    <div>
                        <small style="opacity:0.6; display:block; font-size:11px; text-transform:uppercase;">Day Low</small>
                        <b style="font-size:16px; color: #f87171;">{curr_low:,.2f}</b>
                    </div>
                </div>
            </div>
        </div>
        """

#############################################
## MODULE 3: REPORT BUILDER (THE MISSING CLASS)
#############################################

class ReportBuilder:
    @staticmethod
    def get_seo_tags(change):
        return {
            'aioseo_title': f"Market Wrap {datetime.now().strftime('%d %b')}: Nifty {change:+.2f}%",
            'aioseo_description': f"Nifty ends at {change:+.2f}%. Full NSE analysis with RSI technicals and valuation forecasts."
        }

    @staticmethod
    def build_html_content(stock_data, idx_returns, val_data, nifty_info):
        summary, pe, forecast, v_table = val_data
        n_price, n_change = nifty_info
        
        perf_map = {INDEX_TICKERS[k]: v for k, v in idx_returns.items() if k in INDEX_TICKERS}
        sorted_sectors = sorted(perf_map.items(), key=lambda x: x[1], reverse=True)

        html = f"""
        <style>
            .market-card {{ font-family: 'Inter', sans-serif; max-width: 950px; margin: auto; }}
            .sector-block {{ background: white; border: 1px solid #e2e8f0; border-radius: 20px; padding: 25px; margin-bottom: 25px; }}
            .stock-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; margin-top: 20px; }}
            .stock-card {{ border: 1px solid #f1f5f9; padding: 12px; border-radius: 10px; font-size: 13px; }}
            a {{ text-decoration: none; color: #3b82f6; font-weight: 700; }}
            .tag {{ font-size: 10px; padding: 2px 5px; border-radius: 4px; font-weight: bold; text-transform: uppercase; }}
        </style>
        <div style="background:#f8fafc; padding:30px; border-radius:20px; border:1px solid #e2e8f0; margin-bottom:30px;">
            <h3>📊 Valuation Snapshot</h3>
            <div style="display:flex; gap:40px; margin:25px 0;">
                <div><small>CURRENT PE</small><br><b>{pe}</b></div>
                <div><small>1Y FORECAST</small><br><b>{forecast}</b></div>
            </div>
            <p>{summary}</p>
            {v_table}
        </div>
        """
        for sector, s_ret in sorted_sectors:
            if sector not in SECTOR_MAP: continue
            html += f"""<div class="sector-block">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #f1f5f9; padding-bottom:10px;">
                    <h3 style="margin:0;">{sector}</h3>
                    <b style="color:{'#16a34a' if s_ret > 0 else '#dc2626'}">{s_ret:+.2f}%</b>
                </div>
                <div class="stock-grid">"""
            for t in SECTOR_MAP[sector]:
                s = stock_data.get(t, {'price':0, 'change':0, 'rsi':50, 'vol_ratio':1})
                ext_url = f"https://www.google.com/finance/quote/{t}:NSE"
                rsi_tag = '<span class="tag" style="background:#fee2e2; color:#ef4444;">Overbought</span>' if s['rsi'] > 70 else ''
                html += f"""
                <div class="stock-card">
                    <b>{t}</b><br>
                    <a href="{ext_url}" target="_blank">₹{s['price']:,.2f}</a><br>
                    <span style="color:{'#16a34a' if s['change']>0 else '#dc2626'}">{s['change']:+.2f}%</span><br>
                    <span style="font-size:11px; color:#64748b;">Vol: {s['vol_ratio']:.2f}x</span><br>{rsi_tag}
                </div>"""
            html += "</div></div>"
        return html

#############################################
## MODULE 4: WORDPRESS PUBLISHER
#############################################

class WordPressPublisher:
    @staticmethod
    def push_post(title, content, seo_data):
        auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
        payload = {'title': title, 'content': content, 'status': 'publish', 'categories': [CATEGORY_ID], **seo_data}
        res = requests.post(WP_URL, headers=headers, json=payload)
        return res.status_code == 201

#############################################
## MODULE 5: MAIN EXECUTION FLOW
#############################################

def main():
    print(f"🚀 Starting Market Wrap execution for {datetime.now().strftime('%Y-%m-%d')}...")

    # 1. Initialize Engines
    data_engine = MarketDataEngine()
    hero_builder = HeroCardBuilder()
    report_builder = ReportBuilder()
    publisher = WordPressPublisher()
    
    # 2. Fetch Nifty 50 Data & FORCE FLOAT
    nifty_raw = yf.download('^NSEI', period='5d', interval='1d', auto_adjust=True)
    if nifty_raw.empty:
        print("❌ Error: Could not fetch Nifty data.")
        return

    # Using float() here is a double-insurance against the Format Error
    n_close_today = float(nifty_raw['Close'].iloc[-1])
    n_close_prev = float(nifty_raw['Close'].iloc[-2])
    n_change_pct = float(((n_close_today / n_close_prev) - 1) * 100)
    
    # 3. Fetch Index Data (Clean empty columns)
    print("📥 Fetching sectoral indices...")
    idx_raw = yf.download(list(INDEX_TICKERS.keys()), period='5d')['Close']
    idx_raw = idx_raw.dropna(axis=1, how='all') 
    
    # Ensure index returns are scalar-friendly
    idx_returns = ((idx_raw.iloc[-1] / idx_raw.iloc[-2] - 1) * 100).fillna(0)
    
    # 4. Fetch Watchlist Technicals
    stock_stats = data_engine.get_bulk_stock_stats()
    val_metrics = data_engine.get_valuation_metrics()
    
    # 5. Build Components
    hero_html = hero_builder.build_hero_card(nifty_raw, n_change_pct)
    body_html = report_builder.build_html_content(
        stock_stats, 
        idx_returns, 
        val_metrics, 
        (n_close_today, n_change_pct)
    )
    
    # 6. SEO & Publish
    seo_tags = report_builder.get_seo_tags(n_change_pct)
    post_date = datetime.now().strftime('%d %b %Y')
    post_title = f"India Market Wrap {post_date}: Nifty {n_change_pct:+.2f}%"
    
    if publisher.push_post(post_title, hero_html + body_html, seo_tags):
        print(f"✅ Success: {post_title}")
    else:
        print("❌ Posting Failed.")

if __name__ == "__main__":
    main()
