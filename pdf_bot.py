import os
import telebot
from flask import Flask, request
import img2pdf
from PIL import Image
import io

TOKEN = "9189528366:AAE0LTM-26urghvNYXr7nagmrEfSNPJ3d3s"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# رابط الـ Webhook الخاص بك على Render (سيتم ربطه تلقائياً)
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    else:
        return "Internal Server Error", 403

@app.route('/')
def home():
    return "Bot is alive and running!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك! أرسل لي الصور وسأقوم بتحويلها إلى ملف PDF.")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    try:
        bot.reply_to(message, "جاري معالجة الصورة وتحويلها إلى PDF...")
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        pdf_bytes = img2pdf.convert(downloaded_file)
        bot.send_document(message.chat.id, pdf_bytes, visible_file_name="converted_image.pdf")
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء المعالجة: {e}")

if __name__ == "__main__":
    # إزالة أي Webhook قديم وربط الرابط الجديد مباشرة بموقعك على Render
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
