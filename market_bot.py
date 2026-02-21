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

# --- MARKET STRUCTURE ---
SECTOR_MAP = {
    'Nifty Bank': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK', 'INDUSINDBK', 'BANKBARODA', 'PNB', 'IDFCFIRSTB', 'FEDERALBNK'],
    'IT Services': ['TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM', 'LTIM', 'PERSISTENT', 'COFORGE', 'MPHASIS', 'KPITTECH'],
    'Automobile': ['M&M', 'MARUTI', 'TATAMOTORS', 'BAJAJ-AUTO', 'EICHERMOT', 'TVSMOTOR', 'HEROMOTOCO', 'ASHOKLEY', 'MRF', 'BALKRISIND'],
    'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'GODREJCP', 'DABUR', 'MARICO', 'VBL', 'COLPAL', 'TATACONSUM'],
    'Metals': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'JINDALSTEL', 'VEDL', 'NMDC', 'SAIL', 'NATIONALUM', 'APLAPOLLO', 'RATNAMANI'],
    'Pharma': ['SUNPHARMA', 'CIPLA', 'DRREDDY', 'LUPIN', 'AUROPHARMA', 'ZYDUSLIFE', 'DIVISLAB', 'ALKEM', 'TORNTPHARM', 'ABBOTT'],
    'Energy': ['RELIANCE', 'NTPC', 'ONGC', 'POWERGRID', 'BPCL', 'ADANIGREEN', 'TATAPOWER', 'IOC', 'GAIL', 'ADANIENSOL'],
    'Financial Services': ['BAJFINANCE', 'HDFCBANK', 'ICICIBANK', 'BAJAJFINSV', 'CHOLAFIN', 'REC', 'PFC', 'SHRIRAMFIN', 'SBILIFE', 'HDFCLIFE'],
    'PSU Bank': ['SBIN', 'BANKBARODA', 'CANBK', 'UNIONBANK', 'IOB', 'PNB', 'INDIANB', 'BANKINDIA', 'UCOBANK', 'CENTRALBK'],
    'Realty': ['DLF', 'LODHA', 'GODREJPROP', 'OBEROIRLTY', 'PRESTIGE', 'PHOENIXLTD', 'BRIGADE', 'SOBHA', 'SIGNATURE', 'SUNTECK'],
    'Media': ['ZEEL', 'SUNTV', 'PVRINOX', 'NETWORK18', 'TV18BRDCST', 'NAZARA', 'DISHTV', 'HATHWAY', 'SAREGMAPA', 'TIPSINDLTD'],
    'Consumption': ['ITC', 'HINDUNILVR', 'TITAN', 'ASIANPAINT', 'NESTLEIND', 'TRENT', 'DMART', 'ZOMATO', 'BRITANNIA', 'PAGEIND'],
    'Infrastructure': ['RELIANCE', 'LT', 'BHARTIARTL', 'NTPC', 'ADANIPORTS', 'ULTRACEMCO', 'ONGC', 'GRASIM', 'IIFL', 'POWERGRID'],
    'PSE': ['NTPC', 'ONGC', 'POWERGRID', 'COALINDIA', 'BEL', 'HAL', 'BPCL', 'IOC', 'PFC', 'REC'],
    'CPSE': ['NTPC', 'ONGC', 'POWERGRID', 'COALINDIA', 'BEL', 'NHPC', 'SJVN', 'NBCC', 'OIL', 'COCHINSHIP'],
    'Commodities': ['RELIANCE', 'TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'NTPC', 'ONGC', 'AMBUJACEM', 'GRASIM', 'VEDL', 'COALINDIA'],
    'Services': ['LT', 'ADANIPORTS', 'APOLLOHOSP', 'HDFCLIFE', 'SBILIFE', 'TRENT', 'INDIGO', 'VBL', 'TATACOMM', 'GMRINFRA']
}

