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

# معرف القناة الخاصة بك للاشتراك الإجباري
CHANNEL_USERNAME = "@bot1234569"

# قاموس مؤقت لتخزين مسارات الصور والمؤقتات لكل مستخدم
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

# دالة التحقق من اشتراك المستخدم في القناة
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        print(f"Error checking subscription: {e}")
    return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # فحص الاشتراك الإجباري
    if not check_subscription(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        btn_channel = telebot.types.InlineKeyboardButton("📢 اشترك في القناة", url="https://t.me/bot1234569")
        btn_check = telebot.types.InlineKeyboardButton("✅ لقد انضممت، تحقق", callback_data="check_sub")
        markup.add(btn_channel)
        markup.add(btn_check)
        
        bot.reply_to(message, "🚨 **عذراً يا إسماعيل!** لاستخدام هذا البوت، يجب عليك الانضمام إلى قناتنا أولاً:\n\n🔗 https://t.me/bot1234569", 
                     reply_markup=markup, parse_mode="Markdown")
        return

    bot.reply_to(message, "مرحباً بك يا إسماعيل! أرسل لي عدة صور دفعة واحدة وسأقوم بجمعها وترتيبها في ملف PDF واحد.")

# التعامل مع زر التحقق من الاشتراك
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_query(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "✅ شكراً لاشتراكك! يمكنك الآن استخدام البوت.")
        bot.send_message(call.id, "أهلاً بك مجدداً! أرسل لي الصور الآن لدمجها في ملف PDF.")
    else:
        bot.answer_callback_query(call.id, "❌ لم تقم بالانضمام للقناة بعد!", show_alert=True)

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    
    # التحقق من الاشتراك قبل استقبال الصور أيضاً
    if not check_subscription(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        btn_channel = telebot.types.InlineKeyboardButton("📢 اشترك في القناة", url="https://t.me/bot1234569")
        markup.add(btn_channel)
        bot.reply_to(message, "🚨 يجب عليك الاشتراك في القناة أولاً لتتمكن من إرسال الصور وتحويلها:\n\n🔗 https://t.me/bot1234569", reply_markup=markup)
        return

    chat_id = message.chat.id
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image = Image.open(io.BytesIO(downloaded_file)).convert('RGB')
        
        os.makedirs(f"temp_{chat_id}", exist_ok=True)
        img_path = f"temp_{chat_id}/{time.time()}.jpg"
        image.save(img_path, "JPEG")
        
        if chat_id not in user_images:
            user_images[chat_id] = []
        user_images[chat_id].append(img_path)
        
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
        
        images_list = sorted(user_images[chat_id])
        
        with open(f"output_{chat_id}.pdf", "wb") as f:
            f.write(img2pdf.convert(images_list))
            
        with open(f"output_{chat_id}.pdf", "rb") as f:
            bot.send_document(chat_id, f, visible_file_name="images_collection.pdf")
            
    except Exception as e:
        bot.send_message(chat_id, f"حدث خطأ أثناء الدمج: {e}")
        
    finally:
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
