import mplfinance as mpf
import time

def generate_trade_chart(df, trades):
    """
    Generate candle chart with SMC + trades
    """
    apds = []
    for trade in trades:
        apds.append(mpf.make_addplot([trade['entry']]*len(df), type='scatter', markersize=50, marker='^'))
    chart_file = f"charts/trade_{int(time.time())}.png"
    mpf.plot(df, type='candle', addplot=apds, volume=True, savefig=chart_file)
    return chart_file
