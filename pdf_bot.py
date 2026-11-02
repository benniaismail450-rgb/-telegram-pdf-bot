import os
import telebot
from flask import Flask

# --- 1. إعداد تطبيق Flask الخفيف لفتح البورت فوراً ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

# --- 2. كود بوت تيليجرام ---
TOKEN = "YOUR_BOT_TOKEN"  # استبدل هذا بتوكن البوت الخاص بك
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك! أرسل لي الصور وسأقوم بتحويلها إلى ملف PDF.")

# تشغيل البوت في الخلفية باستخدام Webhook أو Polling (سنستخدم Polling مع خيط منفصل لتشغيل Flask جنباً إلى جنب)
import threading
def run_bot():
    print("Bot is starting polling...")
    bot.infinity_polling()

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
