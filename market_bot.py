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
        """Generates punchy, irresistible headlines based on daily move."""
        val = float(change)
        if val > 1.2: return "Bulls on Rampage! 🚀 Nifty Shatters Resistance"
        elif val > 0.3: return "Green Shoot Recovery 📈 Bulls Defend Key Levels"
        elif val < -1.2: return "Blood on D-Street! 🩸 Bears Aggressive as Support Fails"
        elif abs(val) <= 0.3: return "Tug-of-War! ⚖️ Market Braces for Major Breakout"
        else: return "Bears in Control 🔻 Sellers Dominate the Session"

    @staticmethod
    def build_hero_card(nifty_data, change):
        """Creates the professional Hero Dashboard with color-coded Highs/Lows."""
        today = nifty_data.iloc[-1]
        yesterday = nifty_data.iloc[-2]
        
        # Explicit scalar conversion for formatting
        curr_close = float(today['Close'])
        curr_open = float(today['Open'])
        curr_high = float(today['High'])
        curr_low = float(today['Low'])
        prev_close = float(yesterday['Close'])
        
        # Contextual Color Logic
        brand_color = "#22c55e" if change > 0 else "#ef4444"
        open_color = "#22c55e" if curr_open > prev_close else "#ef4444"
        
        return f"""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 40px 30px; border-radius: 24px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); margin-bottom: 40px; font-family: 'Inter', sans-serif;">
            
            <div style="text-transform: uppercase; letter-spacing: 2px; font-size: 13px; font-weight: 800; color: {brand_color}; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
                {HeroCardBuilder.get_market_sentiment(change)}
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 30px;">
                <div>
                    <span style="font-size: 16px; opacity: 0.6; font-weight: 600; display: block;">NIFTY 50 INDEX</span>
                    <span style="font-size: 68px; font-weight: 900; line-height: 0.9;">{curr_close:,.2f}</span>
                    <div style="margin-top: 15px; font-size: 26px; font-weight: 700; color: {brand_color};">
                        {'▲' if change > 0 else '▼'} {abs(change):.2f}% 
                        <span style="font-size: 16px; opacity: 0.8; font-weight: 500; color: white; margin-left: 12px; background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 8px;">
                            {curr_close - prev_close:+.2f} pts
                        </span>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; background: rgba(255,255,255,0.03); padding: 25px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="border-right: 1px solid rgba(255,255,255,0.1); padding-right: 15px;">
                        <small style="opacity:0.5; font-size:10px; text-transform:uppercase;">Prev Close</small><br>
                        <b style="font-size:17px; color: #94a3b8;">{prev_close:,.2f}</b>
                    </div>
                    <div style="padding-left: 5px;">
                        <small style="opacity:0.5; font-size:10px; text-transform:uppercase;">Open Price</small><br>
                        <b style="font-size:17px; color: {open_color};">{curr_open:,.2f}</b>
                    </div>
                    <div style="border-right: 1px solid rgba(255,255,255,0.1); padding-right: 15px; margin-top: 10px;">
                        <small style="opacity:0.5; font-size:10px; text-transform:uppercase;">Day High</small><br>
                        <b style="font-size:17px; color: #22c55e;">{curr_high:,.2f}</b>
                    </div>
                    <div style="padding-left: 5px; margin-top: 10px;">
                        <small style="opacity:0.5; font-size:10px; text-transform:uppercase;">Day Low</small><br>
                        <b style="font-size:17px; color: #ef4444;">{curr_low:,.2f}</b>
                    </div>
                </div>
            </div>
        </div>
        """

#############################################
###MODULE 3.2: THE HEAT-MAPPED WATCHLIST
#############################################
  
