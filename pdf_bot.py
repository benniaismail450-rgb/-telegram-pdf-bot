import os
import telebot
from flask import Flask, request
import img2pdf
from PIL import Image
import io
import time
import threading

TOKEN = "9189528366:AAE0LTM-26urghvNYXr7nagmrEfSNPJ3d3s"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# قاموس مؤقت لتخزين مسارات الصور لكل مستخدم حسب الـ Chat ID
user_images = {}
user_timers = {}

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
    bot.reply_to(message, "مرحباً بك! أرسل لي عدة صور دفعة واحدة وسأقوم بجمعها وترتيبها في ملف PDF واحد.")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    
    try:
        # تنزيل الصورة بأعلى دقة
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # فتح الصورة وتحويلها إلى صيغة RGB وحفظها مؤقتاً بصيغة PNG أو JPEG
        image = Image.open(io.BytesIO(downloaded_file)).convert('RGB')
        
        # إنشاء مجلد مؤقت للمستخدم إذا لمש يكن موجوداً
        os.makedirs(f"temp_{chat_id}", exist_ok=True)
        img_path = f"temp_{chat_id}/{time.time()}.jpg"
        image.save(img_path, "JPEG")
        
        # إضافة مسار الصورة لقائمة المستخدم
        if chat_id not in user_images:
            user_images[chat_id] = []
        user_images[chat_id].append(img_path)
        
        # إعادة ضبط المؤقت: الانتظار لمدة 3 ثوانٍ بعد آخر صورة لضمان وصول كل الصور الدفعة الواحدة
        if chat_id in user_timers:
            user_timers[chat_id].cancel()
            
        timer = threading.Timer(3.0, process_and_send_pdf, args=[chat_id, message])
        user_timers[chat_id] = timer
        timer.start()
        
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء استقبال الصورة: {e}")

def process_and_send_pdf(chat_id, message):
    if chat_id not in user_images or not user_images[chat_id]:
        return
        
    try:
        bot.send_message(chat_id, "⏳ جاري دمج الصور وتحويلها إلى ملف PDF واحد...")
        
        # ترتيب الصور حسب وقت إرسالها
        images_list = sorted(user_images[chat_id])
        
        # تحويل جميع الصور إلى ملف PDF واحد باستخدام img2pdf
        with open(f"output_{chat_id}.pdf", "wb") as f:
            f.write(img2pdf.convert(images_list))
            
        # إرسال ملف الـ PDF للمستخدم
        with open(f"output_{chat_id}.pdf", "rb") as f:
            bot.send_document(chat_id, f, visible_file_name="images_collection.pdf")
            
    except Exception as e:
        bot.send_message(chat_id, f"حدث خطأ أثناء الدمج: {e}")
        
    finally:
        # تنظيف الملفات المؤقتة وحذفها من الخادم
        if chat_id in user_images:
            for img_path in user_images[chat_id]:
                if os.path.exists(img_path):
                    os.remove(img_path)
            del user_images[chat_id]
            
        if os.path.exists(f"output_{chat_id}.pdf"):
            os.remove(f"output_{chat_id}.pdf")
            
        if chat_id in user_timers:
            del user_timers[chat_id]

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
