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
        """SCRAPER: Fetches PE, Forecasts, and Historical Tables from WorldPERatio."""
        url = "https://worldperatio.com/area/india/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            # Extract summary text
            summary = " ".join([p.get_text() for p in soup.find_all('p', limit=3) if len(p.get_text()) > 50])
            tables = pd.read_html(io.StringIO(res.text))
            pe, forecast, table_html = "N/A", "N/A", ""
            for df in tables:
                # Find Current PE
                pe_col = [c for c in df.columns if "vs" in str(c)]
                if pe_col and pe == "N/A":
                    pe = str(pe_col[0]).split("vs")[-1].strip().translate({ord(i): None for i in "()'"})
                # Find Historical Averages Table
                if 'Period' in df.columns and any('Average P/E' in col for col in df.columns):
                    table_html = df[['Period', 'Average P/E (μ)', 'Std Dev (σ)', 'vs Current P/E']].head(5).to_html(index=False, border=0, classes='valuation-table')
                # Find 1Y Forecast
                if not df.empty and '1 Years' in str(df.iloc[:, 0].values):
                    forecast = f"{df.iloc[0, 6]}%"
            return summary, pe, forecast, table_html
        except Exception as e: 
            print(f"⚠️ Valuation Scrape Error: {e}")
            return "Historical analysis for Nifty valuation.", "Analyzing...", "7.33%", ""

    @staticmethod
    def get_bulk_stock_stats():
        """TECHNICALS: Fetches Price, RSI, Multipliers, and RAW Volume data."""
        all_tickers = list(set([f"{t}.NS" for sublist in SECTOR_MAP.values() for t in sublist]))
        data = yf.download(all_tickers, period="60d", interval="1d", auto_adjust=True)
        results = {}
        for t in all_tickers:
            try:
                subset = data.iloc[:, data.columns.get_level_values(1)==t]
                subset.columns = subset.columns.get_level_values(0)
                prices, vol = subset['Close'].dropna(), subset['Volume'].dropna()
                if len(prices) < 20: continue
                
                # Volume Calculations
                avg_vol_20 = vol.iloc[-21:-1].mean()
                curr_vol_today = vol.iloc[-1]
                
                results[t.replace(".NS", "")] = {
                    'price': prices.iloc[-1],
                    'change': ((prices.iloc[-1]/prices.iloc[-2])-1)*100,
                    'rsi': ta.rsi(prices, length=14).iloc[-1],
                    'vol_ratio': curr_vol_today / avg_vol_20 if avg_vol_20 > 0 else 1.0,
                    'curr_vol': curr_vol_today,  # NEW: Added raw today vol
                    'avg_vol': avg_vol_20        # NEW: Added raw avg vol
                }
            except Exception as e: 
                continue
        return results
#############################################
## MODULE 3.1: THE SEO HERO CARD (DYNAMIC UI)
#############################################

