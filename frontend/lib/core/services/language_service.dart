import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LanguageService with ChangeNotifier {
  String _language = 'en';
  static const Map<String, String> languageCodes = {
    'en': 'English',
    'hi': 'Hindi',
  };

  String get language => _language;

  String get languageName => languageCodes[_language] ?? 'English';

  LanguageService() {
    _loadLanguage();
  }

  Future<void> _loadLanguage() async {
    final prefs = await SharedPreferences.getInstance();
    final savedLanguage = prefs.getString('language');
    if (savedLanguage != null && languageCodes.containsKey(savedLanguage)) {
      _language = savedLanguage;
    } else {
      _language = 'en'; // default
    }
    notifyListeners();
  }

  Future<void> setLanguage(String lang) async {
    if (!languageCodes.containsKey(lang)) return;

    _language = lang;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('language', lang);
    notifyListeners();
  }

  void toggleLanguage() {
    final newLanguage = _language == 'en' ? 'hi' : 'en';
    setLanguage(newLanguage);
  }
}