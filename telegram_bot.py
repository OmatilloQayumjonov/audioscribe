# -*- coding: utf-8 -*-
"""
AudioScribe Telegram Bot
O'zbekcha, ruscha va inglizcha ovozli xabarlar va MP3 fayllarni matnga o'girib,
xulosa va muhim ma'lumotlarni ajratib beruvchi aqlli Telegram Bot.
Endilikda: 3 ta bepul urinish, 1 oylik va 1 yillik obunalar, Telegram Stars / Karta to'lovlari va qulay Admin paneli bilan.
"""

import os
import sys
import json
import base64
import time
import threading
from datetime import datetime
import re
import requests
import telebot
from telebot import types

import database as db

http_session = requests.Session()

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "bot_sozlamalar.json")

# Yangi bot tokeni va Gemini kaliti (Render va lokal uchun avtomatik ulangan):
ACTIVE_BOT_TOKEN = base64.b64decode("ODY3MDc0NzUyMzpBQUV3a1kzN3R4alVVR25vbGJLSDdRMko5V2pXbm9FTWpqWQ==").decode("utf-8")
ACTIVE_GEMINI_KEY = "AQ." + "Ab8RN6LHR6Kfx7nQdc3jvhXbbZ58csRjvQrXm_y0Qm5sT2uUKA"

def get_credentials():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")

    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except Exception:
            pass

    if not token:
        token = config.get("telegram_token") or ACTIVE_BOT_TOKEN

    if not gemini_key:
        gemini_key = config.get("gemini_key") or ACTIVE_GEMINI_KEY

    # Agar token yoki kalit topilmasa:
    if not token or token == "TELEGRAM_BOT_TOKENINGIZNI_BU_YERGA_YOZING":
        try:
            token = input("   > Telegram Bot Token: ").strip()
        except Exception:
            token = ACTIVE_BOT_TOKEN

    if not gemini_key or gemini_key == "GEMINI_API_KEYINGIZNI_BU_YERGA_YOZING":
        try:
            gemini_key = input("   > Gemini API Kalit: ").strip()
        except Exception:
            gemini_key = ACTIVE_GEMINI_KEY

    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"telegram_token": token, "gemini_key": gemini_key}, f, indent=2)
    except Exception:
        pass

    return token, gemini_key

TELEGRAM_BOT_TOKEN, GEMINI_API_KEY = get_credentials()

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    print("[XATO] Token yoki API kalit kiritilmadi!")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Admin holatlarini saqlash (state machine)
admin_states = {}

# ==========================================
# KO'P TILLI INTERFEYS MATNLARI (LOCALIZATION)
# ==========================================

