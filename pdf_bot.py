import os
import telebot
import img2pdf

# توكن البوت الجديد الخاص بتحويل الصور إلى PDF
TOKEN = '9189528366:AAE0LTM-26urghvNYXr7nagmrEfSNPJ3d3s'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! أرسل لي أي صورة وسأقوم بتحويلها فوراً إلى ملف PDF 📄✨")

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        # إخبار المستخدم بأن العمل جاري
        msg = bot.reply_to(message, "⏳ جاري تحويل الصورة إلى PDF...")
        
        # تحميل الصورة المرسلة بأعلى جودة متاحة
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "temp_image.jpg"
        pdf_path = "converted_document.pdf"
        
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # تحويل الصورة إلى PDF باستخدام مكتبة img2pdf
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(image_path))
        
        # إرسال ملف الـ PDF الناتج إلى المستخدم
        with open(pdf_path, 'rb') as pdf_file:
            bot.send_document(message.chat.id, pdf_file, caption="✨ تم تحويل الصورة إلى PDF بنجاح!")
        
        # حذف الملفات المؤقتة من السيرفر لتنظيف المساحة
        os.remove(image_path)
        os.remove(pdf_path)
        
    except Exception as e:
        bot.reply_to(message, f"عذراً، حدث خطأ أثناء التحويل: {e}")

# تشغيل البوت باستمرار
print("PDF Bot is running...")
bot.infinity_polling()