class HeroCardBuilder:
    @staticmethod
    def get_market_sentiment(change):
        val = float(change)
        if val > 1.2: return "Bulls on Rampage! 🚀 Nifty Shatters Resistance"
        elif val > 0.3: return "Green Shoot Recovery 📈 Bulls Defend Key Levels"
        elif val < -1.2: return "Blood on D-Street! 🩸 Bears Aggressive as Support Fails"
        elif abs(val) <= 0.3: return "Tug-of-War! ⚖️ Market Braces for Major Breakout"
        else: return "Bears in Control 🔻 Sellers Dominate the Session"

    @staticmethod
    def _safe_scalar(val):
        if hasattr(val, 'item'):
            return float(val.item())
        return float(val)

    @staticmethod
    def build_hero_card(nifty_data, change):
        today = nifty_data.iloc[-1]
        yesterday = nifty_data.iloc[-2]
        
        curr_close = HeroCardBuilder._safe_scalar(today['Close'])
        curr_open = HeroCardBuilder._safe_scalar(today['Open'])
        curr_high = HeroCardBuilder._safe_scalar(today['High'])
        curr_low = HeroCardBuilder._safe_scalar(today['Low'])
        prev_close = HeroCardBuilder._safe_scalar(yesterday['Close'])
        
        brand_color = "#22c55e" if change > 0 else "#ef4444"
        open_color = "#22c55e" if curr_open > prev_close else "#ef4444"
        
        return f"""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 24px 20px; border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.25); margin-bottom: 20px; font-family: 'Inter', sans-serif;">
            
            <div style="text-transform: uppercase; letter-spacing: 1.5px; font-size: 11px; font-weight: 800; color: {brand_color}; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
                {HeroCardBuilder.get_market_sentiment(change)}
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                <div>
                    <span style="font-size: 12px; opacity: 0.5; font-weight: 600; display: block;">NIFTY 50 INDEX</span>
                    <span style="font-size: 48px; font-weight: 900; line-height: 0.95;">{curr_close:,.2f}</span>
                    <div style="margin-top: 8px; font-size: 20px; font-weight: 700; color: {brand_color};">
                        {'▲' if change > 0 else '▼'} {abs(change):.2f}% 
                        <span style="font-size: 13px; opacity: 0.8; font-weight: 500; color: white; margin-left: 8px; background: rgba(255,255,255,0.08); padding: 2px 8px; border-radius: 6px;">
                            {curr_close - prev_close:+.2f} pts
                        </span>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: rgba(255,255,255,0.03); padding: 14px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08);">
                    <div style="border-right: 1px solid rgba(255,255,255,0.08); padding-right: 10px;">
                        <small style="opacity:0.4; font-size:9px; text-transform:uppercase;">Prev Close</small><br>
                        <b style="font-size:14px; color: #94a3b8;">{prev_close:,.2f}</b>
                    </div>
                    <div style="padding-left: 3px;">
                        <small style="opacity:0.4; font-size:9px; text-transform:uppercase;">Open Price</small><br>
                        <b style="font-size:14px; color: {open_color};">{curr_open:,.2f}</b>
                    </div>
                    <div style="border-right: 1px solid rgba(255,255,255,0.08); padding-right: 10px; margin-top: 6px;">
                        <small style="opacity:0.4; font-size:9px; text-transform:uppercase;">Day High</small><br>
                        <b style="font-size:14px; color: #22c55e;">{curr_high:,.2f}</b>
                    </div>
                    <div style="padding-left: 3px; margin-top: 6px;">
                        <small style="opacity:0.4; font-size:9px; text-transform:uppercase;">Day Low</small><br>
                        <b style="font-size:14px; color: #ef4444;">{curr_low:,.2f}</b>
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
    def format_vol(n):
        if n >= 1e7: return f"{n/1e7:.2f}Cr"
        if n >= 1e5: return f"{n/1e5:.2f}L"
        if n >= 1e3: return f"{n/1e3:.1f}K"
        return f"{n:.0f}"

    @staticmethod
    def build_html_content(stock_data, idx_returns, val_data, nifty_info):
        summary, pe, forecast, v_table = val_data
        
        perf_map = {INDEX_TICKERS[k]: v for k, v in idx_returns.items() if k in INDEX_TICKERS}
        sorted_sectors = sorted(perf_map.items(), key=lambda x: x[1], reverse=True)

        html = f"""
        <style>
            .market-card {{ font-family: 'Inter', sans-serif; max-width: 950px; margin: auto; color: #1e293b; line-height: 1.4; }}
            .valuation-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
            .valuation-table th {{ background: #f1f5f9; text-align: left; padding: 8px 10px; border-bottom: 2px solid #e2e8f0; }}
            
            .sector-block {{ background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
            .sector-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px; }}
            .sector-header h3 {{ margin:0; font-size:16px; font-weight:700; }}
            .sector-ret {{ font-size:15px; font-weight:700; }}
            .vol-hint {{ font-size: 10px; color: #64748b; margin: 0 0 6px 0; font-style: italic; }}
            
            .stock-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
            .stock-table th {{ background: #f1f5f9; text-align: left; padding: 6px 8px; font-size: 10px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #e2e8f0; }}
            .stock-table td {{ padding: 5px 8px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }}
            .stock-table tr:hover td {{ background: #f8fafc; }}
            .stock-table tr:last-child td {{ border-bottom: none; }}
            .stock-table a {{ text-decoration: none; color: #2563eb; font-weight: 700; }}
            .stock-table .price {{ font-size: 13px; font-weight: 800; color: #0f172a; }}
            .stock-table .change {{ font-weight: 700; }}
            .stock-table .volx {{ font-weight: 700; font-size: 11px; padding: 2px 6px; border-radius: 4px; display: inline-block; }}
            .stock-table .vol-raw {{ font-size: 10px; color: #475569; }}
            .stock-table .tag {{ font-size: 9px; padding: 2px 5px; border-radius: 3px; font-weight: bold; text-transform: uppercase; }}
            
            .stock-table th:nth-child(1), .stock-table td:nth-child(1) {{ width: 80px; }}
            .stock-table th:nth-child(2), .stock-table td:nth-child(2) {{ width: 85px; }}
            .stock-table th:nth-child(3), .stock-table td:nth-child(3) {{ width: 65px; }}
            .stock-table th:nth-child(4), .stock-table td:nth-child(4) {{ width: 70px; }}
            .stock-table th:nth-child(5), .stock-table td:nth-child(5) {{ width: 65px; }}
            .stock-table th:nth-child(6), .stock-table td:nth-child(6) {{ width: 65px; }}
            .stock-table th:nth-child(7), .stock-table td:nth-child(7) {{ width: 70px; }}
            
            /* MOBILE: Horizontal scroll wrapper */
            @media (max-width: 640px) {{
                .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
                .stock-table {{ min-width: 520px; font-size: 11px; }}
                .stock-table th, .stock-table td {{ padding: 4px 6px; }}
                .stock-table .price {{ font-size: 12px; }}
                .stock-table a {{ font-size: 11px; }}
            }}
        </style>

        <div style="background:#f8fafc; padding:14px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:14px;">
            <h2 style="margin:0 0 8px 0; font-size:16px;">📊 Valuation Analytics</h2>
            <div style="display:flex; gap:20px; margin:8px 0; background:white; padding:10px 14px; border-radius:8px;">
                <div><small style="font-size:10px; color:#64748b;">CURRENT PE</small><br><b style="font-size:15px;">{pe}</b></div>
                <div><small style="font-size:10px; color:#64748b;">1Y FORECAST</small><br><b style="font-size:15px; color:#15803d;">{forecast}</b></div>
            </div>
            <p style="font-size:13px; margin:6px 0; line-height:1.5;">{summary}</p>
            {v_table}
        </div>
        """
        
        for sector, s_ret in sorted_sectors:
            if sector not in SECTOR_MAP: continue
            
            sector_stocks = []
            for t in SECTOR_MAP[sector]:
                stats = stock_data.get(t, {'price':0, 'change':0, 'rsi':50, 'vol_ratio':1.0, 'curr_vol':0, 'avg_vol':1})
                sector_stocks.append({'ticker': t, **stats})
            
            sorted_stocks = sorted(sector_stocks, key=lambda x: x['vol_ratio'], reverse=True)

            html += f"""<div class="sector-block">
                <div class="sector-header">
                    <h3>{sector}</h3>
                    <b class="sector-ret" style="color:{'#15803d' if s_ret > 0 else '#dc2626'}">{s_ret:+.2f}%</b>
                </div>
                <div class="vol-hint">💡 VolumeX = 20 Day Avg Volume Multiplier</div>
                
                <div class="table-wrap">
                <table class="stock-table">
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Price</th>
                            <th>Change</th>
                            <th>VolumeX</th>
                            <th>Today Vol</th>
                            <th>Avg Vol</th>
                            <th>Signal</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for s in sorted_stocks:
                t = s['ticker']
                ext_url = f"https://www.google.com/finance/quote/{t}:NSE"
                
                t_vol = ReportBuilder.format_vol(s['curr_vol'])
                a_vol = ReportBuilder.format_vol(s['avg_vol'])
                
                vol_val = float(s['vol_ratio'])
                if vol_val > 2.5:
                    volx_style = "background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa;"
                    volx_label = f"🔥 {vol_val:.2f}x"
                elif vol_val > 1.5:
                    volx_style = "color: #b45309;"
                    volx_label = f"📈 {vol_val:.2f}x"
                else:
                    volx_style = "color: #475569;"
                    volx_label = f"{vol_val:.2f}x"
                
                rsi_tag = '<span class="tag" style="background:#fee2e2; color:#b91c1c;">Overbought</span>' if s['rsi'] > 70 else \
                          ('<span class="tag" style="background:#dcfce7; color:#15803d;">Oversold</span>' if s['rsi'] < 30 else '—')

                html += f"""
                        <tr>
                            <td><a href="{ext_url}" target="_blank">{t}</a></td>
                            <td class="price">₹{s['price']:,.2f}</td>
                            <td class="change" style="color:{'#15803d' if s['change'] > 0 else '#dc2626'}">{s['change']:+.2f}%</td>
                            <td><span class="volx" style="{volx_style}">{volx_label}</span></td>
                            <td class="vol-raw">{t_vol}</td>
                            <td class="vol-raw">{a_vol}</td>
                            <td>{rsi_tag}</td>
                        </tr>"""
            
            html += """
                    </tbody>
                </table>
                </div>
            </div>"""
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
    
    # Helper for scalar extraction
    def safe_scalar(val):
        if hasattr(val, 'item'):
            return float(val.item())
        return float(val)
    
    # 2. Fetch Nifty 50 Data
    nifty_raw = yf.download('^NSEI', period='5d', interval='1d', auto_adjust=True)
    if nifty_raw.empty:
        print("❌ Error: Could not fetch Nifty data.")
        return

    # Safe scalar extraction
    n_close_today = safe_scalar(nifty_raw['Close'].iloc[-1])
    n_close_prev = safe_scalar(nifty_raw['Close'].iloc[-2])
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