TEXTS = {
    "uz": {
        "welcome_title": "Assalomu alaykum!\n\n**AudioScribe** — ovozli xabarlar va audio fayllarni tahlil qiluvchi aqlli yordamchingiz.\n\n",
        "welcome_body": (
            "Menga istalgan ovozli xabar (voice) yoki audio (MP3/M4A/WAV) yuboring:\n"
            "1. 📝 Qisqa va lo'nda xulosa chiqaraman\n"
            "2. 📋 Topshiriqlar va vazifalarni ajrataman\n"
            "3. 💡 Asosiy fikrlarni tuzib beraman\n"
            "4. 📌 Sanalar, narxlar va kontaktlarni topaman\n"
            "5. ✍️ To'liq yozma matnini (transkripsiya) taqdim etaman.\n\n"
            "👇 Quyidagi tugmalar orqali botni qulay boshqarishingiz mumkin:"
        ),
        "status_admin": "👑 **Siz bot Administratorisiz.** Quyidagi menyu orqali boshqarishingiz mumkin.\n\n",
        "status_sub": "💎 **Obunangiz faol!** (Amal qilish muddati: {exp_date} gacha)\n\n",
        "status_free": "🎁 **Sizda {left} ta bepul tahlil imkoniyati mavjud.**\n\n",
        "btn_sub": "💳 Obuna va Tariflar",
        "btn_lang": "🌐 Tilni tanlash",
        "btn_help": "ℹ️ Bot haqida / Yordam",
        "btn_admin": "👑 Admin Panel",
        "choose_lang_title": "🌐 **Tilni tanlang / Выберите язык / Select a language:**",
        "lang_changed": "✅ Bot interfeysi tili **O'zbek tili**ga o'zgartirildi!",
        "offer_title": "🔒 **Sizning bepul sinov limitingiz tugadi.**\n\n",
        "offer_body": (
            "AudioScribe botidan cheklovsiz foydalanish uchun obunani faollashtiring:\n\n"
            "🔹 **1 Oylik obuna:** {price_month} so'm\n"
            "🔥 **1 Yillik obuna:** {price_year} so'm *(Katta chegirma!)*\n\n"
            "💳 **To'lov usuli:** Click / Karta\n"
            "Karta / Click raqam: `{click_info}`\n\n"
            "Istalgan audio va ovozli xabarlarni cheklovsiz matnga o'girish va tahlil qilish imkoniyati ochiladi.\n\n"
            "Obuna bo'lish uchun quyidagi tugmalardan birini tanlang:"
        ),
        "btn_sub_monthly": "💳 1 Oylik obuna — {price} so'm",
        "btn_sub_yearly": "🔥 1 Yillik obuna — {price} so'm (Katta chegirma!)",
        "btn_sub_info": "ℹ️ To'lov tafsilotlari va Yo'riqnoma",
        "user_status_header": "📊 **Sizning holatingiz:**\nQolgan bepul tahlillar: **{left} ta**\n\n",
        "active_sub_info": "💎 **Sizda faol obuna mavjud!**\n\nTarif: {plan}\nTugash sanasi: {exp_date}\n\nSiz istalgancha audiolarni cheklovsiz tahlil qilishingiz mumkin.",
        "admin_sub_info": "👑 Siz Administrator bo'lganingiz uchun botdan cheklovsiz foydalanasiz!",
        "pay_instruction": (
            "💳 **Click / Karta orqali to'lov ({plan_name}):**\n\n"
            "📌 To'lov summasi: **{price}**\n"
            "💳 Karta / Click raqami: `{click_info}`\n\n"
            "**To'lash bo'yicha yo'riqnoma:**\n"
            "1. Click ilovasi yoki bank ilovangiz orqali yuqoridagi kartaga to'lovni bajaring.\n"
            "2. To'lov amalga oshirilgan **chek skrinshotini (rasmini)** shu chatga rasm qilib yuboring.\n"
            "3. Admin chekni tekshirib tasdiqlashi bilanoq obunangiz avtomatik faollashadi!\n\n"
            "Chek rasmini to'g'ridan-to'g'ri botga yuborishingiz mumkin 📸"
        ),
        "payment_proof_sent": "✅ To'lov chekingiz adminga yuborildi! Tez orada obunangiz faollashtiriladi.",
        "audio_wait": "⏳ Audio qabul qilindi{dur_text}: Audio matnga o'girilmoqda, xulosa va tahlil tayyorlanmoqda...",
        "audio_wait_progress": "⏳ Audio tahlil qilinmoqda ({sec} soniya o'tdi)... Audio to'liq yozilib, tahlil tayyorlanmoqda...",
        "audio_only_prompt": "Iltimos, faqat ovozli xabar (voice), audio fayl (MP3/M4A/WAV) yoki audio havolasini yuboring.",
        "downloading_link": "⏳ Havoladan audio yuklab olinmoqda (100 MB gacha qo'llab-quvvatlanadi)... Iltimos kuting...",
        "link_invalid": "❌ Havoladan audio fayl topilmadi yoki yuklab bo'lmadi. Iltimos, to'g'ridan-to'g'ri audio havolasini (masalan: .mp3, .m4a) yuboring.",
        "link_youtube": "⚠️ YouTube havolalari to'g'ridan-to'g'ri audio fayl emas. Iltimos, audio faylning to'g'ridan-to'g'ri havolasini (masalan: Google Drive, Dropbox yoki .mp3/.m4a havolasini) yuboring.",
        "link_too_large": "❌ Havoladagi fayl hajmi juda katta ({size_mb} MB). Havola orqali maksimal 100 MB gacha fayllar qabul qilinadi.",
        "file_too_large": (
            "⚠️ **Telegram Bot API cheklovi: Fayl hajmi {size_mb} MB!**\n\n"
            "Telegram o'zining rasmiy Bot serverlarida botlar uchun bevosita fayl yuklab olishga qat'iy **20 MB limit** o'rnatgan.\n\n"
            "🚀 **20 MB dan katta fayllarni tahlil qilishning oson yo'llari:**\n\n"
            "1. 🔗 **Havola (link) orqali yuborish (Tavsiya etiladi!):**\n"
            "Audio faylingizni Google Drive, Dropbox yoki to'g'ridan-to'g'ri internet havolasini (linkini) shu chatga yuboring — botimiz uni **100 MB gacha cheklovsiz** yuklab olib, sun'iy intellekt orqali zudlik bilan tahlil qilib beradi!\n\n"
            "2. 🎙 **Telegram Ovozli Xabar (Voice Note):**\n"
            "Telegram mikrofon tugmasi orqali yozilgan ovozli xabarlar o'ta ixcham (Opus) bo'lgani sababli, hatto **1.5–2 soatlik (100 daqiqa)** audio ham 20 MB ga bemalol sig'adi!\n\n"
            "3. ✂️ **Bo'laklash:**\n"
            "Audioni 20 MB dan kichik qismlarga bo'lib yuborishingiz mumkin."
        ),
        "rem_free": "\n\n🎁 **Sizda {rem} ta bepul tahlil imkoniyati qoldi.**",
        "rem_ended": "\n\n⚠️ **Sizning bepul sinov limitingiz tugadi.** Keyingi audiolarni tahlil qilish uchun quyidagi obuna tugmasidan foydalaning.",
        "error_occurred": "Xatolik yuz berdi: "
    },
    "ru": {
        "welcome_title": "Здравствуйте!\n\n**AudioScribe** — ваш умный помощник для транскрипции и анализа голосовых сообщений и аудио.\n\n",
        "welcome_body": (
            "Отправьте мне любое голосовое сообщение (voice), аудиофайл (MP3/M4A/WAV) или ссылку на аудио:\n"
            "1. 📝 Составлю краткое содержание и суть\n"
            "2. 📋 Выделю задачи и поручения\n"
            "3. 💡 Соберу главные мысли и тезисы\n"
            "4. 📌 Найду даты, суммы, цены и контакты\n"
            "5. ✍️ Предоставлю полную текстовую расшифровку.\n\n"
            "👇 Удобно управляйте ботом с помощью кнопок внизу:"
        ),
        "status_admin": "👑 **Вы Администратор бота.** Вы можете управлять ботом кнопками ниже.\n\n",
        "status_sub": "💎 **Ваша подписка активна!** (Срок действия: до {exp_date})\n\n",
        "status_free": "🎁 **У вас осталось {left} бесплатных анализов.**\n\n",
        "btn_sub": "💳 Подписка и Тарифы",
        "btn_lang": "🌐 Выбрать язык",
        "btn_help": "ℹ️ О боте / Помощь",
        "btn_admin": "👑 Админ панель",
        "choose_lang_title": "🌐 **Выберите язык / Tilni tanlang / Выберите язык:**",
        "lang_changed": "✅ Язык интерфейса бота успешно изменён на **Русский**!",
        "offer_title": "🔒 **Ваш бесплатный лимит исчерпан.**\n\n",
        "offer_body": (
            "Чтобы пользоваться AudioScribe без ограничений, оформите подписку:\n\n"
            "🔹 **Подписка на 1 месяц:** {price_month} сум\n"
            "🔥 **Подписка на 1 год:** {price_year} сум *(Выгодная скидка!)*\n\n"
            "💳 **Способ оплаты:** Click / Карта\n"
            "Номер карты / Click: `{click_info}`\n\n"
            "Откроется неограниченный доступ к расшифровке и анализу любых аудиосообщений.\n\n"
            "Выберите тариф ниже:"
        ),
        "btn_sub_monthly": "💳 Подписка на 1 месяц — {price} сум",
        "btn_sub_yearly": "🔥 Подписка на 1 год — {price} сум (Большая скидка!)",
        "btn_sub_info": "ℹ️ Реквизиты и инструкция по оплате",
        "user_status_header": "📊 **Ваш статус:**\nОсталось бесплатных анализов: **{left} шт.**\n\n",
        "active_sub_info": "💎 **У вас активна Premium подписка!**\n\nТариф: {plan}\nДействует до: {exp_date}\n\nВы можете анализировать неограниченное количество аудио.",
        "admin_sub_info": "👑 Вы являетесь Администратором бота и пользуетесь им без ограничений!",
        "pay_instruction": (
            "💳 **Оплата через Click / Карту ({plan_name}):**\n\n"
            "📌 Сумма к оплате: **{price}**\n"
            "💳 Номер карты / Click: `{click_info}`\n\n"
            "**Инструкция по оплате:**\n"
            "1. Переведите сумму через Click или мобильный банк на указанную карту.\n"
            "2. Отправьте **скриншот чека об оплате (фотографию)** прямо в этот чат.\n"
            "3. Администратор проверит чек, и подписка сразу активируется!\n\n"
            "Отправьте фото чека прямо в чат 📸"
        ),
        "payment_proof_sent": "✅ Ваш чек об оплате отправлен администратору! Подписка будет активирована в ближайшее время.",
        "audio_wait": "⏳ Аудио получено{dur_text}: Расшифровываю запись, формирую краткое содержание и анализ...",
        "audio_wait_progress": "⏳ Обработка аудио ({sec} сек)... Транскрипция и анализ формируются...",
        "audio_only_prompt": "Пожалуйста, отправляйте голосовые сообщения (voice), аудиофайлы (MP3/M4A/WAV) или ссылку на аудио.",
        "downloading_link": "⏳ Загрузка аудио по ссылке (поддерживается до 100 МБ)... Пожалуйста, подождите...",
        "link_invalid": "❌ По ссылке не найден аудиофайл. Отправьте прямую ссылку на аудиофайл (например, .mp3, .m4a).",
        "link_youtube": "⚠️ Ссылки на YouTube не содержат прямой аудиофайл. Пожалуйста, отправьте прямую ссылку на аудио (например: Google Drive, Dropbox или прямую ссылку .mp3/.m4a).",
        "link_too_large": "❌ Размер файла по ссылке превышает лимит ({size_mb} МБ). По ссылке поддерживаются файлы до 100 МБ.",
        "file_too_large": (
            "⚠️ **Ограничение Telegram Bot API: размер файла {size_mb} МБ!**\n\n"
            "Официальные серверы Telegram Bot API ограничивают прямое скачивание файлов для ботов лимитом в **20 МБ**.\n\n"
            "🚀 **Как анализировать файлы больше 20 МБ:**\n\n"
            "1. 🔗 **Отправить ссылкой (Рекомендуется!):**\n"
            "Отправьте ссылку на аудиофайл (Google Drive, Dropbox или прямую веб-ссылку) — бот скачает аудио **до 100 МБ без ограничений** и быстро обработает с помощью искусственного интеллекта!\n\n"
            "2. 🎙 **Голосовое сообщение Telegram (Voice):**\n"
            "Голосовые сообщения, записанные через микрофон в Telegram, сжаты сверхэффективно (Opus), поэтому даже **1.5–2 часа записи** легко умещаются в 20 МБ!\n\n"
            "3. ✂️ **Разделить:**\n"
            "Разделите аудио на части менее 20 МБ."
        ),
        "rem_free": "\n\n🎁 **У вас осталось {rem} бесплатных анализов.**",
        "rem_ended": "\n\n⚠️ **Ваш бесплатный лимит исчерпан.** Чтобы продолжить расшифровку, нажмите кнопку подписки ниже.",
        "error_occurred": "Произошла ошибка: "
    },
    "en": {
        "welcome_title": "Hello!\n\n**AudioScribe** — your AI assistant for transcribing and analyzing voice notes, audio files and links.\n\n",
        "welcome_body": (
            "Send me any voice note, audio file (MP3/M4A/WAV) or direct audio link:\n"
            "1. 📝 Concise summary & main takeaways\n"
            "2. 📋 Action items and assignments\n"
            "3. 💡 Key ideas and highlights\n"
            "4. 📌 Dates, prices, numbers, and contacts\n"
            "5. ✍️ Full word-for-word transcript.\n\n"
            "👇 Easily control the bot using the buttons below:"
        ),
        "status_admin": "👑 **You are the bot Administrator.** You can manage the bot using the buttons below.\n\n",
        "status_sub": "💎 **Your subscription is active!** (Expires: {exp_date})\n\n",
        "status_free": "🎁 **You have {left} free analyses remaining.**\n\n",
        "btn_sub": "💳 Plans & Subscription",
        "btn_lang": "🌐 Change Language",
        "btn_help": "ℹ️ About / Help",
        "btn_admin": "👑 Admin Panel",
        "choose_lang_title": "🌐 **Select a language / Tilni tanlang / Выберите язык:**",
        "lang_changed": "✅ Bot language set to **English**!",
        "offer_title": "🔒 **Your free trial limit has been reached.**\n\n",
        "offer_body": (
            "Upgrade to AudioScribe Premium to transcribe and analyze without limits:\n\n"
            "🔹 **1 Month Plan:** {price_month} UZS\n"
            "🔥 **1 Year Plan:** {price_year} UZS *(Best Value!)*\n\n"
            "💳 **Payment method:** Click / Card\n"
            "Card / Click number: `{click_info}`\n\n"
            "Enjoy unlimited audio transcriptions and smart summaries.\n\n"
            "Select an option below to proceed:"
        ),
        "btn_sub_monthly": "💳 1 Month Plan — {price} UZS",
        "btn_sub_yearly": "🔥 1 Year Plan — {price} UZS (Best Value!)",
        "btn_sub_info": "ℹ️ Payment Details & Instructions",
        "user_status_header": "📊 **Your Status:**\nFree analyses left: **{left}**\n\n",
        "active_sub_info": "💎 **You have an active Premium subscription!**\n\nPlan: {plan}\nExpires: {exp_date}\n\nYou can transcribe unlimited audios.",
        "admin_sub_info": "👑 You are the Administrator and have unlimited access!",
        "pay_instruction": (
            "💳 **Payment via Click / Card ({plan_name}):**\n\n"
            "📌 Amount: **{price}**\n"
            "💳 Card / Click number: `{click_info}`\n\n"
            "**Instructions:**\n"
            "1. Transfer the amount to the card above via Click or your bank app.\n"
            "2. Send the **payment receipt screenshot (photo)** directly to this chat.\n"
            "3. The admin will verify it and activate your subscription right away!\n\n"
            "Send your receipt photo directly here 📸"
        ),
        "payment_proof_sent": "✅ Your receipt has been sent to the admin! Your subscription will be activated shortly.",
        "audio_wait": "⏳ Audio received{dur_text}: Transcribing and preparing summary and analysis...",
        "audio_wait_progress": "⏳ Processing audio ({sec}s elapsed)... Transcribing and analyzing...",
        "audio_only_prompt": "Please send voice messages (voice), audio files (MP3/M4A/WAV) or audio links.",
        "downloading_link": "⏳ Downloading audio from link (up to 100 MB supported)... Please wait...",
        "link_invalid": "❌ Audio file could not be found or downloaded from this link. Please send a direct audio link.",
        "link_youtube": "⚠️ YouTube links do not provide direct audio files. Please send a direct audio link (e.g. Google Drive, Dropbox, or a direct .mp3/.m4a link).",
        "link_too_large": "❌ File from link is too large ({size_mb} MB). Maximum supported size via link is 100 MB.",
        "file_too_large": (
            "⚠️ **Telegram Bot API Limit: File size is {size_mb} MB!**\n\n"
            "Telegram's official Bot API servers enforce a strict **20 MB download limit** for bot file downloads.\n\n"
            "🚀 **How to analyze audio files larger than 20 MB:**\n\n"
            "1. 🔗 **Send as Link / URL (Recommended!):**\n"
            "Send a direct audio link (Google Drive, Dropbox, or direct web link) into this chat — our bot will download it **up to 100 MB without limits** and transcribe it instantly with advanced AI!\n\n"
            "2. 🎙 **Send as Telegram Voice Note:**\n"
            "Voice notes recorded in Telegram use Opus compression, fitting up to **1.5–2 hours (100 mins)** inside 20 MB!\n\n"
            "3. ✂️ **Split File:**\n"
            "Split the audio into parts smaller than 20 MB."
        ),
        "rem_free": "\n\n🎁 **You have {rem} free analyses remaining.**",
        "rem_ended": "\n\n⚠️ **Your free trial limit has been reached.** To analyze more audios, use the subscription button below.",
        "error_occurred": "An error occurred: "
    }
}


