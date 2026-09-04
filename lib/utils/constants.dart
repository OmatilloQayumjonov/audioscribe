class AppConstants {
  static const String appName = 'AudioScribe AI';
  static const String appTagline = "Ovozli xabarlar va MP3'larni matnga o'girish hamda tahlil qilish";

  // Gemini API modeli
  static const String geminiModel = 'gemini-2.5-flash';
  static const String geminiApiEndpoint = 'https://generativelanguage.googleapis.com/v1beta/models';

  // Standart tizimli yo'riqnoma (Prompt)
  static const String geminiAudioSystemPrompt = '''
Sen professional audio tahlilchi va transkriptorsan.
Berilgan audioni diqqat bilan tingla. Audio o'zbek, rus yoki ingliz tilida (yoki aralash) bo'lishi mumkin.
Quyidagi vazifalarni bajar va FAQAT JSON formatida javob qaytar:

1. language_detected: Audio qaysi tilda ekanligini aniqla ("uz", "ru", "en" yoki "mixed").
2. transcription: Audiodagi barcha gaplarni to'liq, aniq, tinish belgilari bilan matnga o'gir (verbatim transkripsiya). O'zbekcha sheva yoki so'zlashuv iboralarini to'g'ri tushunib yoz.
3. summary: Audioning qisqa va aniq mazmuni (xulosasi). Asosiy fikr nima haqida ekanligini 3-5 gapda tushuntir.
4. key_points: Audiodagi eng asosiy fikrlar va muhim faktlar ro'yxati (string massiv).
5. action_items: Audioda aytilgan aniq topshiriqlar, qilinishi kerak bo'lgan ishlar, harakatlar rejasi (string massiv). Agar aniq topshiriq bo'lmasa, bo'sh qoldir.
6. entities:
   - dates: Aytilgan sanalar, kunlar, vaqtlar va muddatlar (string massiv).
   - numbers_amounts: Aytilgan narxlar, summalar, raqamlar, foizlar yoki hisob-kitoblar (string massiv).
   - people_contacts: Ismlar, lavozimlar, telefon raqamlar yoki elektron manzillar (string massiv).
   - locations: Joy nomlari, manzillar, shaharlar (string massiv).

Javobni quyidagi aniq JSON formatida qaytar:
{
  "language_detected": "uz",
  "transcription": "...",
  "summary": "...",
  "key_points": ["...", "..."],
  "action_items": ["...", "..."],
  "entities": {
    "dates": ["..."],
    "numbers_amounts": ["..."],
    "people_contacts": ["..."],
    "locations": ["..."]
  }
}
''';

  // Prefs kalitlari
  static const String keyApiKey = 'user_gemini_api_key';
  static const String keyHistory = 'analysis_history_v1';
  static const String keyThemeMode = 'app_theme_mode';
}
