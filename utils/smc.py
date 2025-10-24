import pandas as pd

def smc_signal(df):
    # Add mock SMC signals; implement proper SMC logic here
    df['SMC'] = "Neutral"
    # Example: if last candle bullish -> mark SMC Bull
    if df['Close'].iloc[-1] > df['Open'].iloc[-1]:
        df['SMC'].iloc[-1] = "Bull"
    else:
        df['SMC'].iloc[-1] = "Bear"
    return df

def generate_trades(df, name, max_trades=5):
    trades = []
    for i in range(min(max_trades, len(df))):
        row = df.iloc[-(i+1)]
        direction = "CALL" if row['SMC'] == "Bull" else "PUT"
        trade = {
            "direction": direction,
            "strike": row['Strike'],
            "original_strike": row['Strike'],
            "entry": row['Close'],
            "SL": row['Close'] - 20 if direction == "CALL" else row['Close'] + 20,
            "TP1": row['Close'] + 50 if direction == "CALL" else row['Close'] - 50,
            "TP2": row['Close'] + 100 if direction == "CALL" else row['Close'] - 100,
            "expiry": (pd.Timestamp.now() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        }
        trades.append(trade)
    return trades