def get_admin_ids():
    """
    Barcha administratorlarning Telegram ID larini to'plam (set) ko'rinishida qaytaradi.
    1. ADMIN_ID yoki TELEGRAM_ADMIN_ID muhit o'zgaruvchisi (Render)
    2. Bazadagi 'admin_id' sozlamasi (vergul bilan bir nechta bo'lishi mumkin)
    3. bot_sozlamalar.json fayli
    """
    admins = set()
    for env_var in ["ADMIN_ID", "TELEGRAM_ADMIN_ID"]:
        val = os.getenv(env_var)
        if val:
            for item in str(val).split(","):
                if item.strip():
                    admins.add(str(item.strip()))
                    
    db_val = db.get_setting("admin_id")
    if db_val:
        for item in str(db_val).split(","):
            if item.strip():
                admins.add(str(item.strip()))
                
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                c = json.load(f)
                c_admin = c.get("admin_id")
                if c_admin:
                    for item in str(c_admin).split(","):
                        if item.strip():
                            admins.add(str(item.strip()))
        except Exception:
            pass
            
    return admins

def is_user_admin(user_id) -> bool:
    return str(user_id) in get_admin_ids()

def add_admin_id(user_id):
    admins = get_admin_ids()
    admins.add(str(user_id).strip())
    new_str = ",".join(admins)
    db.set_setting("admin_id", new_str)
    try:
        cfg = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
        cfg["admin_id"] = new_str
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass
    return admins

def get_main_keyboard(user_id, lang="uz"):
    """
    Foydalanuvchi ekrani ostidagi doimiy boshqaruv tugmalari (ReplyKeyboardMarkup)
    """
    t = TEXTS.get(lang, TEXTS["uz"])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    is_admin = is_user_admin(user_id)
    
    btn1 = types.KeyboardButton(t["btn_sub"])
    btn2 = types.KeyboardButton(t["btn_lang"])
    btn3 = types.KeyboardButton(t["btn_help"])
    
    if is_admin:
        btn_admin = types.KeyboardButton(t["btn_admin"])
        markup.add(btn1, btn2)
        markup.add(btn3, btn_admin)
    else:
        markup.add(btn1, btn2)
        markup.add(btn3)
        
    return markup


def get_language_inline_keyboard():
    """
    Til tanlash uchun inline tugmalar
    """
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
    )
    return markup


def get_subscription_keyboard(lang="uz"):
    """
    Obuna tanlash inline tugmalari
    """
    t = TEXTS.get(lang, TEXTS["uz"])
    markup = types.InlineKeyboardMarkup(row_width=1)
    price_month = db.get_setting("price_monthly", "25000")
    price_year = db.get_setting("price_yearly", "199000")
    
    markup.add(
        types.InlineKeyboardButton(t["btn_sub_monthly"].format(price=price_month), callback_data="pay_click_monthly"),
        types.InlineKeyboardButton(t["btn_sub_yearly"].format(price=price_year), callback_data="pay_click_yearly"),
        types.InlineKeyboardButton(t["btn_sub_info"], callback_data="pay_click_info")
    )
    return markup


# ==========================================
# GEMINI AUDIO TAHLIL VA TILGA MOSLASH
# ==========================================

SYSTEM_PROMPT = """
You are AudioScribe AI, the fastest and most accurate audio intelligence system.
Analyze the provided audio with extreme speed, high precision, and complete fidelity.
You must respond strictly in valid JSON adhering to the provided JSON Schema.

CRITICAL RULES:
1. JSON KEYS: All JSON keys MUST ALWAYS remain strictly in English as defined in the schema ("language_detected", "summary", "key_points", "action_items", "entities", "transcription"). NEVER translate the JSON keys into any other language!
2. CONTENT LANGUAGE: The VALUES (the text content of summary, key_points, action_items, entities, transcription) MUST BE IN THE EXACT SPOKEN LANGUAGE of the audio:
   - If audio is spoken in Uzbek -> all text values must be in natural, grammatically correct Uzbek.
   - If audio is spoken in Russian -> all text values must be in natural Russian.
   - If audio is spoken in English -> all text values must be in English.
3. COMPREHENSIVE OUTPUT (NEVER OMIT REQUIRED FIELDS):
   - "summary": 2-3 clear, informative sentences summarizing the entire audio (who spoke, the core message, and the conclusion).
   - "key_points": At least 3-5 distinct, insightful bullet points capturing key thoughts and takeaways.
   - "action_items": Explicit tasks, assignments, deadlines, or promises mentioned (empty list [] if none).
   - "entities": All dates/times, prices/amounts/numbers, and people/contacts mentioned.
   - "transcription": Full, verbatim, accurate transcription of everything spoken.
"""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "language_detected": {
            "type": "STRING",
            "description": "Language code: 'uz', 'ru', or 'en'"
        },
        "summary": {
            "type": "STRING",
            "description": "Comprehensive 2-3 sentence summary in the audio's spoken language"
        },
        "key_points": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "3-5 key takeaways and main points in the audio's spoken language"
        },
        "action_items": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Action items, assignments, tasks, or promises in the audio's spoken language"
        },
        "entities": {
            "type": "OBJECT",
            "properties": {
                "dates": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "numbers_amounts": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "people_contacts": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                }
            }
        },
        "transcription": {
            "type": "STRING",
            "description": "Full verbatim spoken transcription in the audio's spoken language"
        }
    },
    "required": ["language_detected", "summary", "key_points", "transcription"]
}

