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
## MODULE 3: HTML & SEO REPORT BUILDER
#############################################

class ReportBuilder:
    @staticmethod
    def get_seo_tags(change):
        return {
            'aioseo_title': f"Market Wrap: Nifty {change:+.2f}% | Sector Analysis & 170+ Stocks",
            'aioseo_description': f"Nifty ends at {change:+.2f}%. Full NSE analysis with RSI technicals, valuation forecasts, and institutional volume shockers."
        }

    @staticmethod
    def build_html_content(stock_data, idx_returns, val_data, nifty_info):
        summary, pe, forecast, v_table = val_data
        n_price, n_change = nifty_info
        
        perf_map = {INDEX_TICKERS[k]: v for k, v in idx_returns.items() if k in INDEX_TICKERS}
        sorted_sectors = sorted(perf_map.items(), key=lambda x: x[1], reverse=True)

        html = f"""
        <style>
            .market-card {{ font-family: 'Inter', -apple-system, sans-serif; max-width: 950px; margin: auto; color: #1e293b; line-height: 1.6; }}
            .header-box {{ background: #0f172a; color: white; padding: 50px 25px; border-radius: 24px; text-align: center; margin-bottom: 30px; }}
            .valuation-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
            .valuation-table th {{ background: #f1f5f9; text-align: left; padding: 12px; border-bottom: 2px solid #e2e8f0; }}
            .sector-block {{ background: white; border: 1px solid #e2e8f0; border-radius: 20px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .stock-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; margin-top: 20px; }}
            .stock-card {{ border: 1px solid #f1f5f9; padding: 12px; border-radius: 10px; font-size: 13px; background: #fff; }}
            .tag {{ font-size: 10px; padding: 2px 5px; border-radius: 4px; font-weight: bold; text-transform: uppercase; margin-right: 4px; }}
            .vol-label {{ font-size: 11px; color: #64748b; font-weight: 600; margin-top: 4px; display: block; }}
            a {{ text-decoration: none; color: #3b82f6; font-weight: 700; }}
        </style>
        <div class="market-card">
            <div class="header-box">
                <span style="font-size: 64px; font-weight: 800; display: block;">{n_price:,.2f}</span>
                <div style="font-size: 24px; color: {'#4ade80' if n_change > 0 else '#f87171'}; font-weight: 700;">
                    {'▲' if n_change > 0 else '▼'} {n_change:+.2f}%
                </div>
            </div>
            <div style="background:#f8fafc; padding:30px; border-radius:20px; border:1px solid #e2e8f0; margin-bottom:30px;">
                <h2 style="margin-top:0;">📊 Valuation Snapshot</h2>
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
            html += f"""<div class="sector-block">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #f1f5f9; padding-bottom:10px;">
                    <h3 style="margin:0; font-size:22px;">{sector}</h3>
                    <b style="font-size:20px; color:{'#16a34a' if s_ret > 0 else '#dc2626'}">{s_ret:+.2f}%</b>
                </div>
                <div class="stock-grid">"""
            for t in SECTOR_MAP[sector]:
                s = stock_data.get(t, {'price':0, 'change':0, 'rsi':50, 'vol_ratio':1.0})
                ext_url = f"https://www.google.com/finance/quote/{t}:NSE"
                int_url = f"{WP_URL.split('wp-json')[0]}?s={t}"
                rsi_tag = '<span class="tag" style="background:#fee2e2; color:#ef4444;">Overbought</span>' if s['rsi'] > 70 else \
                          ('<span class="tag" style="background:#dcfce7; color:#22c55e;">Oversold</span>' if s['rsi'] < 30 else '')
                vol_color = "#d97706" if s['vol_ratio'] > 2.0 else "#64748b"
                
                html += f"""
                <div class="stock-card">
                    <b><a href="{int_url}">{t}</a></b><br>
                    <div style="font-size:16px; font-weight:800; margin:4px 0;"><a href="{ext_url}" target="_blank" style="color:#1e293b;">₹{s['price']:,.2f}</a></div>
                    <div style="font-weight:700; color:{'#16a34a' if s['change'] > 0 else '#dc2626'}">{s['change']:+.2f}%</div>
                    <span class="vol-label" style="color:{vol_color}">Vol: {s['vol_ratio']:.2f}x</span>
                    <div style="margin-top:8px;">{rsi_tag}</div>
                </div>"""
            html += "</div></div>"
        return html + "</div>"

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
    engine = MarketDataEngine()
    val_data = engine.get_valuation_metrics()
    stock_stats = engine.get_bulk_stock_stats()
    
    idx_raw = yf.download(list(INDEX_TICKERS.keys()), period='5d')['Close'].dropna(axis=1)
    idx_returns = ((idx_raw.iloc[-1] / idx_raw.iloc[-2] - 1) * 100).dropna()
    n_price, n_change = idx_raw.iloc[-1]['^NSEI'], idx_returns['^NSEI']
    
    builder = ReportBuilder()
    html_content = builder.build_html_content(stock_stats, idx_returns, val_data, (n_price, n_change))
    seo_payload = builder.get_seo_tags(n_change)
    
    publisher = WordPressPublisher()
    post_title = f"Market Wrap {datetime.now().strftime('%d %b')}: Nifty {n_change:+.2f}% | Top Performance Sectors"
    
    if publisher.push_post(post_title, html_content, seo_payload):
        print(f"✅ Post Successful: {post_title}")
    else:
        print("❌ Posting Failed.")

if __name__ == "__main__":
    main()
