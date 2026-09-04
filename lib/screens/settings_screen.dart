import 'package:flutter/material.dart';
import '../services/storage_service.dart';

class SettingsScreen extends StatefulWidget {
  final VoidCallback onThemeChanged;

  const SettingsScreen({Key? key, required this.onThemeChanged}) : super(key: key);

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final TextEditingController _apiKeyController = TextEditingController();
  bool _obscureApiKey = true;
  bool _isDarkMode = true;

  @override
  void initState() {
    super.initState();
    _apiKeyController.text = StorageService().getApiKey();
    _isDarkMode = StorageService().isDarkMode();
  }

  @override
  void dispose() {
    _apiKeyController.dispose();
    super.dispose();
  }

  Future<void> _saveApiKey() async {
    await StorageService().setApiKey(_apiKeyController.text.trim());
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('API kalit muvaffaqiyatli saqlandi!'),
          backgroundColor: Colors.green,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sozlamalar'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Gemini API bo'limi
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.vpn_key_outlined, color: Colors.amber),
                      const SizedBox(width: 10),
                      Text(
                        'Google Gemini API Kaliti',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Audio yozuvlarni yuqori aniqlikda tahlil qilish uchun Google AI Studio API kaliti zarur.',
                    style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _apiKeyController,
                    obscureText: _obscureApiKey,
                    decoration: InputDecoration(
                      labelText: 'API Kalit (AIzaSy...)',
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscureApiKey ? Icons.visibility : Icons.visibility_off,
                        ),
                        onPressed: () {
                          setState(() {
                            _obscureApiKey = !_obscureApiKey;
                          });
                        },
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _saveApiKey,
                      icon: const Icon(Icons.save),
                      label: const Text('Kalitni saqlash'),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.info_outline, size: 20, color: Colors.blueAccent),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Bepul API kalit olish manzili: aistudio.google.com/app/apikey',
                            style: theme.textTheme.bodySmall?.copyWith(
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Mavzu va ko'rinish
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  secondary: Icon(
                    _isDarkMode ? Icons.dark_mode : Icons.light_mode,
                    color: theme.colorScheme.primary,
                  ),
                  title: const Text('Qorong\'u mavzu (Dark mode)'),
                  subtitle: Text(
                    _isDarkMode ? 'Hozir yoqilgan' : 'Yorug\' mavzu yoqilgan',
                  ),
                  value: _isDarkMode,
                  onChanged: (val) async {
                    setState(() {
                      _isDarkMode = val;
                    });
                    await StorageService().setDarkMode(val);
                    widget.onThemeChanged();
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Ilova haqida
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.info_outline, color: Colors.cyan),
                      const SizedBox(width: 10),
                      Text(
                        'Ilova haqida',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const Divider(height: 24),
                  const Text(
                    'AudioScribe AI - o\'zbek, rus va ingliz tillaridagi audio xabarlar, '
                    'MP3 fayllarni aqlli transkripsiya qilish va xulosalash uchun mo\'ljallangan.',
                    style: TextStyle(height: 1.4),
                  ),
                  const SizedBox(height: 12),
                  const Text('Versiya: 1.0.0 (Release)'),
                  const SizedBox(height: 4),
                  const Text('Platforma: Android (APK)'),
                  const SizedBox(height: 4),
                  const Text('AI Engine: Google Gemini Multimodal Audio'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