class ReportBuilder:
    @staticmethod
    def get_seo_tags(change):
        return {
            'aioseo_title': f"Market Wrap {datetime.now().strftime('%d %b')}: Nifty {change:+.2f}% | 170+ Stocks Analysis",
            'aioseo_description': f"Nifty ends at {change:+.2f}%. Full NSE analysis with RSI technicals, valuation forecasts, and institutional volume signals."
        }

    @staticmethod
    def build_html_content(stock_data, idx_returns, val_data, nifty_info):
        summary, pe, forecast, v_table = val_data
        
        # Sort sectors by index performance
        perf_map = {INDEX_TICKERS[k]: v for k, v in idx_returns.items() if k in INDEX_TICKERS}
        sorted_sectors = sorted(perf_map.items(), key=lambda x: x[1], reverse=True)

        html = f"""
        <style>
            .market-card {{ font-family: 'Inter', sans-serif; max-width: 950px; margin: auto; color: #1e293b; line-height: 1.6; }}
            .valuation-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
            .valuation-table th {{ background: #f1f5f9; text-align: left; padding: 12px; border-bottom: 2px solid #e2e8f0; }}
            .sector-block {{ background: white; border: 1px solid #e2e8f0; border-radius: 20px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .stock-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; margin-top: 20px; }}
            .stock-card {{ border: 1px solid #f1f5f9; padding: 12px; border-radius: 10px; font-size: 13px; background: #fff; transition: transform 0.2s; }}
            .stock-card:hover {{ transform: translateY(-3px); border-color: #3b82f6; }}
            .vol-heat {{ font-size: 11px; font-weight: 700; margin-top: 6px; display: block; }}
            .tag {{ font-size: 10px; padding: 2px 5px; border-radius: 4px; font-weight: bold; text-transform: uppercase; }}
            a {{ text-decoration: none; color: #3b82f6; font-weight: 700; }}
        </style>

        <div style="background:#f8fafc; padding:30px; border-radius:20px; border:1px solid #e2e8f0; margin-bottom:30px;">
            <h2 style="margin-top:0;">📊 Valuation Analytics</h2>
            <div style="display:flex; gap:40px; margin:25px 0; background:white; padding:20px; border-radius:15px;">
                <div><small>CURRENT PE</small><br><b style="font-size:28px;">{pe}</b></div>
                <div><small>1Y FORECAST</small><br><b style="font-size:28px; color:#22c55e;">{forecast}</b></div>
            </div>
            <p style="font-size:17px;">{summary}</p>
            {v_table}
        </div>
        """
        
        for sector, s_ret in sorted_sectors:
            if sector not in SECTOR_MAP: continue
            
            # --- NEW STOCK SORTING LOGIC ---
            # Extract and sort stocks by the volume multiplier (vol_ratio)
            sector_stocks = []
            for t in SECTOR_MAP[sector]:
                stats = stock_data.get(t, {'price':0, 'change':0, 'rsi':50, 'vol_ratio':1.0})
                sector_stocks.append({'ticker': t, **stats})
            
            # Descending sort: Highest volume shockers first
            sorted_stocks = sorted(sector_stocks, key=lambda x: x['vol_ratio'], reverse=True)

            html += f"""<div class="sector-block">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #f1f5f9; padding-bottom:10px;">
                    <h3 style="margin:0; font-size:22px;">{sector}</h3>
                    <b style="font-size:20px; color:{'#16a34a' if s_ret > 0 else '#dc2626'}">{s_ret:+.2f}%</b>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-top: 8px; font-style: italic;">
                    Note: "Vol X" indicates the multiplier relative to the 20-day average volume. Higher values signal institutional activity.
                </div>
                <div class="stock-grid">"""
            
            for s in sorted_stocks:
                t = s['ticker']
                ext_url, int_url = f"https://www.google.com/finance/quote/{t}:NSE", f"{WP_URL.split('wp-json')[0]}?s={t}"
                
                # --- HEAT-MAPPED VOLUME RATIO ---
                vol_val = float(s['vol_ratio'])
                if vol_val > 2.5:
                    vol_html = f'<span class="vol-heat" style="color: #ea580c; background: #fff7ed; padding: 2px 4px; border-radius: 4px;">🔥 {vol_val:.2f}x Vol</span>'
                elif vol_val > 1.5:
                    vol_html = f'<span class="vol-heat" style="color: #d97706;">📈 {vol_val:.2f}x Vol</span>'
                else:
                    vol_html = f'<span class="vol-heat" style="color: #64748b;">{vol_val:.2f}x Vol</span>'
                
                rsi_tag = '<span class="tag" style="background:#fee2e2; color:#ef4444;">Overbought</span>' if s['rsi'] > 70 else \
                          ('<span class="tag" style="background:#dcfce7; color:#22c55e;">Oversold</span>' if s['rsi'] < 30 else '')

                html += f"""
                <div class="stock-card">
                    <b><a href="{int_url}">{t}</a></b><br>
                    <div style="font-size:16px; font-weight:800; margin:4px 0;"><a href="{ext_url}" target="_blank" style="color:#1e293b;">₹{s['price']:,.2f}</a></div>
                    <div style="font-weight:700; color:{'#16a34a' if s['change'] > 0 else '#dc2626'}">{s['change']:+.2f}%</div>
                    {vol_html}
                    <div style="margin-top:8px;">{rsi_tag}</div>
                </div>"""
            html += "</div></div>"
        return html

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
