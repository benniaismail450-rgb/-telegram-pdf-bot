import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot

# --- 1. تشغيل بوت تيليجرام في خلفية الكود (Thread منفصل) ---
TOKEN = "YOUR_BOT_TOKEN"  # استبدل هذا بتوكن البوت الخاص بك
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك! أرسل لي الصور وسأقوم بتحويلها إلى ملف PDF.")

def run_bot():
    print("Bot is starting polling...")
    bot.infinity_polling()

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

# --- 2. خادم الويب في العملية الرئيسية ليتم رصد البورت فوراً بواسطة Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Web server running on port {port}")
    server.serve_forever()
