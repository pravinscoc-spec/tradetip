import yfinance as yf

def fetch_option_chain(symbol):
    try:
        df = yf.download(symbol, period="7d", interval="5m", progress=False)
        if df.empty:
            return None
        # Add mock 'Strike' column if options chain not present
        if 'Strike' not in df.columns:
            df['Strike'] = df['Close'].round(-2)  # approximate strike
        return df
    except Exception as e:
        print(f"[Error] Fetching option chain for {symbol}: {e}")
        return None

def fetch_option_price(strike, direction):
    # Mock price fetching; integrate Angel One API for live data
    # For demo purposes, return a random price near strike
    import random
    return strike + random.randint(-20, 20)
