import asyncio
import datetime
import time
from utils.fetch_data import fetch_option_chain, fetch_option_price
from utils.smc import smc_signal, generate_trades
from utils.charting import generate_trade_chart
from utils.alerts import send_alert

# Symbols to monitor
OPTION_SYMBOLS = {
    "Nifty50": "^NSEI",
    "BankNifty": "^NSEBANK",
    "Sensex": "^BSESN",
    "Finnifty": "^NSEFINNIFTY",
    "MidcapNifty": "^NSEMDCP"
}

# Settings
MAX_DAILY_TRADES = 10
TRADE_INTERVAL = 300  # seconds, 5 minutes
PRE_EXPIRY_WARNING_HOURS = 2

# Daily logs
sent_trades = []
failed_trades = []
cancelled_trades = []
successful_trades = []

# ------------------ Pre-entry validation with dynamic strike ------------------
def validate_trade(trade, df_smc):
    strikes_available = df_smc['Strike'].unique()
    if trade['strike'] in strikes_available:
        return True, trade
    # Closest strike adjustment
    closest_strike = min(strikes_available, key=lambda x: abs(x - trade['strike']))
    adjusted_trade = trade.copy()
    adjusted_trade['strike'] = closest_strike
    return False, adjusted_trade

# ------------------ Fetch and send trades ------------------
async def fetch_and_send_trades():
    daily_count = {symbol: 0 for symbol in OPTION_SYMBOLS}
    while True:
        for name, symbol in OPTION_SYMBOLS.items():
            if daily_count[name] >= MAX_DAILY_TRADES:
                continue
            df = fetch_option_chain(symbol)
            if df is None:
                continue
            df_smc = smc_signal(df)
            trades = generate_trades(df_smc, name, max_trades=MAX_DAILY_TRADES)
            for trade in trades:
                if daily_count[name] >= MAX_DAILY_TRADES:
                    break

                # Pre-entry validation + dynamic strike
                is_valid, trade = validate_trade(trade, df_smc)
                if not is_valid:
                    send_alert(f"⚠️ Trade Adjusted ⚠️\n"
                               f"Original Strike: {trade['original_strike']} -> Adjusted Strike: {trade['strike']}\n"
                               f"{trade['direction']} | Expiry: {trade['expiry']}")
                    cancelled_trades.append(trade)

                # Generate chart and send alert
                chart_file = generate_trade_chart(df_smc, [trade])
                msg = (
                    f"🆕 New Trade Alert ({name}) 🆕\n"
                    f"{trade['direction']} | Strike: {trade['strike']}\n"
                    f"Entry: {trade['entry']} | SL: {trade['SL']}\n"
                    f"TP1: {trade['TP1']} | TP2: {trade['TP2']}\n"
                    f"Expiry: {trade['expiry']} ⚠️ Trade on your own risk"
                )
                send_alert(msg, chart_file=chart_file)
                trade['status'] = 'Sent'
                sent_trades.append(trade)
                daily_count[name] += 1
        await asyncio.sleep(TRADE_INTERVAL)

# ------------------ Monitor sent trades ------------------
async def monitor_sent_trades():
    while True:
        now = datetime.datetime.now()
        for trade in sent_trades[:]:
            expiry_dt = datetime.datetime.strptime(trade['expiry'], "%Y-%m-%d")
            hours_to_expiry = (expiry_dt - now).total_seconds() / 3600

            # Expiry monitoring
            if hours_to_expiry <= 0:
                send_alert(f"❌ Trade Expired ❌\n{trade['direction']} {trade['strike']} | Expired")
                trade['status'] = 'Expired'
                sent_trades.remove(trade)
                cancelled_trades.append(trade)
                continue
            elif 0 < hours_to_expiry <= PRE_EXPIRY_WARNING_HOURS:
                send_alert(f"⏰ Expiry Warning ⏰\n{trade['direction']} {trade['strike']} | Expires in {int(hours_to_expiry)}h")

            # Price monitoring
            price = fetch_option_price(trade['strike'], trade['direction'])
            if price >= trade['TP2']:
                send_alert(f"✅ Trade Success ✅\n{trade['direction']} {trade['strike']} 🎯 TP2 Hit")
                trade['status'] = 'Completed'
                successful_trades.append(trade)
                sent_trades.remove(trade)
            elif price >= trade['TP1']:
                send_alert(f"✅ Trade Progress ✅\n{trade['direction']} {trade['strike']} 🎯 TP1 Hit")
                trade['status'] = 'Active'
            elif price <= trade['SL']:
                send_alert(f"❌ Trade Failed ❌\n{trade['direction']} {trade['strike']} 🔴 Hit SL")
                trade['status'] = 'Failed'
                failed_trades.append(trade)
                sent_trades.remove(trade)
            elif trade['status'] == 'Sent' and abs(price - trade['entry']) < 0.1:
                send_alert(f"🚀 Trade Entered 🚀\n{trade['direction']} {trade['strike']} 🟢")
                trade['status'] = 'Active'
        await asyncio.sleep(60)

# ------------------ Daily summary ------------------
async def send_daily_summary():
    while True:
        now = datetime.datetime.now()
        if now.hour == 17 and now.minute == 30:
            msg = (
                f"📊 Daily Trade Summary 📊\n"
                f"Total Trades Sent: {len(sent_trades) + len(successful_trades) + len(failed_trades) + len(cancelled_trades)}\n"
                f"✅ Successful Trades: {len(successful_trades)}\n"
                f"❌ Failed Trades: {len(failed_trades)}\n"
                f"⚠️ Cancelled Trades: {len(cancelled_trades)}\n"
            )
            send_alert(msg)
            successful_trades.clear()
            failed_trades.clear()
            cancelled_trades.clear()
        await asyncio.sleep(60)

# ------------------ Main loop ------------------
async def main_loop():
    await asyncio.gather(
        fetch_and_send_trades(),
        monitor_sent_trades(),
        send_daily_summary()
    )

if __name__ == "__main__":
    asyncio.run(main_loop())
