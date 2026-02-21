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

class HeroCardBuilder:
    @staticmethod
    def get_market_sentiment(change):
        """Generates punchy, irresistible SEO-optimized headlines based on daily move."""
        if change > 1.2:
            return "Bulls on Rampage! 🚀 Nifty Shatters Resistance"
        elif change > 0.3:
            return "Green Shoot Recovery 📈 Bulls Defend Key Levels"
        elif change >= -0.3 and change <= 0.3:
            return "Tug-of-War! ⚖️ Market Braces for Major Breakout"
        elif change < -1.2:
            return "Blood on D-Street! 🩸 Bears Aggressive as Support Fails"
        else:
            return "Bears in Control 🔻 Sellers Dominate the Session"

    @staticmethod
    def build_hero_card(nifty_df, change):
        """
        Creates a high-contrast Hero Card with OHLC and Sentiment.
        nifty_df: The yfinance dataframe for ^NSEI (Nifty 50)
        """
        # Get the last two days of data
        today = nifty_df.iloc[-1]
        yesterday = nifty_df.iloc[-2]
        
        points_change = today['Close'] - yesterday['Close']
        sentiment_headline = HeroCardBuilder.get_market_sentiment(change)
        
        # Color logic for UI
        brand_color = "#22c55e" if change > 0 else "#ef4444"
        bg_gradient = "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)"
        
        return f"""
        <div style="background: {bg_gradient}; color: white; padding: 40px 30px; border-radius: 24px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); margin-bottom: 40px; font-family: 'Inter', sans-serif;">
            
            <div style="text-transform: uppercase; letter-spacing: 2px; font-size: 13px; font-weight: 800; color: {brand_color}; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
                {sentiment_headline}
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 30px;">
                
                <div style="flex: 1; min-width: 250px;">
                    <span style="font-size: 16px; opacity: 0.6; font-weight: 600; display: block; margin-bottom: 5px;">NIFTY 50 INDEX</span>
                    <span style="font-size: 68px; font-weight: 900; line-height: 0.9; letter-spacing: -2px;">{today['Close']:,.2f}</span>
                    
                    <div style="margin-top: 15px; font-size: 26px; font-weight: 700; color: {brand_color};">
                        {'▲' if change > 0 else '▼'} {abs(change):.2f}% 
                        <span style="font-size: 16px; opacity: 0.8; font-weight: 500; color: white; margin-left: 12px; background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 8px;">
                            {points_change:+.2f} pts
                        </span>
                    </div>
                </div>
                
                <div style="flex: 1; min-width: 280px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; background: rgba(255,255,255,0.03); padding: 25px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="border-right: 1px solid rgba(255,255,255,0.1); padding-right: 15px;">
                        <small style="opacity:0.5; display:block; font-size:10px; text-transform:uppercase; margin-bottom:4px;">Prev Close</small>
                        <b style="font-size:17px; color: #94a3b8;">{yesterday['Close']:,.2f}</b>
                    </div>
                    <div style="padding-left: 5px;">
                        <small style="opacity:0.5; display:block; font-size:10px; text-transform:uppercase; margin-bottom:4px;">Open Price</small>
                        <b style="font-size:17px;">{today['Open']:,.2f}</b>
                    </div>
                    <div style="border-right: 1px solid rgba(255,255,255,0.1); padding-right: 15px; margin-top: 10px;">
                        <small style="opacity:0.5; display:block; font-size:10px; text-transform:uppercase; margin-bottom:4px;">Day High</small>
                        <b style="font-size:17px; color: #4ade80;">{today['High']:,.2f}</b>
                    </div>
                    <div style="padding-left: 5px; margin-top: 10px;">
                        <small style="opacity:0.5; display:block; font-size:10px; text-transform:uppercase; margin-bottom:4px;">Day Low</small>
                        <b style="font-size:17px; color: #f87171;">{today['Low']:,.2f}</b>
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

def main():
    # 1. Initialize Engines
    data_engine = MarketDataEngine()
    report_builder = ReportBuilder()
    hero_builder = HeroCardBuilder()
    publisher = WordPressPublisher()
    
    # 2. Fetch Market Data
    # Fetch Nifty 50 OHLC for Hero Card
    nifty_raw = yf.download('^NSEI', period='5d', interval='1d', auto_adjust=True)
    nifty_change = ((nifty_raw['Close'].iloc[-1] / nifty_raw['Close'].iloc[-2]) - 1) * 100
    
    # Fetch Sector Returns for Sorting
    idx_raw = yf.download(list(INDEX_TICKERS.keys()), period='5d')['Close'].dropna(axis=1)
    idx_returns = ((idx_raw.iloc[-1] / idx_raw.iloc[-2] - 1) * 100).dropna()
    
    # Fetch Watchlist Technicals & Valuation Scrape
    stock_stats = data_engine.get_bulk_stock_stats()
    val_metrics = data_engine.get_valuation_metrics() # (summary, pe, forecast, table)
    
    # 3. Assemble the Report Components
    # Build the Hero Card first
    hero_html = hero_builder.build_hero_card(nifty_raw, nifty_change)
    
    # Build the rest of the body (Valuation + Sector Grids)
    # Pass (nifty_price, nifty_change) as a tuple
    body_html = report_builder.build_html_content(
        stock_stats, 
        idx_returns, 
        val_metrics, 
        (nifty_raw['Close'].iloc[-1], nifty_change)
    )
    
    # Final Full Content (Hero + Body)
    full_html = hero_html + body_html
    
    # 4. SEO Payload
    seo_tags = report_builder.get_seo_tags(nifty_change)
    
    # 5. Execute Posting
    post_date = datetime.now().strftime('%d %b')
    post_title = f"India Market Wrap {post_date}: Nifty {nifty_change:+.2f}% | Sectoral Performance"
    
    if publisher.push_post(post_title, full_html, seo_tags):
        print(f"✅ Mission Accomplished! Post Live: {post_title}")
    else:
        print("❌ Posting Failed. Check API credentials or network.")

if __name__ == "__main__":
    main()
