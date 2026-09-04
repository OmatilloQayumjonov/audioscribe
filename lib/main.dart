import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/home_screen.dart';
import 'services/storage_service.dart';
import 'utils/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Tizim holat paneli (StatusBar) ranglarini sozlash
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );

  // Mahalliy ma'lumotlar omborini ishga tushirish
  await StorageService().init();

  runApp(const AudioScribeApp());
}

class AudioScribeApp extends StatefulWidget {
  const AudioScribeApp({Key? key}) : super(key: key);

  @override
  State<AudioScribeApp> createState() => _AudioScribeAppState();
}

class _AudioScribeAppState extends State<AudioScribeApp> {
  late bool _isDarkMode;

  @override
  void initState() {
    super.initState();
    _isDarkMode = StorageService().isDarkMode();
  }

  void _toggleTheme() {
    setState(() {
      _isDarkMode = StorageService().isDarkMode();
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AudioScribe AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: _isDarkMode ? ThemeMode.dark : ThemeMode.light,
      home: HomeScreen(
        onThemeChanged: _toggleTheme,
      ),
    );
  }
}
