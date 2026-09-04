"""
AudioScribe Telegram Bot
O'zbekcha, ruscha va inglizcha ovozli xabarlar va MP3 fayllarni matnga o'girib,
xulosa va muhim ma'lumotlarni ajratib beruvchi Telegram Bot.

O'rnatish:
pip install pyTelegramBotAPI google-genai requests
"""

import os
import json
import base64
import requests
import telebot

# --- SOZLAMALAR ---
# 1. @BotFather dan olingan Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKENINGIZNI_BU_YERGA_YOZING")

# 2. aistudio.google.com dan olingan bepul Gemini API kaliti
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "GEMINI_API_KEYINGIZNI_BU_YERGA_YOZING")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

SYSTEM_PROMPT = """
Sen professional audio tahlilchi va transkriptorsan.
Berilgan audioni diqqat bilan tingla. Audio o'zbek, rus yoki ingliz tilida (yoki aralash) bo'lishi mumkin.
Quyidagi vazifalarni bajar va FAQAT quyidagi JSON formatida javob qaytar:

{
  "language_detected": "uz",
  "transcription": "audiodagi barcha gaplarning to'liq va aniq matni (tinish belgilari bilan)",
  "summary": "audioning 2-4 gapli qisqa va lo'nda xulosasi",
  "key_points": ["asosiy fikr 1", "asosiy fikr 2"],
  "action_items": ["topshiriq yoki qilinishi kerak bo'lgan ish 1"],
  "entities": {
    "dates": ["aytilgan sanalar va vaqtlar"],
    "numbers_amounts": ["narxlar, summalar, raqamlar"],
    "people_contacts": ["ismlar, shaxslar, telefonlar"],
    "locations": ["manzillar, joylar"]
  }
}
"""

def analyze_audio_with_gemini(file_bytes, mime_type="audio/ogg"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    base64_data = base64.b64encode(file_bytes).decode("utf-8")
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64_data
                        }
                    },
                    {
                        "text": SYSTEM_PROMPT
                    }
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
    }
    
    response = requests.post(url, json=payload, timeout=90)
    response.raise_for_status()
    
    data = response.json()
    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    
    # JSON tozalash
    raw_text = raw_text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endsWith("```"):
        raw_text = raw_text[:-3]
        
    return json.loads(raw_text.strip())


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 **Assalomu alaykum!**\n\n"
        "Menga istalgan **ovozli xabar (voice)** yoki **MP3 audio** yuboring.\n"
        "Men uni:\n"
        "1. 📝 To'liq matnga o'girib beraman\n"
        "2. 📌 Qisqacha xulosa yozib beraman\n"
        "3. ✅ Topshiriqlar va sanalar/narxlarni ajratib beraman.\n\n"
        "🌐 *O'zbek, Rus va Ingliz tillarini tushunaman!*",
        parse_mode="Markdown"
    )


@bot.message_handler(content_types=['voice', 'audio', 'document'])
def handle_audio(message):
    try:
        status_msg = bot.reply_to(message, "⏳ Audio yuklab olinmoqda va AI tahlil qilmoqda...")
        
        file_id = None
        mime_type = "audio/ogg"
        
        if message.content_type == 'voice':
            file_id = message.voice.file_id
            mime_type = "audio/ogg"
        elif message.content_type == 'audio':
            file_id = message.audio.file_id
            mime_type = message.audio.mime_type or "audio/mp3"
        elif message.content_type == 'document' and (message.document.mime_type or "").startswith("audio/"):
            file_id = message.document.file_id
            mime_type = message.document.mime_type
        else:
            bot.edit_message_text("Iltimos, faqat ovozli xabar yoki audio fayl yuboring.", message.chat.id, status_msg.message_id)
            return

        # Faylni yuklab olish
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Gemini AI tahlili
        res = analyze_audio_with_gemini(downloaded_file, mime_type)
        
        # Natijani chiroyli xabar shaklida tayyorlash
        lang_names = {"uz": "O'zbekcha", "ru": "Ruscha", "en": "Inglizcha", "mixed": "Aralash"}
        detected_lang = lang_names.get(res.get("language_detected", "uz"), res.get("language_detected", "uz"))
        
        text_reply = f"🌐 **Til:** {detected_lang}\n\n"
        text_reply += f"📌 **QISQACHA XULOSA:**\n{res.get('summary', '')}\n\n"
        
        # Topshiriqlar
        action_items = res.get("action_items", [])
        if action_items:
            text_reply += "✅ **TOPSHIRIQLAR VA VAZIFALAR:**\n"
            for item in action_items:
                text_reply += f"• {item}\n"
            text_reply += "\n"
            
        # Asosiy faktlar
        key_points = res.get("key_points", [])
        if key_points:
            text_reply += "💡 **ASOSIY FIKRLAR:**\n"
            for point in key_points:
                text_reply += f"• {point}\n"
            text_reply += "\n"
            
        # Entities (sanalar, raqamlar)
        entities = res.get("entities", {})
        dates = entities.get("dates", [])
        numbers = entities.get("numbers_amounts", [])
        people = entities.get("people_contacts", [])
        
        if dates or numbers or people:
            text_reply += "🔍 **AJRATIB OLINGAN MA'LUMOTLAR:**\n"
            if dates:
                text_reply += f"🗓 Sanalar: {', '.join(dates)}\n"
            if numbers:
                text_reply += f"💰 Narxlar/Summalar: {', '.join(numbers)}\n"
            if people:
                text_reply += f"👤 Shaxslar: {', '.join(people)}\n"
            text_reply += "\n"
            
        text_reply += f"📝 **TO'LIQ TRANSKRIPSIYA:**\n{res.get('transcription', '')}"
        
        # Telegram 4096 belgi limitini hisobga olish
        if len(text_reply) > 4000:
            bot.edit_message_text(text_reply[:4000], message.chat.id, status_msg.message_id, parse_mode="Markdown")
            bot.send_message(message.chat.id, text_reply[4000:], parse_mode="Markdown")
        else:
            bot.edit_message_text(text_reply, message.chat.id, status_msg.message_id, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling()
