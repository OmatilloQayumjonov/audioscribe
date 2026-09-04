# AudioScribe AI - Android APK O'rnatish va Foydalanish Qo'llanmasi

Ushbu loyiha o'zbek, rus va ingliz tillaridagi audio va ovozli xabarlarni matnga o'giruvchi, qisqa xulosa hamda muhim ma'lumotlarni (topshiriqlar, sanalar, narxlar) ajratib beruvchi to'liq Android ilovadir.

---

## 1. APK Faylni Yig'ish (Build APK)

Loyihani APK formatiga yig'ish uchun terminal yoki buyruqlar satrida (PowerShell / CMD) quyidagi buyruqni ishga tushiring:

```bash
# 1. Kutubxonalarni yuklab olish
flutter pub get

# 2. Release formatidagi APK faylni yig'ish
flutter build apk --release
```

Agar bitta umumiy fayl o'rniga telefon protsessoriga moslashtirilgan yengilroq APK kerak bo'lsa:
```bash
flutter build apk --split-per-abi
```

### Tayyor APK fayl qayerda bo'ladi?
Yig'ish muvaffaqiyatli yakunlangach, tayyor APK faylingiz quyidagi manzilda paydo bo'ladi:
📁 `build/app/outputs/flutter-apk/app-release.apk`

Ushbu `app-release.apk` faylini xohlagan Android telefoningizga (Telegram orqali o'zingizga yuborib yoki USB kabel orqali) o'rnatishingiz mumkin.

---

## 2. Gemini Bepul API Kalitini Olish (1 daqiqa)

Ilova ovozlarni yuqori aniqlikda tahlil qilishi uchun Google Gemini AI modelidan foydalanadi:

1. Brauzeringizda **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)** sahifasiga kiring.
2. Google akkountingiz bilan kiring va **"Create API key"** tugmasini bosing.
3. Hosil bo'lgan kalitni (masalan: `AIzaSy...`) nusxalab oling.
4. Ilovani ochib, yuqoridagi **Sozlamalar (⚙️)** bo'limiga kiring va kalitni joylashtirib, **"Kalitni saqlash"** tugmasini bosing.
*(Kalit telefonda xavfsiz saqlanadi va bepul limitlari shaxsiy foydalanish uchun bemalol yetadi).*

---

## 3. Ilovadan Foydalanish Imkoniyatlari

### A. To'g'ridan-to'g'ri ovoz yozish (Mikrofon)
- Bosh sahifadagi **"Ovoz yozishni boshlash"** tugmasini bosing.
- O'zbek, rus yoki ingliz tilida erkin gapiring (sheva yoki aralash so'zlarni ham tushunadi).
- **"Tugatish"** tugmasini bosganingizda ilova avtomatik tarzda audioni tahlil qilib beradi.

### B. MP3 / Audio fayllarni yuklash
- Bosh sahifadagi **"MP3 / Audio fayl tanlash"** kartasini bosing.
- Telefoningizdagi MP3, M4A, WAV, OGG yoki AAC fayllarni tanlang.
- Ilova bir necha soniyada to'liq matn va xulosani tayyorlaydi.

### C. Telegram yoki WhatsApp ovozli xabarlarini yuborish
- Telegram yoki WhatsApp'dagi istalgan ovozli xabarni tanlang.
- **"Share" (Ulashish / Поделиться)** tugmasini bosing.
- Ro'yxatdan **AudioScribe AI** ilovasini tanlang.
- Xabar darhol tahlil qilinadi!

---

## 4. Natijalar Ko'rinishi

Tahlil yakunlangach sizga quyidagilar taqdim etiladi:
- **Audio pleer**: Audioni yana bir bor eshitish imkoniyati.
- **Til belgisi**: Aniqlangan til (O'zbekcha / Ruscha / Inglizcha).
- **Asosiy Xulosa**: Gapning asl mag'zi va xulosasi.
- **Topshiriqlar va Vazifalar**: Belgilash mumkin bo'lgan nazorat ro'yxati (Checklist).
- **Ajratib olingan ma'lumotlar**:
  - Sanalar va muddatlar (🗓)
  - Narxlar, summalar va hisob-kitoblar (💰)
  - Ismlar, rahbarlar va kontaktlar (👤)
  - Joy nomlari va manzillar (📍)
- **To'liq Transkripsiya**: Audiodagi barcha aytilgan so'zlar matni.
- **Ulashish va Nusxalash**: Barcha ma'lumotlarni bitta tugma bilan nusxalash yoki Telegram/WhatsApp orqali do'stlarga yuborish.