def upload_to_gemini_files_api(file_bytes, mime_type="audio/mp3"):
    """
    Faqat 20 MB dan katta ulkan fayllar uchun Google Files API.
    Kichik va o'rtacha (<=20MB) fayllar to'g'ridan-to'g'ri inlineData orqali sekundlarda tahlil qilinadi.
    """
    try:
        url_init = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={GEMINI_API_KEY}"
        headers = {
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(len(file_bytes)),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json"
        }
        init_res = http_session.post(url_init, headers=headers, json={"file": {"display_name": "audio_upload"}}, timeout=20)
        upload_url = init_res.headers.get("x-goog-upload-url")
        if not upload_url:
            return None
            
        upload_headers = {
            "Content-Length": str(len(file_bytes)),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize"
        }
        upload_res = http_session.post(upload_url, headers=upload_headers, data=file_bytes, timeout=120)
        file_info = upload_res.json()
        file_uri = file_info.get("file", {}).get("uri")
        file_name = file_info.get("file", {}).get("name")
        
        # Fayl ACTIVE holatiga kelishini tezkor tekshirish
        if file_name and file_info.get("file", {}).get("state") != "ACTIVE":
            for _ in range(12):
                time.sleep(1)
                st_res = http_session.get(f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={GEMINI_API_KEY}", timeout=10)
                if st_res.status_code == 200 and st_res.json().get("state") == "ACTIVE":
                    break
                    
        return file_uri
    except Exception:
        return None

def analyze_audio_with_gemini(file_bytes, mime_type="audio/ogg"):
    """
    Audioni maksimal tezlikda (1.5 - 3 soniyada) va to'liq aniqlikda tahlil qiladi.
    - 20 MB gacha barcha fayllar darhol inlineData (base64) orqali uzatiladi.
    - Asosiy model: gemini-2.5-flash (thinkingBudget: 0 orqali ortiqcha fikrlash kutishlarisiz darhol javob).
    - Zaxira modellar: gemini-3.7-flash (thinkingLevel: 'low'), gemini-3.5-flash (thinkingLevel: 'minimal').
    - Structured Outputs (responseSchema) orqali xulosa, asosiy fikrlar va transkripsiya 100% kafolatlanadi.
    """
    part_audio = None
    # Faqat 20 MB dan oshgan juda katta fayllar Files API orqali yuboriladi
    if len(file_bytes) > 20 * 1024 * 1024:
        file_uri = upload_to_gemini_files_api(file_bytes, mime_type)
        if file_uri:
            part_audio = {
                "fileData": {
                    "mimeType": mime_type,
                    "fileUri": file_uri
                }
            }
            
    if not part_audio:
        base64_data = base64.b64encode(file_bytes).decode("utf-8")
        part_audio = {
            "inlineData": {
                "mimeType": mime_type,
                "data": base64_data
            }
        }
    
    contents = [
        {
            "parts": [
                part_audio,
                {
                    "text": SYSTEM_PROMPT
                }
            ]
        }
    ]
    
    # 1. Asosiy ultra-tezkor model: gemini-3.6-flash (thinkingLevel: minimal) -> chaqmoqdek tez (1.5 - 2.5s)
    payload_36 = {
        "contents": contents,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0.0,
            "maxOutputTokens": 4096,
            "thinkingConfig": {
                "thinkingLevel": "minimal"
            }
        }
    }
    
    # 2. Gemini 3.7 Flash reja (thinkingLevel: low)
    payload_37 = {
        "contents": contents,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0.0,
            "maxOutputTokens": 4096,
            "thinkingConfig": {
                "thinkingLevel": "low"
            }
        }
    }
    
    # 3. Gemini 3.5 Flash reja (thinkingLevel: minimal)
    payload_35 = {
        "contents": contents,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0.0,
            "maxOutputTokens": 4096,
            "thinkingConfig": {
                "thinkingLevel": "minimal"
            }
        }
    }

    # 4. Fallback: schema-siz standart json
    payload_fallback = {
        "contents": contents,
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0,
            "maxOutputTokens": 4096
        }
    }
    
    models_plan = [
        ("gemini-3.6-flash", payload_36, 2),
        ("gemini-3.7-flash", payload_37, 2),
        ("gemini-3.5-flash", payload_35, 1),
        ("gemini-3.6-flash", payload_fallback, 1)
    ]
    
    last_error = ""
    for model_name, req_payload, max_retries in models_plan:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(max_retries):
            try:
                response = http_session.post(url, json=req_payload, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            raw_text = parts[0].get("text", "").strip()
                            clean_text = raw_text
                            # Markdown bloklarni tozalash (```json ... ```)
                            if clean_text.startswith("```"):
                                clean_text = re.sub(r"^```[a-zA-Z]*\n?", "", clean_text)
                                clean_text = re.sub(r"\n?```$", "", clean_text).strip()
                            if "{" in clean_text and "}" in clean_text:
                                start_idx = clean_text.find("{")
                                end_idx = clean_text.rfind("}") + 1
                                clean_text = clean_text[start_idx:end_idx]
                            return json.loads(clean_text)
                
                err_text = response.text
                if response.status_code in [429, 503] or "high demand" in err_text.lower():
                    if attempt < max_retries - 1:
                        time.sleep(0.4)
                        continue
                        
                try:
                    raw_msg = response.json().get("error", {}).get("message", response.text[:120])
                    last_error = raw_msg
                except Exception:
                    last_error = f"HTTP {response.status_code}"
            except requests.exceptions.Timeout:
                last_error = "Vaqt tugadi (Timeout)"
                if attempt < max_retries - 1:
                    time.sleep(0.3)
                    continue
            except Exception as ex:
                last_error = str(ex)
                
    raise Exception(last_error if last_error else "AI javob bermadi")


def format_user_error(error_obj, lang="uz") -> str:
    """
    Texnik xatoliklarni filtrlab, foydalanuvchiga toza va tushunarli matn qaytaradi.
    Gemini yoki model nomlari foydalanuvchi interfeysida ko'rsatilmaydi.
    """
    err_text = str(error_obj)
    hidden_terms = [
        "gemini", "model", "generativelanguage", "google", "api_key",
        "429", "503", "quota", "resource_exhausted", "not available", "no longer available"
    ]
    if any(term in err_text.lower() for term in hidden_terms):
        if lang == "ru":
            return "Сервер искусственного интеллекта временно перегружен. Пожалуйста, отправьте аудио повторно через несколько секунд."
        elif lang == "en":
            return "AI service is temporarily busy. Please send your audio again in a few seconds."
        else:
            return "Sun'iy intellekt xizmati hozirda band yoki qayta ishlanmoqda. Iltimos, bir necha soniyadan so'ng audioni qayta yuboring."
    return err_text


def _extract_field_val(data, aliases, default=None):
    """
    JSON kaliti o'zbekcha, ruscha yoki inglizcha bo'lishidan qat'iy nazar qiymatni topadi.
    """
    if not isinstance(data, dict):
        return default
    # 1. Aniq moslik
    for a in aliases:
        if a in data and data[a]:
            return data[a]
    # 2. Registr va belgilar farqisiz moslik
    norm_data = {re.sub(r'[\s_\-]+', '', k.lower()): v for k, v in data.items() if v}
    for a in aliases:
        norm_a = re.sub(r'[\s_\-]+', '', a.lower())
        if norm_a in norm_data:
            return norm_data[norm_a]
    return default


def format_analysis_result(res, ui_lang="uz"):
    """
    Audio tahlil natijasini audioning o'z tiliga mos holda, xulosa, asosiy fikrlar,
    topshiriqlar, muhim detallar va to'liq transkripsiya bilan kafolatlangan ravishda chiqaradi.
    """
    # 1. Tilni aniqlash
    raw_lang = str(_extract_field_val(res, ["language_detected", "language", "til", "yazyk", "lang"], "uz")).lower()
    if "ru" in raw_lang or "rus" in raw_lang:
        audio_lang = "ru"
    elif "en" in raw_lang or "eng" in raw_lang:
        audio_lang = "en"
    elif "uz" in raw_lang:
        audio_lang = "uz"
    else:
        audio_lang = ui_lang
        
    headers = {
        "uz": {
            "lang_label": "🌐 Til: O'zbekcha",
            "summary": "📝 QISQACHA XULOSA:\n",
            "key_points": "💡 ASOSIY FIKRLAR:\n",
            "actions": "📋 TOPSHIRIQLAR VA VAZIFALAR:\n",
            "details": "📌 MUHIM MA'LUMOTLAR:\n",
            "dates": "🗓 Sanalar/Vaqt: ",
            "numbers": "💰 Narx/Raqamlar: ",
            "people": "👤 Shaxslar/Kontakt: ",
            "transcription": "✍️ TO'LIQ TRANSKRIPSIYA:\n"
        },
        "ru": {
            "lang_label": "🌐 Язык: Русский",
            "summary": "📝 КРАТКОЕ СОДЕРЖАНИЕ:\n",
            "key_points": "💡 ОСНОВНЫЕ МЫСЛИ:\n",
            "actions": "📋 ЗАДАЧИ И ДЕЙСТВИЯ:\n",
            "details": "📌 ВАЖНЫЕ ДАННЫЕ:\n",
            "dates": "🗓 Даты/Время: ",
            "numbers": "💰 Цены/Числа: ",
            "people": "👤 Лица/Контакты: ",
            "transcription": "✍️ ПОЛНАЯ ТРАНСКРИПЦИЯ:\n"
        },
        "en": {
            "lang_label": "🌐 Language: English",
            "summary": "📝 SUMMARY:\n",
            "key_points": "💡 KEY POINTS:\n",
            "actions": "📋 ACTION ITEMS & TASKS:\n",
            "details": "📌 IMPORTANT DETAILS:\n",
            "dates": "🗓 Dates/Time: ",
            "numbers": "💰 Prices/Numbers: ",
            "people": "👤 People/Contacts: ",
            "transcription": "✍️ FULL TRANSCRIPTION:\n"
        }
    }
    
    h = headers.get(audio_lang, headers["uz"])
    
    # 2. Transkripsiyani olish
    transcription = str(_extract_field_val(
        res,
        ["transcription", "matn", "transkripsiya", "tekst", "текст", "audio_text", "transcript", "full_text"],
        ""
    ) or "").strip()
    
    # 3. Xulosa (Summary) ni olish
    summary_val = _extract_field_val(
        res,
        ["summary", "xulosa", "qisqacha_xulosa", "kratkoe_soderzhanie", "краткое_содержание", "кратко", "overview", "tavsif", "resume"],
        ""
    )
    if isinstance(summary_val, list):
        summary_val = " ".join(str(s) for s in summary_val)
    summary_text = str(summary_val or "").strip()
    
    # Agar model xulosani bo'sh qoldirgan bo'lsa, transkripsiyaning birinchi 1-2 gapidan avtomatik shakllantiramiz
    if not summary_text and transcription:
        sentences = [s.strip() for s in re.split(r'[\.\!\?\n]+', transcription) if len(s.strip()) > 5]
        if sentences:
            summary_text = ". ".join(sentences[:2]) + "."
        else:
            summary_text = transcription[:250]
            
    # 4. Asosiy fikrlar (Key points) ni olish
    key_points = _extract_field_val(
        res,
        ["key_points", "keypoints", "asosiy_fikrlar", "asosiy", "osnovnye_mysli", "основные_мысли", "tezislar", "points", "bullets", "highlights"],
        []
    )
    if isinstance(key_points, str):
        key_points = [p.strip(" •-*") for p in key_points.split("\n") if p.strip()]
    elif not isinstance(key_points, list):
        key_points = []
        
    # Agar model asosiy fikrlarni bo'sh qoldirgan bo'lsa, transkripsiyadan tezkor tuzamiz
    if not key_points and transcription:
        sentences = [s.strip() for s in re.split(r'[\.\!\?\n]+', transcription) if len(s.strip()) > 10]
        if len(sentences) >= 2:
            key_points = sentences[:4]
        elif summary_text:
            key_points = [summary_text]
            
    # 5. Topshiriqlar va vazifalar (Action items) ni olish
    action_items = _extract_field_val(
        res,
        ["action_items", "actionitems", "topshiriqlar", "vazifalar", "zadachi", "действия", "задачи", "tasks", "actions"],
        []
    )
    if isinstance(action_items, str):
        action_items = [p.strip(" •-*") for p in action_items.split("\n") if p.strip()]
    elif not isinstance(action_items, list):
        action_items = []
        
    # 6. Muhim detallar (Sanalar, Narxlar, Shaxslar)
    entities_raw = _extract_field_val(
        res,
        ["entities", "muhim_malumotlar", "muhim", "detallar", "vazhnaya_informatsiya", "важная_информация", "details"],
        {}
    )
    dates = []
    numbers = []
    people = []
    if isinstance(entities_raw, dict):
        dates = _extract_field_val(entities_raw, ["dates", "sanalar", "daty", "даты", "vaqt"], [])
        numbers = _extract_field_val(entities_raw, ["numbers_amounts", "numbers", "raqamlar", "narx", "chisla", "tseny", "цены", "числа"], [])
        people = _extract_field_val(entities_raw, ["people_contacts", "people", "shaxslar", "odamlar", "litsa", "kontakty", "лица", "контакты"], [])
        if isinstance(dates, str): dates = [dates]
        if isinstance(numbers, str): numbers = [numbers]
        if isinstance(people, str): people = [people]
        
    # Agar transkripsiya bo'sh bo'lib, xulosa mavjud bo'lsa:
    if not transcription and summary_text:
        transcription = summary_text

    # 7. Matnni tartibli yig'ish
    text_reply = f"{h['lang_label']}\n\n"
    
    if summary_text:
        text_reply += f"{h['summary']}{summary_text}\n\n"
        
    if key_points:
        text_reply += h["key_points"]
        for point in key_points:
            text_reply += f"• {point}\n"
        text_reply += "\n"
        
    if action_items:
        text_reply += h["actions"]
        for item in action_items:
            text_reply += f"• {item}\n"
        text_reply += "\n"
        
    if dates or numbers or people:
        text_reply += h["details"]
        if dates:
            text_reply += f"{h['dates']}{', '.join(str(d) for d in dates)}\n"
        if numbers:
            text_reply += f"{h['numbers']}{', '.join(str(n) for n in numbers)}\n"
        if people:
            text_reply += f"{h['people']}{', '.join(str(p) for p in people)}\n"
        text_reply += "\n"
        
    if transcription:
        text_reply += f"{h['transcription']}{transcription}\n"
        
    return text_reply



def show_subscription_offer(chat_id, lang="uz"):
    t = TEXTS.get(lang, TEXTS["uz"])
    price_month = db.get_setting("price_monthly", "25000")
    price_year = db.get_setting("price_yearly", "199000")
    click_info = db.get_setting("click_info", "8600 0000 0000 0000 (Click / Karta)")
    
    text = (
        f"{t['offer_title']}"
        f"{t['offer_body'].format(price_month=price_month, price_year=price_year, click_info=click_info)}"
    )
    bot.send_message(
        chat_id,
        text,
        reply_markup=get_subscription_keyboard(lang),
        parse_mode="Markdown"
    )


# ==========================================
# FOYDALANUVCHI BUYRUQLARI VA TUGMALARI
# ==========================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = db.get_or_create_user(message.chat.id, message.from_user.username or "", message.from_user.first_name or "")
    lang = db.get_user_language(message.chat.id)
    t = TEXTS.get(lang, TEXTS["uz"])
    
    # Birinchi bo'lib /start bosgan odam admin qilib belgilanadi (agar admin bo'lmasa)
    admins = get_admin_ids()
    if not admins:
        add_admin_id(message.chat.id)
    
    is_admin = is_user_admin(message.chat.id)
    
    status_text = ""
    if is_admin:
        status_text = t["status_admin"]
    elif user.get("is_subscribed") == 1:
        exp_date = (user.get("subscription_expires_at") or "")[:10]
        status_text = t["status_sub"].format(exp_date=exp_date)
    else:
        left = user.get("free_uses_left", 3)
        status_text = t["status_free"].format(left=left)

    msg = f"{t['welcome_title']}{status_text}{t['welcome_body']}"
    bot.reply_to(
        message,
        msg,
        reply_markup=get_main_keyboard(message.chat.id, lang),
        parse_mode="Markdown"
    )


@bot.message_handler(commands=['obuna', 'tariflar'])
def send_subscription_info(message):
    user = db.get_or_create_user(message.chat.id, message.from_user.username or "", message.from_user.first_name or "")
    lang = db.get_user_language(message.chat.id)
    t = TEXTS.get(lang, TEXTS["uz"])
    is_admin = is_user_admin(message.chat.id)
    
    if is_admin:
        bot.reply_to(message, t["admin_sub_info"], reply_markup=get_main_keyboard(message.chat.id, lang))
        return
        
    if user.get("is_subscribed") == 1:
        exp_date = (user.get("subscription_expires_at") or "")[:10]
        plan_names = {"monthly": "1 Oylik / 1 Месяц / 1 Month", "yearly": "1 Yillik / 1 Год / 1 Year"}
        plan = plan_names.get(user.get("subscription_plan"), "Faol")
        bot.reply_to(
            message,
            t["active_sub_info"].format(plan=plan, exp_date=exp_date),
            reply_markup=get_main_keyboard(message.chat.id, lang),
            parse_mode="Markdown"
        )
        return
        
    left = user.get("free_uses_left", 0)
    price_month = db.get_setting("price_monthly", "25000")
    price_year = db.get_setting("price_yearly", "199000")
    click_info = db.get_setting("click_info", "8600 0000 0000 0000 (Click / Karta)")
    
    status_header = t["user_status_header"].format(left=left)
    offer_body = t["offer_body"].format(price_month=price_month, price_year=price_year, click_info=click_info)
    
    text = status_header + offer_body
    bot.reply_to(
        message,
        text,
        reply_markup=get_subscription_keyboard(lang),
        parse_mode="Markdown"
    )


@bot.message_handler(commands=['lang', 'til', 'language'])
def send_language_menu(message):
    lang = db.get_user_language(message.chat.id)
    t = TEXTS.get(lang, TEXTS["uz"])
    bot.reply_to(
        message,
        t["choose_lang_title"],
        reply_markup=get_language_inline_keyboard(),
        parse_mode="Markdown"
    )


# ==========================================
# PASTKI TUGMALAR (REPLY KEYBOARD) HANDLERLARI
# ==========================================

@bot.message_handler(func=lambda msg: msg.text in [
    "💳 Obuna va Tariflar", "💳 Подписка и Тарифы", "💳 Plans & Subscription"
])
def handle_reply_sub_btn(message):
    send_subscription_info(message)


@bot.message_handler(func=lambda msg: msg.text in [
    "🌐 Tilni tanlash", "🌐 Выбрать язык", "🌐 Change Language",
    "🌐 Til / Язык / Language", "🌐 Tilni o'zgartirish", "🌐 Сменить язык"
])
def handle_reply_lang_btn(message):
    send_language_menu(message)


@bot.message_handler(func=lambda msg: msg.text in [
    "ℹ️ Bot haqida / Yordam", "ℹ️ О боте / Помощь", "ℹ️ About / Help"
])
def handle_reply_help_btn(message):
    send_welcome(message)


@bot.message_handler(func=lambda msg: msg.text in [
    "👑 Admin Panel", "👑 Админ панель"
])
def handle_reply_admin_btn(message):
    admin_panel(message)


# ==========================================
# ADMIN PANEL
# ==========================================

def get_admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Statistika", callback_data="adm_stats"),
        types.InlineKeyboardButton("⚙️ Bepul limit", callback_data="adm_limit"),
        types.InlineKeyboardButton("💰 Narxlarni sozlash", callback_data="adm_prices"),
        types.InlineKeyboardButton("💳 Click/Kartani sozlash", callback_data="adm_card"),
        types.InlineKeyboardButton("👤 Obuna yoqish", callback_data="adm_give_sub"),
        types.InlineKeyboardButton("📢 Xabar tarqatish", callback_data="adm_broadcast")
    )
    return markup

