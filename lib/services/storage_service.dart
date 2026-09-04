import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/audio_analysis_result.dart';
import '../utils/constants.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  SharedPreferences? _prefs;

  Future<void> init() async {
    _prefs ??= await SharedPreferences.getInstance();
  }

  // API Kalit
  String getApiKey() {
    return _prefs?.getString(AppConstants.keyApiKey) ?? '';
  }

  Future<void> setApiKey(String key) async {
    await _prefs?.setString(AppConstants.keyApiKey, key.trim());
  }

  // Tarix (History)
  List<AudioAnalysisResult> getHistory() {
    final rawList = _prefs?.getStringList(AppConstants.keyHistory) ?? [];
    final List<AudioAnalysisResult> results = [];
    for (final item in rawList) {
      try {
        final map = jsonDecode(item) as Map<String, dynamic>;
        results.add(AudioAnalysisResult.fromJson(map));
      } catch (_) {}
    }
    // Yangilari yuqorida turishi uchun sort qilish
    results.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return results;
  }

  Future<void> saveAnalysis(AudioAnalysisResult result) async {
    final current = getHistory();
    // Agar id mavjud bo'lsa yangilash, bo'lmasa qo'shish
    current.removeWhere((item) => item.id == result.id);
    current.insert(0, result);

    final encodedList = current.map((e) => jsonEncode(e.toJson())).toList();
    await _prefs?.setStringList(AppConstants.keyHistory, encodedList);
  }

  Future<void> deleteAnalysis(String id) async {
    final current = getHistory();
    current.removeWhere((item) => item.id == id);
    final encodedList = current.map((e) => jsonEncode(e.toJson())).toList();
    await _prefs?.setStringList(AppConstants.keyHistory, encodedList);
  }

  Future<void> clearHistory() async {
    await _prefs?.remove(AppConstants.keyHistory);
  }

  // Mavzu (Dark/Light)
  bool isDarkMode() {
    return _prefs?.getBool(AppConstants.keyThemeMode) ?? true;
  }

  Future<void> setDarkMode(bool isDark) async {
    await _prefs?.setBool(AppConstants.keyThemeMode, isDark);
  }
}
