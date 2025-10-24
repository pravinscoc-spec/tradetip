import os
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

def send_alert(msg, chart_file=None):
    try:
        if chart_file:
            bot.send_photo(chat_id=CHAT_ID, photo=open(chart_file, "rb"), caption=msg)
        else:
            bot.send_message(chat_id=CHAT_ID, text=msg)
        print(f"[Sent] {msg.splitlines()[0]}")
    except Exception as e:
        print(f"[Error] Sending alert: {e}")