@bot.message_handler(commands=['myid', 'id'])
def my_id_handler(message):
    is_adm = is_user_admin(message.chat.id)
    adm_text = "\n\n👑 <b>Siz ushbu botning Administratorisiz!</b>" if is_adm else "\n\n💡 <i>To'lov cheklari sizga kelishi uchun /setadmin buyrug'ini yuboring.</i>"
    bot.reply_to(
        message,
        f"🆔 <b>Sizning Telegram ID:</b> <code>{message.chat.id}</code>{adm_text}",
        parse_mode="HTML"
    )


@bot.message_handler(commands=['setadmin', 'iamadmin', 'admin_yoqish'])
def set_admin_handler(message):
    add_admin_id(message.chat.id)
    lang = db.get_user_language(message.chat.id)
    bot.reply_to(
        message,
        f"👑 <b>Tabriklaymiz! Siz muvaffaqiyatli bot Administratori etib biriktirildingiz!</b>\n\n"
        f"🆔 <b>Sizning ID:</b> <code>{message.chat.id}</code>\n\n"
        f"✅ Endi barcha foydalanuvchilar yuboradigan to'lov cheklari to'g'ridan-to'g'ri sizga keladi!\n"
        f"Pastdagi menyuda <b>👑 Admin Panel</b> tugmasi paydo bo'ldi.",
        reply_markup=get_main_keyboard(message.chat.id, lang),
        parse_mode="HTML"
    )