INDEX_TICKERS = {'^NSEI': 'NIFTY 50', '^NSEBANK': 'Nifty Bank', '^CNXIT': 'IT Services', '^CNXAUTO': 'Automobile', '^CNXFMCG': 'FMCG', '^CNXMETAL': 'Metals', '^CNXPHARMA': 'Pharma', '^CNXENERGY': 'Energy', '^CNXREALTY': 'Realty', '^CNXINFRA': 'Infrastructure', '^CNXFIN': 'Financial Services', '^CNXPSUBANK': 'PSU Bank', '^CNXMEDIA': 'Media', '^CNXCONSUMP': 'Consumption', '^CNXPSE': 'PSE', '^CNXCPSE': 'CPSE', '^CNXCOMMOD': 'Commodities', '^CNXSERVICE': 'Services'}

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
###### MODULE 3.1: THE SEO HERO CARD (DYNAMIC UI)
#############################################
class HeroCardBuilder:
    @staticmethod
    def get_market_sentiment(change):
        """Generates punchy, irresistible SEO-optimized headlines."""
        if change > 1.0:
            return "Bulls on Rampage! 🚀 Nifty Shatters Resistance"
        elif change > 0:
            return "Green Shoot Recovery 📈 Bulls Defend Key Levels"
        elif change < -1.0:
            return "Blood on D-Street! 🩸 Bears Aggressive as Support Fails"
        else:
            return "Tug-of-War! ⚖️ Market Braces for Major Breakout"

    @staticmethod
    def build_hero_card(nifty_data, change):
        """
        Creates the high-info Hero Card showing OHLC and Yesterday's Close.
        nifty_data is the full yf dataframe for ^NSEI
        """
        curr = nifty_data.iloc[-1]
        prev_close = nifty_data.iloc[-2]['Close']
        
        sentiment_headline = HeroCardBuilder.get_market_sentiment(change)
        
        # UI color logic
        brand_color = "#22c55e" if change > 0 else "#ef4444"
        bg_gradient = "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)"
        
        return f"""
        <div style="background: {bg_gradient}; color: white; padding: 40px 30px; border-radius: 24px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); margin-bottom: 40px; font-family: 'Inter', sans-serif;">
            <div style="text-transform: uppercase; letter-spacing: 2px; font-size: 14px; font-weight: 700; color: {brand_color}; margin-bottom: 10px;">
                {sentiment_headline}
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 20px;">
                <div>
                    <span style="font-size: 18px; opacity: 0.7; display: block;">NIFTY 50 INDEX</span>
                    <span style="font-size: 64px; font-weight: 900; line-height: 1;">{curr['Close']:,.2f}</span>
                    <div style="margin-top: 10px; font-size: 24px; font-weight: 700; color: {brand_color};">
                        {'▲' if change > 0 else '▼'} {change:+.2f}% 
                        <span style="font-size: 16px; opacity: 0.8; font-weight: 400; color: white; margin-left: 10px;">
                            ({curr['Close'] - prev_close:+.2f} pts)
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
                        <b style="font-size:16px;">{curr['Open']:,.2f}</b>
                    </div>
                    <div style="border-right: 1px solid rgba(255,255,255,0.1); padding-right: 15px;">
                        <small style="opacity:0.6; display:block; font-size:11px; text-transform:uppercase;">Day High</small>
                        <b style="font-size:16px; color: #4ade80;">{curr['High']:,.2f}</b>
                    </div>
                    <div>
                        <small style="opacity:0.6; display:block; font-size:11px; text-transform:uppercase;">Day Low</small>
                        <b style="font-size:16px; color: #f87171;">{curr['Low']:,.2f}</b>
                    </div>
                </div>
            </div>
        </div>
        """

#############################################
## MODULE 4: WORDPRESS PUBLISHER
#############################################

class WordPressPublisher:
    @staticmethod
    def push_post(title, content, seo_data):
        auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
        payload = {
            'title': title, 'content': content, 'status': 'publish', 'categories': [CATEGORY_ID],
            **seo_data
        }
        res = requests.post(WP_URL, headers=headers, json=payload)
        return res.status_code == 201

#############################################
## MODULE 5: MAIN EXECUTION FLOW
#############################################

def main():
    """
    Main execution flow for the India Market Bot.
    Coordinates Data Extraction -> UI Generation -> Publication.
    """
    print(f"🚀 Starting Market Wrap execution for {datetime.now().strftime('%Y-%m-%d')}...")

    # 1. INITIALIZE ALL MODULE ENGINES
    data_engine = MarketDataEngine()
    hero_builder = HeroCardBuilder()
    report_builder = ReportBuilder()
    publisher = WordPressPublisher()
    
    # 2. FETCH NIFTY 50 OHLC (For the Irresistible Hero Card)
    # We fetch 5 days to ensure we have enough data for today vs yesterday comparison
    print("📥 Fetching Nifty 50 OHLC and technicals...")
    nifty_raw = yf.download('^NSEI', period='5d', interval='1d', auto_adjust=True)
    if nifty_raw.empty:
        print("❌ Error: Could not fetch Nifty data. Aborting.")
        return

    nifty_close_today = nifty_raw['Close'].iloc[-1]
    nifty_close_prev = nifty_raw['Close'].iloc[-2]
    nifty_change_pct = ((nifty_close_today / nifty_close_prev) - 1) * 100
    
    # 3. FETCH SECTORAL DATA (For Top Gainers Sorting)
    print("📥 Analyzing sectoral performance...")
    idx_raw = yf.download(list(INDEX_TICKERS.keys()), period='5d')['Close'].dropna(axis=1)
    idx_returns = ((idx_raw.iloc[-1] / idx_raw.iloc[-2] - 1) * 100).dropna()
    
    # 4. FETCH 170+ STOCK WATCHLIST & VALUATIONS
    print("📥 Fetching watchlist technicals and valuation metrics...")
    stock_stats = data_engine.get_bulk_stock_stats()
    val_metrics = data_engine.get_valuation_metrics() # Returns: (summary, pe, forecast, table)
    
    # 5. ASSEMBLE THE HTML REPORT
    print("🎨 Building the UI components...")
    # Generate the Hero Dashboard
    hero_html = hero_builder.build_hero_card(nifty_raw, nifty_change_pct)
    
    # Generate the Body (Valuation Analytics + Sorted Sector Grids)
    body_html = report_builder.build_html_content(
        stock_stats, 
        idx_returns, 
        val_metrics, 
        (nifty_close_today, nifty_change_pct)
    )
    
    # Merge Components
    final_post_html = hero_html + body_html
    
    # 6. CONFIGURE SEO METADATA (AIOSEO)
    print("🔍 Optimizing for SEO...")
    seo_payload = report_builder.get_seo_tags(nifty_change_pct)
    
    # 7. EXECUTE PUBLICATION
    post_date = datetime.now().strftime('%d %b %Y')
    post_title = f"India Market Wrap {post_date}: Nifty {nifty_change_pct:+.2f}% | Sectoral Deep-Dive"
    
    print(f"📤 Uploading to WordPress: {post_title}...")
    if publisher.push_post(post_title, final_post_html, seo_payload):
        print(f"✅ SUCCESS: Post is live at {WP_URL}")
    else:
        print("❌ FAILURE: Could not publish post. Check API credentials or Category ID.")

# --- THE TRIGGER ---
if __name__ == "__main__":
    main()
