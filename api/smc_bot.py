import os
from dotenv import load_dotenv
import yfinance as yf
import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# ---------------- CONFIG ----------------
load_dotenv()  # Load .env variables locally
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # Used if sending directly to group
TIMEFRAME = "15m"  # Intraday candle timeframe
DAYS = "7d"       # Lookback period for chart

bot = Bot(TOKEN)

# List of indices (display name: yfinance ticker)
INDICES = {
    "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK",
    "Sensex": "^BSESN",
    "Nifty IT": "^CNXIT"
}

# ---------------- /start COMMAND ----------------
def start(update: Update, context):
    keyboard = [[InlineKeyboardButton(name, callback_data=code)] for name, code in INDICES.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Select an index:", reply_markup=reply_markup)

# ---------------- CALLBACK HANDLER ----------------
def button(update: Update, context):
    query = update.callback_query
    query.answer()
    ticker = query.data

    # Fetch data from yfinance
    df = yf.download(ticker, period=DAYS, interval=TIMEFRAME)
    if df.empty:
        query.message.reply_text(f"No data found for {ticker}")
        return

    # Generate candlestick chart
    plt.figure(figsize=(10,5))
    plt.plot(df['Close'], label='Close Price', color='blue')
    plt.fill_between(df.index, df['Close'], alpha=0.1)
    plt.title(f"{ticker} Price Chart ({TIMEFRAME})")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.grid(True)
    plt.legend()
    chart_file = f"{ticker.replace('^','')}_chart.png"
    plt.savefig(chart_file)
    plt.close()

    # Prepare summary message
    last_price = df['Close'].iloc[-1]
    volume = df['Volume'].iloc[-1]
    high = df['High'].iloc[-1]
    low = df['Low'].iloc[-1]
    msg = (
        f"📊 {ticker} ({TIMEFRAME})\n"
        f"Last Price: {last_price:.2f}\n"
        f"High: {high:.2f} | Low: {low:.2f}\n"
        f"Volume: {volume}"
    )

    # Send chart + message
    query.message.reply_photo(photo=open(chart_file, "rb"), caption=msg)

# ---------------- MAIN FUNCTION ----------------
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