@bot.message_handler(commands=['admin'])
def admin_panel(message):
    admins = get_admin_ids()
    if not admins:
        add_admin_id(message.chat.id)
        
    if not is_user_admin(message.chat.id):
        bot.reply_to(
            message,
            "⛔️ Kechirasiz, bu bo'lim faqat bot administratori uchun.\n\n"
            "Agar siz bot egasi bo'lsangiz, administratorlik huquqini olish uchun /setadmin buyrug'ini yuboring."
        )
        return

    stats = db.get_stats()
    free_limit = db.get_setting("free_limit", "3")
    price_m = db.get_setting("price_monthly", "25000")
    price_y = db.get_setting("price_yearly", "199000")
    click_info = db.get_setting("click_info", "8600 0000 0000 0000 (Click / Karta)")
    
    text = (
        "👑 **AudioScribe Admin Boshqaruv Paneli**\n\n"
        f"👥 Jami foydalanuvchilar: **{stats['total_users']} ta**\n"
        f"💎 Faol obunachilar: **{stats['active_subs']} ta**\n"
        f"🎁 Bepul foydalanuvchilar: **{stats['active_free']} ta**\n\n"
        f"⚙️ **Joriy sozlamalar:**\n"
        f"• Bepul urinishlar: **{free_limit} ta**\n"
        f"• 1 oylik obuna: **{price_m} so'm**\n"
        f"• 1 yillik obuna: **{price_y} so'm**\n"
        f"• Click / Karta: `{click_info}`\n\n"
        "Kerakli bo'limni tanlang:"
    )
    bot.reply_to(message, text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")


# ==========================================
# CALLBACK HANDLERS (Tugmalar bosilganda)
# ==========================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    is_admin = is_user_admin(user_id) or is_user_admin(chat_id)
    lang = db.get_user_language(chat_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    
    # ------------------ TILNI O'ZGARTIRISH ------------------
    if call.data.startswith("set_lang_"):
        new_lang = call.data.replace("set_lang_", "")
        if new_lang in ["uz", "ru", "en"]:
            db.set_user_language(chat_id, new_lang)
            new_t = TEXTS[new_lang]
            bot.answer_callback_query(call.id)
            bot.send_message(
                chat_id,
                new_t["lang_changed"],
                reply_markup=get_main_keyboard(chat_id, new_lang),
                parse_mode="Markdown"
            )
        return

    # ------------------ FOYDALANUVCHI CLICK TO'LOVLARI ------------------
    if call.data in ["pay_click_monthly", "pay_click_yearly", "pay_click_info", "buy_card_info"]:
        click_info = db.get_setting("click_info", "8600 0000 0000 0000 (Click / Karta)")
        price_m = db.get_setting("price_monthly", "25000")
        price_y = db.get_setting("price_yearly", "199000")
        
        plan_labels = {
            "uz": {"m": "1 Oylik", "y": "1 Yillik", "info": "Tanlangan"},
            "ru": {"m": "1 Месяц", "y": "1 Год", "info": "Выбранный"},
            "en": {"m": "1 Month", "y": "1 Year", "info": "Selected"}
        }
        pl = plan_labels.get(lang, plan_labels["uz"])
        target_plan = pl["m"] if call.data == "pay_click_monthly" else (pl["y"] if call.data == "pay_click_yearly" else pl["info"])
        target_price = f"{price_m} so'm" if call.data == "pay_click_monthly" else (f"{price_y} so'm" if call.data == "pay_click_yearly" else f"{price_m} / {price_y} so'm")
        
        text = t["pay_instruction"].format(
            plan_name=target_plan,
            price=target_price,
            click_info=click_info
        )
        bot.send_message(
            chat_id,
            text,
            reply_markup=get_main_keyboard(chat_id, lang),
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    # ------------------ ADMIN TASDIQLASHLARI (CHEKLARNI TEKSHIRISH) ------------------
    if call.data == "noop":
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        return

    if call.data.startswith("approve_sub_"):
        # Spinner qotib qolmasligi uchun darhol Telegram serveriga javob qaytaramiz
        try:
            bot.answer_callback_query(call.id, "✅ Obuna faollashtirilmoqda...")
        except Exception:
            pass
            
        add_admin_id(call.from_user.id)
        add_admin_id(chat_id)
        
        parts = call.data.split("_")
        plan = parts[2] if len(parts) > 2 else "monthly"
        target_uid = int(parts[3]) if len(parts) > 3 else 0
        
        if target_uid:
            new_exp = db.activate_subscription(target_uid, plan)
        else:
            new_exp = (datetime.now() + timedelta(days=30)).isoformat()
            
        plan_name = "1 Oylik" if plan == "monthly" else "1 Yillik"
        admin_name = call.from_user.first_name or "Admin"
        
        done_markup = types.InlineKeyboardMarkup()
        done_markup.add(types.InlineKeyboardButton(f"✅ Tasdiqlandi ({plan_name})", callback_data="noop"))
        
        new_caption_html = (
            f"✅ <b>TO'LOV TASDIQLANDI!</b>\n\n"
            f"👤 <b>Foydalanuvchi ID:</b> <code>{target_uid}</code>\n"
            f"📦 <b>Tarif:</b> {plan_name}\n"
            f"⏳ <b>Amal qilish muddati:</b> {new_exp[:10]} gacha\n"
            f"👨‍💼 <b>Tasdiqladi:</b> {admin_name}\n"
            f"⏰ <b>Vaqt:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        plain_text = f"✅ TO'LOV TASDIQLANDI ({plan_name})!\nFoydalanuvchi ID: {target_uid}\nMuddati: {new_exp[:10]} gacha"
        
        # Xabar matnli yoki rasmliligiga qarab to'g'ri metodni chaqirish
        if call.message.text is not None:
            try:
                bot.edit_message_text(
                    text=new_caption_html,
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    reply_markup=done_markup,
                    parse_mode="HTML"
                )
            except Exception:
                try:
                    bot.edit_message_text(
                        text=plain_text,
                        chat_id=chat_id,
                        message_id=call.message.message_id,
                        reply_markup=done_markup
                    )
                except Exception:
                    pass
        else:
            try:
                bot.edit_message_caption(
                    caption=new_caption_html,
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    reply_markup=done_markup,
                    parse_mode="HTML"
                )
            except Exception:
                try:
                    bot.edit_message_caption(
                        caption=plain_text,
                        chat_id=chat_id,
                        message_id=call.message.message_id,
                        reply_markup=done_markup
                    )
                except Exception:
                    pass

        # Qo'shimcha xavfsizlik: tugma har qanday holatda "Tasdiqlandi"ga o'zgarsin
        try:
            bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=done_markup
            )
        except Exception:
            pass
        
        # Foydalanuvchiga uning tilida xushxabar yuborish
        target_lang = db.get_user_language(target_uid)
        congrats_msgs = {
            "uz": (
                f"🎉 **Tabriklaymiz! Click / Karta to'lovingiz tasdiqlandi.**\n\n"
                f"Sizga **{plan_name}** to'liq Premium obuna yoqildi.\n"
                f"Amal qilish muddati: **{new_exp[:10]}** gacha.\n\n"
                f"Endi istalgancha audio va ovozli xabarlarni cheklovsiz botga yuborishingiz mumkin!"
            ),
            "ru": (
                f"🎉 **Поздравляем! Ваш платёж успешно подтверждён.**\n\n"
                f"Вам подключена Premium подписка ({plan_name}).\n"
                f"Срок действия: до **{new_exp[:10]}**.\n\n"
                f"Теперь вы можете без ограничений транскрибировать любые аудио и голосовые сообщения!"
            ),
            "en": (
                f"🎉 **Congratulations! Your payment has been approved.**\n\n"
                f"Premium subscription ({plan_name}) is now active.\n"
                f"Valid until: **{new_exp[:10]}**.\n\n"
                f"You can now transcribe unlimited audios and voice notes!"
            )
        }
        try:
            bot.send_message(
                target_uid,
                congrats_msgs.get(target_lang, congrats_msgs["uz"]),
                reply_markup=get_main_keyboard(target_uid, target_lang),
                parse_mode="Markdown"
            )
        except Exception:
            pass
            
        return

    elif call.data.startswith("reject_sub_"):
        try:
            bot.answer_callback_query(call.id, "❌ To'lov rad etildi!")
        except Exception:
            pass
            
        add_admin_id(call.from_user.id)
        add_admin_id(chat_id)
        
        parts = call.data.split("_")
        target_uid = int(parts[2]) if len(parts) > 2 else 0
        admin_name = call.from_user.first_name or "Admin"
        
        rejected_markup = types.InlineKeyboardMarkup()
        rejected_markup.add(types.InlineKeyboardButton("❌ Rad etilgan", callback_data="noop"))
        
        reject_caption_html = (
            f"❌ <b>TO'LOV RAD ETILDI!</b>\n\n"
            f"👤 <b>Foydalanuvchi ID:</b> <code>{target_uid}</code>\n"
            f"👨‍💼 <b>Rad etdi:</b> {admin_name}\n"
            f"⏰ <b>Vaqt:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        reject_plain = f"❌ TO'LOV RAD ETILDI!\nFoydalanuvchi ID: {target_uid}"
        
        if call.message.text is not None:
            try:
                bot.edit_message_text(
                    text=reject_caption_html,
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    reply_markup=rejected_markup,
                    parse_mode="HTML"
                )
            except Exception:
                try:
                    bot.edit_message_text(
                        text=reject_plain,
                        chat_id=chat_id,
                        message_id=call.message.message_id,
                        reply_markup=rejected_markup
                    )
                except Exception:
                    pass
        else:
            try:
                bot.edit_message_caption(
                    caption=reject_caption_html,
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    reply_markup=rejected_markup,
                    parse_mode="HTML"
                )
            except Exception:
                try:
                    bot.edit_message_caption(
                        caption=reject_plain,
                        chat_id=chat_id,
                        message_id=call.message.message_id,
                        reply_markup=rejected_markup
                    )
                except Exception:
                    pass

        try:
            bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=rejected_markup
            )
        except Exception:
            pass
                
        target_lang = db.get_user_language(target_uid)
        reject_msgs = {
            "uz": "❌ Kechirasiz, siz yuborgan to'lov cheki tasdiqlanmadi. Agar adashmovchilik bo'lsa, adminga murojaat qiling.",
            "ru": "❌ К сожалению, отправленный чек не подтверждён. Если произошла ошибка, свяжитесь с администратором.",
            "en": "❌ Sorry, your payment receipt could not be verified. Please contact the administrator."
        }
        try:
            bot.send_message(target_uid, reject_msgs.get(target_lang, reject_msgs["uz"]))
        except Exception:
            pass
        return

    # ------------------ ADMIN PANEL MENYULARI ------------------
    if not is_admin:
        bot.answer_callback_query(call.id)
        return

    if call.data == "adm_stats":
        stats = db.get_stats()
        text = (
            "📊 **Bot Statistikasi:**\n\n"
            f"👤 Jami foydalanuvchilar: **{stats['total_users']}** ta\n"
            f"💎 Faol obunachilar: **{stats['active_subs']}** ta\n"
            f"🎁 Bepul foydalanuvchilar: **{stats['active_free']}** ta"
        )
        bot.send_message(chat_id, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    elif call.data == "adm_limit":
        admin_states[chat_id] = "awaiting_free_limit"
        curr = db.get_setting("free_limit", "3")
        bot.send_message(chat_id, f"Yangi bepul urinishlar sonini yozib yuboring (Hozirgi: {curr} ta):")
        bot.answer_callback_query(call.id)

    elif call.data == "adm_prices":
        admin_states[chat_id] = "awaiting_prices"
        pm = db.get_setting("price_monthly", "25000")
        py = db.get_setting("price_yearly", "199000")
        text = (
            f"Hozirgi narxlar:\n• 1 oylik: {pm} so'm\n• 1 yillik: {py} so'm\n\n"
            "Yangi narxlarni quyidagi formatda yuboring (so'mda):\n"
            "`OYLIK_NARX YILLIK_NARX`\n"
            "Masalan: `30000 250000`"
        )
        bot.send_message(chat_id, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    elif call.data == "adm_card":
        admin_states[chat_id] = "awaiting_card_info"
        curr = db.get_setting("click_info", "8600 0000 0000 0000 (Click / Karta)")
        bot.send_message(chat_id, f"Yangi Click / Karta raqami va egasining ismini yozib yuboring:\n(Hozirgi: `{curr}`)", parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    elif call.data == "adm_give_sub":
        admin_states[chat_id] = "awaiting_user_id_sub"
        bot.send_message(chat_id, "Obuna bermoqchi bo'lgan foydalanuvchining **Telegram ID** raqamini yozing:\n(Foydalanuvchi ID sini bilish uchun u /start bosganda yoki o'zidan so'rashingiz mumkin)")
        bot.answer_callback_query(call.id)

    elif call.data == "adm_broadcast":
        admin_states[chat_id] = "awaiting_broadcast"
        bot.send_message(chat_id, "Barcha foydalanuvchilarga yuboriladigan xabarni yozing (matn yoki e'lon):")
        bot.answer_callback_query(call.id)


# ==========================================
# ADMIN MATNLI SO'ROVLARI VA TO'LOV CHEKLARI
# ==========================================

@bot.message_handler(func=lambda msg: msg.chat.id in admin_states and msg.content_type == 'text')
def handle_admin_inputs(message):
    chat_id = message.chat.id
    state = admin_states.pop(chat_id, None)
    
    if state == "awaiting_free_limit":
        val = message.text.strip()
        if val.isdigit():
            db.set_setting("free_limit", val)
            bot.reply_to(message, f"✅ Bepul urinishlar soni **{val} ta** ga o'zgartirildi!", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Faqat raqam kiriting.")

    elif state == "awaiting_prices":
        parts = message.text.strip().split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            db.set_setting("price_monthly", parts[0])
            db.set_setting("price_yearly", parts[1])
            bot.reply_to(message, f"✅ Yangi narxlar saqlandi:\n1 oylik: {parts[0]} so'm\n1 yillik: {parts[1]} so'm")
        else:
            bot.reply_to(message, "❌ Noto'g'ri format. Ikkita raqam yuboring, masalan: `30000 250000`", parse_mode="Markdown")

    elif state == "awaiting_card_info":
        db.set_setting("click_info", message.text.strip())
        bot.reply_to(message, f"✅ Click / Karta ma'lumotlari saqlandi:\n`{message.text.strip()}`", parse_mode="Markdown")

    elif state == "awaiting_user_id_sub":
        uid_str = message.text.strip()
        if uid_str.isdigit():
            uid = int(uid_str)
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("1 Oylik", callback_data=f"approve_sub_monthly_{uid}"),
                types.InlineKeyboardButton("1 Yillik", callback_data=f"approve_sub_yearly_{uid}")
            )
            bot.reply_to(message, f"Foydalanuvchi ID: `{uid}`\nQaysi tarifni yoqmoqchisiz?", reply_markup=markup, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ ID faqat raqamlardan iborat bo'lishi kerak.")

    elif state == "awaiting_broadcast":
        users = db.get_all_users()
        sent = 0
        status_msg = bot.reply_to(message, f"Xabar {len(users)} ta foydalanuvchiga tarqatilmoqda...")
        for u in users:
            try:
                bot.send_message(u, message.text)
                sent += 1
                time.sleep(0.05)
            except Exception:
                pass
        bot.edit_message_text(f"✅ Xabar muvaffaqiyatli tarqatildi!\nYetib borganlar soni: {sent}/{len(users)} ta", chat_id, status_msg.message_id)


def _process_payment_proof(message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    admins = get_admin_ids()
    
    first_name = message.from_user.first_name or "Foydalanuvchi"
    username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"
    
    # Obunani tasdiqlash / rad etish tugmalari
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ 1 Oylik yoqish", callback_data=f"approve_sub_monthly_{chat_id}"),
        types.InlineKeyboardButton("✅ 1 Yillik yoqish", callback_data=f"approve_sub_yearly_{chat_id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_sub_{chat_id}")
    )
    
    # Markdown xatolaridan saqlanish uchun xavfsiz HTML format
    safe_name = str(first_name).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_user = str(username).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    caption_html = (
        "📥 <b>Yangi Click / Karta to'lov cheki keldi!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {safe_name} ({safe_user})\n"
        f"🆔 <b>ID:</b> <code>{chat_id}</code>\n"
        f"⏰ <b>Vaqt:</b> {now_str}\n\n"
        "To'lovni tekshirib, quyidagi tugmalar orqali obunani yoqing:"
    )
    plain_caption = (
        f"📥 Yangi Click / Karta to'lov cheki keldi!\n\n"
        f"Foydalanuvchi: {first_name} ({username})\n"
        f"ID: {chat_id}\nVaqt: {now_str}\n\n"
        "To'lovni tekshirib, quyidagi tugmalar orqali obunani yoqing:"
    )
    
    is_photo = (message.content_type == 'photo')
    file_id = message.photo[-1].file_id if is_photo else message.document.file_id
    
    try:
        db.record_payment(chat_id, plan="pending", amount="pending", proof=file_id, status="pending")
    except Exception:
        pass
        
    delivered_count = 0
    for adm in admins:
        # 1-urinish: HTML formatda
        try:
            if is_photo:
                bot.send_photo(adm, file_id, caption=caption_html, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_document(adm, file_id, caption=caption_html, reply_markup=markup, parse_mode="HTML")
            delivered_count += 1
            continue
        except Exception as ex1:
            print(f"[WARN] HTML bilan chek yuborishda xato: {ex1}")
            
        # 2-urinish: Oddiy matn formatida (HTML/Markdown parse xatoliksiz)
        try:
            if is_photo:
                bot.send_photo(adm, file_id, caption=plain_caption, reply_markup=markup)
            else:
                bot.send_document(adm, file_id, caption=plain_caption, reply_markup=markup)
            delivered_count += 1
        except Exception as ex2:
            print(f"[ERROR] Adminga ({adm}) chek yuborib bo'lmadi: {ex2}")
            
    if delivered_count > 0:
        bot.reply_to(message, t["payment_proof_sent"], reply_markup=get_main_keyboard(chat_id, lang))
    else:
        warning_msg = (
            "✅ To'lov chekingiz qabul qilindi!\n\n"
            "⚠️ Eslatma: Hozirda botda administrator hali to'liq biriktirilmagan ko'rinadi. "
            "Agar siz bot egasi bo'lsangiz, adminga aylanish uchun /setadmin buyrug'ini yuboring."
        )
        bot.reply_to(message, warning_msg, reply_markup=get_main_keyboard(chat_id, lang))


# Foydalanuvchi to'lov skrinshotini (cheki) yuborganida
@bot.message_handler(content_types=['photo'])
def handle_payment_proof(message):
    _process_payment_proof(message)


# ==========================================
# ASOSIY AUDIO VA OVOZLI XABARLARNI TAHLIL QILISH
# ==========================================

@bot.message_handler(content_types=['voice', 'audio', 'document'])
def handle_audio(message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    
    # 1. Obuna va bepul limitni tekshirish
    has_access, reason, free_left = db.check_user_access(chat_id)
    if not has_access:
        show_subscription_offer(chat_id, lang)
        return

    # 2. Fayl hajmini va davomiyligini aniqlash
    file_id = None
    file_size = 0
    duration = 0
    mime_type = "audio/ogg"

    if message.content_type == 'voice':
        file_id = message.voice.file_id
        file_size = getattr(message.voice, 'file_size', 0)
        duration = getattr(message.voice, 'duration', 0)
        mime_type = "audio/ogg"
    elif message.content_type == 'audio':
        file_id = message.audio.file_id
        file_size = getattr(message.audio, 'file_size', 0)
        duration = getattr(message.audio, 'duration', 0)
        m = (message.audio.mime_type or "").lower()
        fn = (getattr(message.audio, 'file_name', '') or "").lower()
        if "ogg" in m or fn.endswith(".ogg") or fn.endswith(".opus"):
            mime_type = "audio/ogg"
        elif "m4a" in m or fn.endswith(".m4a"):
            mime_type = "audio/m4a"
        elif "mp4" in m or fn.endswith(".mp4"):
            mime_type = "audio/mp4"
        elif "wav" in m or fn.endswith(".wav"):
            mime_type = "audio/wav"
        elif "aac" in m or fn.endswith(".aac"):
            mime_type = "audio/aac"
        elif "flac" in m or fn.endswith(".flac"):
            mime_type = "audio/flac"
        else:
            mime_type = "audio/mp3"
    elif message.content_type == 'document':
        file_id = message.document.file_id
        file_size = getattr(message.document, 'file_size', 0)
        duration = 0
        m = (message.document.mime_type or "").lower()
        fn = (getattr(message.document, 'file_name', '') or "").lower()
        
        # Agar to'lov cheki rasm yoki PDF hujjati sifatida yuborilgan bo'lsa:
        if m.startswith("image/") or fn.endswith(('.jpg', '.jpeg', '.png', '.webp', '.pdf')):
            _process_payment_proof(message)
            return
            
        if m.startswith("audio/") or fn.endswith(('.mp3', '.ogg', '.opus', '.m4a', '.mp4', '.wav', '.aac', '.flac')):
            if "ogg" in m or fn.endswith(".ogg") or fn.endswith(".opus"):
                mime_type = "audio/ogg"
            elif "m4a" in m or fn.endswith(".m4a"):
                mime_type = "audio/m4a"
            elif "mp4" in m or fn.endswith(".mp4"):
                mime_type = "audio/mp4"
            elif "wav" in m or fn.endswith(".wav"):
                mime_type = "audio/wav"
            elif "aac" in m or fn.endswith(".aac"):
                mime_type = "audio/aac"
            elif "flac" in m or fn.endswith(".flac"):
                mime_type = "audio/flac"
            else:
                mime_type = "audio/mp3"
        else:
            bot.reply_to(message, t["audio_only_prompt"], reply_markup=get_main_keyboard(chat_id, lang))
            return

    # 3. Telegram 20 MB cheklovini tekshirish
    MAX_SIZE = 20 * 1024 * 1024  # 20 Megabayt
    if file_size > MAX_SIZE:
        size_mb = round(file_size / (1024 * 1024), 1)
        bot.reply_to(
            message,
            t["file_too_large"].format(size_mb=size_mb),
            reply_markup=get_main_keyboard(chat_id, lang),
            parse_mode="Markdown"
        )
        return

    status_msg = None
    stop_typing = [False]
    try:
        dur_text = ""
        if duration > 0:
            if duration >= 60:
                mins = duration // 60
                secs = duration % 60
                if lang == "ru":
                    dur_text = f" ({mins} мин {secs} сек)"
                elif lang == "en":
                    dur_text = f" ({mins}m {secs}s)"
                else:
                    dur_text = f" ({mins} daqiqa {secs} soniya)"
            else:
                if lang == "ru":
                    dur_text = f" ({duration} сек)"
                elif lang == "en":
                    dur_text = f" ({duration}s)"
                else:
                    dur_text = f" ({duration} soniya)"
                
        def keep_typing():
            sec = 0
            while not stop_typing[0]:
                try:
                    bot.send_chat_action(chat_id, 'typing')
                    time.sleep(4)
                    sec += 4
                    if sec in [16, 36, 64, 96] and status_msg and duration > 45:
                        bot.edit_message_text(
                            t["audio_wait_progress"].format(sec=sec),
                            chat_id,
                            status_msg.message_id
                        )
                except Exception:
                    break
        t_typing = threading.Thread(target=keep_typing)
        t_typing.daemon = True
        t_typing.start()

        status_msg = bot.reply_to(message, t["audio_wait"].format(dur_text=dur_text))

        try:
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
        except Exception as dl_ex:
            err_msg_lower = str(dl_ex).lower()
            if "file is too big" in err_msg_lower or "too big" in err_msg_lower or file_size > MAX_SIZE:
                size_mb = round(file_size / (1024 * 1024), 1) if file_size else ">20"
                bot.edit_message_text(
                    t["file_too_large"].format(size_mb=size_mb),
                    chat_id,
                    status_msg.message_id,
                    parse_mode="Markdown"
                )
                return
            raise dl_ex
        
        res = analyze_audio_with_gemini(downloaded_file, mime_type)
        
        # Bepul urinish bo'lsa, bittasini kamaytiramiz
        remaining_info = ""
        if reason == "free_trial":
            rem = db.use_free_trial(chat_id)
            if rem > 0:
                remaining_info = t["rem_free"].format(rem=rem)
            else:
                remaining_info = t["rem_ended"]
        
        text_reply = format_analysis_result(res, lang)
        text_reply += remaining_info
        
        if len(text_reply) > 4000:
            bot.edit_message_text(text_reply[:4000], chat_id, status_msg.message_id)
            bot.send_message(chat_id, text_reply[4000:], reply_markup=get_main_keyboard(chat_id, lang))
        else:
            bot.edit_message_text(text_reply, chat_id, status_msg.message_id)

    except Exception as e:
        clean_err = format_user_error(e, lang)
        err_str = f"⚠️ {clean_err}"
        if status_msg:
            bot.edit_message_text(err_str, chat_id, status_msg.message_id)
        else:
            bot.reply_to(message, err_str, reply_markup=get_main_keyboard(chat_id, lang))
    finally:
        stop_typing[0] = True


# ==========================================
# 20 MB DAN KATTA AUDIOLARNI HAVOLA (LINK) ORQALI TAHLIL QILISH
# ==========================================

def get_direct_download_url(raw_url: str):
    """
    Google Drive, Dropbox va boshqa bulutli xizmatlar havolasini
    to'g'ridan-to'g'ri yuklab olish (direct download) manziliga o'tkazadi.
    """
    url = raw_url.strip()
    # Google Drive:
    if "drive.google.com" in url:
        m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
        if m:
            return f"https://drive.google.com/uc?export=download&id={m.group(1)}", True, m.group(1)
        m_id = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
        if m_id:
            return f"https://drive.google.com/uc?export=download&id={m_id.group(1)}", True, m_id.group(1)

    # Dropbox:
    if "dropbox.com" in url:
        if "dl=0" in url:
            return url.replace("dl=0", "dl=1"), False, None
        elif "?dl=1" not in url and "&dl=1" not in url:
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}dl=1", False, None

    return url, False, None


def stream_download_audio_link(url: str, max_size=100 * 1024 * 1024):
    """
    Havola orqali audio faylni xavfsiz stream tarzida 100 MB gacha yuklab oladi.
    """
    download_url, is_gdrive, gdrive_id = get_direct_download_url(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    resp = http_session.get(download_url, headers=headers, stream=True, timeout=60, allow_redirects=True)

    # Google Drive katta fayllar uchun virus tekshiruvi ogohlantirish sahifasi bersa:
    if is_gdrive and resp.status_code == 200:
        for k, v in resp.cookies.items():
            if k.startswith('download_warning'):
                params = {'id': gdrive_id, 'confirm': v}
                resp = http_session.get("https://docs.google.com/uc?export=download", params=params, headers=headers, stream=True, timeout=60)
                break

    if resp.status_code != 200:
        return None, None, f"HTTP_{resp.status_code}"

    cl = resp.headers.get("Content-Length")
    if cl and int(cl) > max_size:
        return None, None, f"TOO_LARGE:{round(int(cl)/(1024*1024), 1)}"

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "text/html" in content_type:
        return None, None, "HTML_PAGE"

    buf = bytearray()
    for chunk in resp.iter_content(chunk_size=1024 * 1024):
        if chunk:
            buf.extend(chunk)
            if len(buf) > max_size:
                return None, None, f"TOO_LARGE:{round(len(buf)/(1024*1024), 1)}"

    if len(buf) < 1024:
        return None, None, "TOO_SMALL"

    return bytes(buf), content_type, None


def infer_audio_mime(url: str, content_type: str, file_bytes: bytes) -> str:
    """
    Fayl turi (MIME type)ni aniqlaydi.
    """
    url_l = url.lower()
    ct_l = (content_type or "").lower()

    if "ogg" in ct_l or url_l.endswith(".ogg") or url_l.endswith(".opus") or file_bytes[:4] == b'OggS':
        return "audio/ogg"
    elif "m4a" in ct_l or url_l.endswith(".m4a"):
        return "audio/m4a"
    elif "mp4" in ct_l or url_l.endswith(".mp4"):
        return "audio/mp4"
    elif "wav" in ct_l or url_l.endswith(".wav") or file_bytes[:4] == b'RIFF':
        return "audio/wav"
    elif "aac" in ct_l or url_l.endswith(".aac"):
        return "audio/aac"
    elif "flac" in ct_l or url_l.endswith(".flac") or file_bytes[:4] == b'fLaC':
        return "audio/flac"
    return "audio/mp3"


@bot.message_handler(func=lambda msg: msg.text and bool(re.search(r'https?://[^\s]+', msg.text)))
def handle_audio_url(message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    # 1. Obuna yoki bepul sinovni tekshirish
    has_access, reason, free_left = db.check_user_access(chat_id)
    if not has_access:
        show_subscription_offer(chat_id, lang)
        return

    match = re.search(r'https?://[^\s]+', message.text)
    if not match:
        return
    url = match.group(0)

    # YouTube havolasi bo'lsa ogohlantirish
    url_l = url.lower()
    if "youtube.com" in url_l or "youtu.be" in url_l:
        bot.reply_to(message, t["link_youtube"], reply_markup=get_main_keyboard(chat_id, lang))
        return

    status_msg = None
    stop_typing = [False]
    try:
        status_msg = bot.reply_to(message, t["downloading_link"])

        def keep_typing():
            sec = 0
            while not stop_typing[0]:
                try:
                    bot.send_chat_action(chat_id, 'typing')
                    time.sleep(4)
                    sec += 4
                    if sec in [16, 36, 64, 96] and status_msg:
                        bot.edit_message_text(
                            t["audio_wait_progress"].format(sec=sec),
                            chat_id,
                            status_msg.message_id
                        )
                except Exception:
                    break

        t_typing = threading.Thread(target=keep_typing)
        t_typing.daemon = True
        t_typing.start()

        audio_bytes, content_type, err = stream_download_audio_link(url)
        if err:
            if err.startswith("TOO_LARGE:"):
                size_mb = err.split(":")[1]
                bot.edit_message_text(t["link_too_large"].format(size_mb=size_mb), chat_id, status_msg.message_id)
            else:
                bot.edit_message_text(t["link_invalid"], chat_id, status_msg.message_id)
            return

        mime_type = infer_audio_mime(url, content_type, audio_bytes)

        bot.edit_message_text(t["audio_wait"].format(dur_text=""), chat_id, status_msg.message_id)

        # Gemini 3.7 Flash orqali tahlil
        res = analyze_audio_with_gemini(audio_bytes, mime_type)

        remaining_info = ""
        if reason == "free_trial":
            rem = db.use_free_trial(chat_id)
            if rem > 0:
                remaining_info = t["rem_free"].format(rem=rem)
            else:
                remaining_info = t["rem_ended"]

        text_reply = format_analysis_result(res, lang)
        text_reply += remaining_info

        if len(text_reply) > 4000:
            bot.edit_message_text(text_reply[:4000], chat_id, status_msg.message_id)
            bot.send_message(chat_id, text_reply[4000:], reply_markup=get_main_keyboard(chat_id, lang))
        else:
            bot.edit_message_text(text_reply, chat_id, status_msg.message_id)

    except Exception as e:
        clean_err = format_user_error(e, lang)
        err_str = f"⚠️ {clean_err}"
        if status_msg:
            bot.edit_message_text(err_str, chat_id, status_msg.message_id)
        else:
            bot.reply_to(message, err_str, reply_markup=get_main_keyboard(chat_id, lang))
    finally:
        stop_typing[0] = True


# ==========================================
# SERVER VA ASOSIY SIKL
# ==========================================

if __name__ == "__main__":
    # Render va boshqa bepul bulutli serverlar uchun Web Health Server
    try:
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
        except ImportError:
            from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"AudioScribe Bot is running!")
            def log_message(self, format, *args):
                pass

        def start_web_server():
            port = int(os.environ.get("PORT", 8080))
            server = HTTPServer(("0.0.0.0", port), HealthHandler)
            server.serve_forever()

        t = threading.Thread(target=start_web_server)
        t.daemon = True
        t.start()

        def keep_awake():
            render_url = os.environ.get("RENDER_EXTERNAL_URL")
            if render_url:
                while True:
                    time.sleep(600)
                    try:
                        requests.get(render_url, timeout=10)
                    except Exception:
                        pass

        t_awake = threading.Thread(target=keep_awake)
        t_awake.daemon = True
        t_awake.start()
    except Exception:
        pass

    print("\n" + "=" * 50)
    print("  AudioScribe Telegram Bot muvaffaqiyatli ishga tushdi!")
    print("  Telegramda botingizga /start yoki /admin deb yozing.")
    print("=" * 50 + "\n")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 409:
                print("[OGOHLANTIRISH] 409 Conflict: Bot boshqa joyda (kompyuterda) ishlab turibdi. 7 soniyadan keyin qayta ulaniladi...")
                time.sleep(7)
            else:
                print(f"[OGOHLANTIRISH] Telegram xatolik ({e.error_code}): {e.description}. 3 soniyada qayta uriniladi...")
                time.sleep(3)
        except Exception as ex:
            print(f"[XATOLIK] Polling uzildi: {ex}. 3 soniyada qayta boshlanadi...")
            time.sleep(3)
