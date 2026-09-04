import 'dart:async';
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';
import '../models/audio_analysis_result.dart';
import '../services/gemini_audio_service.dart';
import '../services/storage_service.dart';
import '../widgets/voice_recorder_widget.dart';
import 'history_screen.dart';
import 'result_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  final VoidCallback onThemeChanged;

  const HomeScreen({Key? key, required this.onThemeChanged}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = false;
  String _loadingStatus = '';
  StreamSubscription? _intentSub;

  @override
  void initState() {
    super.initState();
    _initShareIntent();
  }

  @override
  void dispose() {
    _intentSub?.cancel();
    super.dispose();
  }

  void _initShareIntent() {
    // Telegram / WhatsApp orqali ilovaga ulashilgan audio fayllarni qabul qilish
    _intentSub = ReceiveSharingIntent.getMediaStream().listen(
      (List<SharedMediaFile> value) {
        if (value.isNotEmpty && mounted) {
          final audioFile = value.first;
          _processAudio(audioFile.path, 0, fileName: 'Telegram/WhatsApp ovozi');
        }
      },
      onError: (err) {
        debugPrint('Share intent stream error: $err');
      },
    );

    ReceiveSharingIntent.getInitialMedia().then((List<SharedMediaFile> value) {
      if (value.isNotEmpty && mounted) {
        final audioFile = value.first;
        _processAudio(audioFile.path, 0, fileName: 'Telegram/WhatsApp ovozi');
        ReceiveSharingIntent.reset();
      }
    });
  }

  Future<void> _pickAudioFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['mp3', 'm4a', 'wav', 'ogg', 'aac', 'flac', 'opus'],
      );

      if (result != null && result.files.single.path != null) {
        final path = result.files.single.path!;
        final name = result.files.single.name;
        await _processAudio(path, 0, fileName: name);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Faylni ochishda xatolik: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _processAudio(
    String filePath,
    int durationSeconds, {
    String? fileName,
  }) async {
    final apiKey = StorageService().getApiKey();
    if (apiKey.isEmpty) {
      _showApiKeyRequiredDialog();
      return;
    }

    final file = File(filePath);
    if (!await file.exists()) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Audio fayl topilmadi yoki o\'qib bo\'lmadi.'),
            backgroundColor: Colors.red,
          ),
        );
      }
      return;
    }

    final resolvedFileName = fileName ??
        'Audio_${DateTime.now().hour}_${DateTime.now().minute}_${DateTime.now().second}';

    setState(() {
      _isLoading = true;
      _loadingStatus = 'Audio yuklanmoqda va AI nutqni tinglamoqda...';
    });

    try {
      final service = GeminiAudioService(apiKey: apiKey);

      setState(() {
        _loadingStatus = 'O\'zbek, rus yoki inglizcha matnga o\'girilmoqda...';
      });

      final analysis = await service.analyzeAudioFile(
        audioFile: file,
        fileName: resolvedFileName,
        durationSeconds: durationSeconds,
      );

      setState(() {
        _loadingStatus = 'Xulosa va muhim ma\'lumotlar saqlanmoqda...';
      });

      await StorageService().saveAnalysis(analysis);

      if (mounted) {
        setState(() {
          _isLoading = false;
        });

        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ResultScreen(result: analysis),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });

        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Row(
              children: [
                Icon(Icons.error_outline, color: Colors.red),
                SizedBox(width: 8),
                Text('Xatolik yuz berdi'),
              ],
            ),
            content: Text(
              e.toString().replaceAll('Exception: ', ''),
              style: const TextStyle(fontSize: 14),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Tushundim'),
              ),
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(ctx);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => SettingsScreen(
                        onThemeChanged: widget.onThemeChanged,
                      ),
                    ),
                  );
                },
                child: const Text('Sozlamalar'),
              ),
            ],
          ),
        );
      }
    }
  }

  void _showApiKeyRequiredDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.key, color: Colors.amber),
            SizedBox(width: 8),
            Text('API Kalit zarur'),
          ],
        ),
        content: const Text(
          'Audioni tahlil qilish uchun Google Gemini API kalitini kiritishingiz kerak.\n\n'
          'Uni Sozlamalar bo\'limida bir marta kiritib qo\'yasiz (bepul).',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Keyinroq'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => SettingsScreen(
                    onThemeChanged: widget.onThemeChanged,
                  ),
                ),
              );
            },
            child: const Text('Sozlamalarga o\'tish'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final history = StorageService().getHistory();
    final recentHistory = history.take(3).toList();

    return Stack(
      children: [
        Scaffold(
          appBar: AppBar(
            title: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primary,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.graphic_eq, color: Colors.white, size: 20),
                ),
                const SizedBox(width: 12),
                const Text(
                  'AudioScribe AI',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20),
                ),
              ],
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.history),
                tooltip: 'Tarix',
                onPressed: () async {
                  await Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const HistoryScreen()),
                  );
                  setState(() {});
                },
              ),
              IconButton(
                icon: const Icon(Icons.settings_outlined),
                tooltip: 'Sozlamalar',
                onPressed: () async {
                  await Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => SettingsScreen(
                        onThemeChanged: widget.onThemeChanged,
                      ),
                    ),
                  );
                  setState(() {});
                },
              ),
            ],
          ),
          body: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              // Banner sarlavhasi
              Text(
                "Ovozli xabar va MP3'larni\nmatnga o'giring va xulosalang",
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                "O'zbekcha, Ruscha va Inglizcha nutqni avtomatik taniydi",
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: Colors.grey,
                ),
              ),
              const SizedBox(height: 24),

              // 1. Ovoz yozish vidjeti
              VoiceRecorderWidget(
                onRecordingComplete: (filePath, duration) {
                  _processAudio(
                    filePath,
                    duration,
                    fileName:
                        "Yozuv_${DateTime.now().hour}_${DateTime.now().minute}",
                  );
                },
              ),
              const SizedBox(height: 16),

              // 2. MP3 / Audio fayl yuklash kartasi
              InkWell(
                onTap: _pickAudioFile,
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surface,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: theme.brightness == Brightness.dark
                          ? Colors.white.withOpacity(0.08)
                          : Colors.black.withOpacity(0.06),
                    ),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.secondary.withOpacity(0.15),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.audio_file_outlined,
                          color: theme.colorScheme.secondary,
                          size: 28,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'MP3 / Audio fayl tanlash',
                              style: theme.textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'MP3, M4A, WAV, OGG, AAC formatlar',
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: Colors.grey,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.file_upload_outlined, color: Colors.grey),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // 3. Telegram / WhatsApp yo'riqnoma kartasi
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blueAccent.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: Colors.blueAccent.withOpacity(0.2),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.telegram, color: Colors.blueAccent, size: 28),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Telegram yoki WhatsApp ovozlari',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Messanjerda ovozli xabarni "Share / Ulashish" qilib, AudioScribe AI ilovasini tanlang!',
                            style: theme.textTheme.bodySmall?.copyWith(
                              height: 1.3,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 28),

              // 4. Oxirgi tahlillar bo'limi
              if (recentHistory.isNotEmpty) ...[
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Oxirgi tahlillar',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    TextButton(
                      onPressed: () async {
                        await Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const HistoryScreen(),
                          ),
                        );
                        setState(() {});
                      },
                      child: const Text('Hammasi'),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: recentHistory.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final item = recentHistory[index];
                    return Card(
                      margin: EdgeInsets.zero,
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor:
                              theme.colorScheme.primary.withOpacity(0.12),
                          foregroundColor: theme.colorScheme.primary,
                          child: const Icon(Icons.text_snippet_outlined, size: 20),
                        ),
                        title: Text(
                          item.fileName,
                          style: const TextStyle(fontWeight: FontWeight.w600),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        subtitle: Text(
                          item.summary.isNotEmpty
                              ? item.summary
                              : item.transcription,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                        trailing: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            color: theme.colorScheme.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            item.formattedLanguage,
                            style: TextStyle(
                              fontSize: 11,
                              color: theme.colorScheme.primary,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        onTap: () async {
                          await Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => ResultScreen(result: item),
                            ),
                          );
                          setState(() {});
                        },
                      ),
                    );
                  },
                ),
              ],
            ],
          ),
        ),

        // Yuklanish holati (Loading Overlay)
        if (_isLoading)
          Container(
            color: Colors.black.withOpacity(0.7),
            child: Center(
              child: Card(
                elevation: 8,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const CircularProgressIndicator(),
                      const SizedBox(height: 20),
                      Text(
                        _loadingStatus,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Iltimos, kuting...',
                        style: TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
