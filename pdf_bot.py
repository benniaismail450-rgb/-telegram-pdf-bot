import os
import telebot
from flask import Flask
import img2pdf
from PIL import Image
import io

# --- 1. إعداد تطبيق Flask الخفيف لفتح البورت فوراً ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

# --- 2. توكن البوت الصحيح الخاص بك ---
TOKEN = "9189528366:AAE0LTM-26urghvNYXr7nagmrEfSNPJ3d3s"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك! أرسل لي الصور (أو مجموعة صور) وسأقوم بتحويلها إلى ملف PDF.")

# معالجة الصور المرسلة من المستخدم
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    try:
        bot.reply_to(message, "جاري معالجة الصورة وتحويلها إلى PDF، ريثما أنتهي...")
        
        # الحصول على أعلى دقة للصورة المرسلة
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # حفظ الصورة مؤقتة أو معالجتها في الذاكرة
        image = Image.open(io.BytesIO(downloaded_file))
        
        # تحويل الصورة إلى PDF باستخدام img2pdf
        pdf_bytes = img2pdf.convert(downloaded_file)
        
        # إرسال ملف الـ PDF الناتج للمستخدم
        bot.send_document(message.chat.id, pdf_bytes, visible_file_name="converted_image.pdf")
        
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء المعالجة: {e}")

# تشغيل البوت في خلفية الكود باستخدام خيط منفصل (Thread)
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
