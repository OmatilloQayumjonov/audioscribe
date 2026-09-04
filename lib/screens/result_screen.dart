import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import '../models/audio_analysis_result.dart';
import '../services/storage_service.dart';
import '../widgets/audio_player_widget.dart';

class ResultScreen extends StatefulWidget {
  final AudioAnalysisResult result;

  const ResultScreen({Key? key, required this.result}) : super(key: key);

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final Set<int> _checkedActionItems = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _copyToClipboard(String text, String message) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _shareAll() {
    final buffer = StringBuffer();
    buffer.writeln('📋 ${widget.result.fileName} - Audio tahlili');
    buffer.writeln('🌐 Til: ${widget.result.formattedLanguage}');
    buffer.writeln('\n--- 📌 QISQACHA XULOSA ---');
    buffer.writeln(widget.result.summary);

    if (widget.result.actionItems.isNotEmpty) {
      buffer.writeln('\n--- ✅ TOPSHIRIQLAR VA VAZIFALAR ---');
      for (final item in widget.result.actionItems) {
        buffer.writeln('• $item');
      }
    }

    if (widget.result.keyPoints.isNotEmpty) {
      buffer.writeln('\n--- 💡 ASOSIY FIKRLAR ---');
      for (final item in widget.result.keyPoints) {
        buffer.writeln('• $item');
      }
    }

    buffer.writeln('\n--- 📝 TO\'LIQ TRANSKRIPSIYA ---');
    buffer.writeln(widget.result.transcription);

    Share.share(buffer.toString());
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasAudioFile = widget.result.filePath.isNotEmpty &&
        File(widget.result.filePath).existsSync();

    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.result.fileName,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            tooltip: 'Ulashish',
            onPressed: _shareAll,
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline),
            tooltip: 'O\'chirish',
            onPressed: () async {
              final confirm = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('O\'chirishni tasdiqlaysizmi?'),
                  content: const Text('Bu tahlil natijasi tarixdan o\'chiriladi.'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Yo\'q'),
                    ),
                    TextButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('O\'chirish', style: TextStyle(color: Colors.red)),
                    ),
                  ],
                ),
              );

              if (confirm == true) {
                await StorageService().deleteAnalysis(widget.result.id);
                if (mounted) {
                  Navigator.pop(context, true);
                }
              }
            },
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: theme.colorScheme.primary,
          indicatorWeight: 3,
          labelColor: theme.colorScheme.primary,
          unselectedLabelColor: Colors.grey,
          tabs: const [
            Tab(icon: Icon(Icons.analytics_outlined), text: 'Xulosa & Tahlil'),
            Tab(icon: Icon(Icons.subject), text: 'To\'liq Matn'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // 1-TAB: Xulosa va ma'lumotlar
          _buildSummaryTab(theme, hasAudioFile),
          // 2-TAB: To'liq transkripsiya
          _buildTranscriptionTab(theme),
        ],
      ),
    );
  }

  Widget _buildSummaryTab(ThemeData theme, bool hasAudioFile) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Audio Player (mavjud bo'lsa)
        if (hasAudioFile) ...[
          AudioPlayerWidget(
            audioPath: widget.result.filePath,
            title: widget.result.fileName,
          ),
          const SizedBox(height: 16),
        ],

        // Til va vaqt ko'rsatkichi
        Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: theme.colorScheme.primary.withOpacity(0.15),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: theme.colorScheme.primary.withOpacity(0.3),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.language, size: 16, color: theme.colorScheme.primary),
                  const SizedBox(width: 6),
                  Text(
                    widget.result.formattedLanguage,
                    style: TextStyle(
                      color: theme.colorScheme.primary,
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            if (widget.result.durationSeconds > 0)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.grey.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.timer_outlined, size: 16, color: Colors.grey),
                    const SizedBox(width: 6),
                    Text(
                      widget.result.formattedDuration,
                      style: const TextStyle(
                        color: Colors.grey,
                        fontWeight: FontWeight.w600,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
        const SizedBox(height: 16),

        // 1. Qisqacha Xulosa
        _buildSectionCard(
          theme: theme,
          icon: Icons.auto_awesome,
          iconColor: Colors.amber,
          title: 'Asosiy Xulosa',
          action: IconButton(
            icon: const Icon(Icons.copy, size: 20),
            tooltip: 'Nusxa olish',
            onPressed: () => _copyToClipboard(
              widget.result.summary,
              'Xulosa nusxalandi',
            ),
          ),
          child: Text(
            widget.result.summary.isNotEmpty
                ? widget.result.summary
                : 'Xulosa mavjud emas.',
            style: theme.textTheme.bodyLarge?.copyWith(height: 1.5),
          ),
        ),
        const SizedBox(height: 16),

        // 2. Vazifalar va Topshiriqlar (Action Items)
        if (widget.result.actionItems.isNotEmpty) ...[
          _buildSectionCard(
            theme: theme,
            icon: Icons.checklist_rounded,
            iconColor: Colors.greenAccent,
            title: 'Topshiriqlar va Vazifalar (${widget.result.actionItems.length})',
            child: Column(
              children: List.generate(widget.result.actionItems.length, (index) {
                final item = widget.result.actionItems[index];
                final isChecked = _checkedActionItems.contains(index);
                return CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  title: Text(
                    item,
                    style: TextStyle(
                      decoration: isChecked
                          ? TextDecoration.lineThrough
                          : TextDecoration.none,
                      color: isChecked ? Colors.grey : null,
                    ),
                  ),
                  value: isChecked,
                  onChanged: (val) {
                    setState(() {
                      if (val == true) {
                        _checkedActionItems.add(index);
                      } else {
                        _checkedActionItems.remove(index);
                      }
                    });
                  },
                );
              }),
            ),
          ),
          const SizedBox(height: 16),
        ],

        // 3. Asosiy Fikrlar (Key Points)
        if (widget.result.keyPoints.isNotEmpty) ...[
          _buildSectionCard(
            theme: theme,
            icon: Icons.lightbulb_outline,
            iconColor: Colors.cyanAccent,
            title: 'Muhim Nuqtalar',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: widget.result.keyPoints.map((point) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('• ', style: TextStyle(fontSize: 18, height: 1.3)),
                      Expanded(
                        child: Text(
                          point,
                          style: theme.textTheme.bodyMedium?.copyWith(height: 1.4),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 16),
        ],

        // 4. Muhim ma'lumotlar (Entities: Sanalar, narxlar, shaxslar)
        _buildEntitiesSection(theme),
      ],
    );
  }

  Widget _buildEntitiesSection(ThemeData theme) {
    final entities = widget.result.entities;
    final dates = entities['dates'] ?? [];
    final numbers = entities['numbers_amounts'] ?? [];
    final contacts = entities['people_contacts'] ?? [];
    final locations = entities['locations'] ?? [];

    if (dates.isEmpty && numbers.isEmpty && contacts.isEmpty && locations.isEmpty) {
      return const SizedBox.shrink();
    }

    return _buildSectionCard(
      theme: theme,
      icon: Icons.fingerprint,
      iconColor: Colors.deepPurpleAccent,
      title: 'Ajratib olingan ma\'lumotlar',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (dates.isNotEmpty) ...[
            _buildEntityGroup('🗓 Sanalar va muddatlar:', dates, Colors.blue),
            const SizedBox(height: 10),
          ],
          if (numbers.isNotEmpty) ...[
            _buildEntityGroup('💰 Narxlar, summalar va hisoblar:', numbers, Colors.amber),
            const SizedBox(height: 10),
          ],
          if (contacts.isNotEmpty) ...[
            _buildEntityGroup('👤 Shaxslar va kontaktlar:', contacts, Colors.teal),
            const SizedBox(height: 10),
          ],
          if (locations.isNotEmpty) ...[
            _buildEntityGroup('📍 Manzillar va joylar:', locations, Colors.redAccent),
          ],
        ],
      ),
    );
  }

  Widget _buildEntityGroup(String title, List<String> items, Color chipColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
        const SizedBox(height: 6),
        Wrap(
          spacing: 8,
          runSpacing: 6,
          children: items.map((item) {
            return Chip(
              backgroundColor: chipColor.withOpacity(0.12),
              side: BorderSide(color: chipColor.withOpacity(0.3)),
              padding: const EdgeInsets.symmetric(horizontal: 4),
              label: Text(
                item,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: chipColor,
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildTranscriptionTab(ThemeData theme) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Ovoz matni',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.copy, size: 20),
                  tooltip: 'Matnni nusxalash',
                  onPressed: () => _copyToClipboard(
                    widget.result.transcription,
                    'Transkripsiya nusxalandi',
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.share_outlined, size: 20),
                  tooltip: 'Matnni ulashish',
                  onPressed: () => Share.share(widget.result.transcription),
                ),
              ],
            ),
          ],
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: theme.brightness == Brightness.dark
                  ? Colors.white.withOpacity(0.08)
                  : Colors.black.withOpacity(0.06),
            ),
          ),
          child: SelectableText(
            widget.result.transcription.isNotEmpty
                ? widget.result.transcription
                : 'Transkripsiya bo\'sh.',
            style: theme.textTheme.bodyLarge?.copyWith(
              height: 1.6,
              fontSize: 15,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSectionCard({
    required ThemeData theme,
    required IconData icon,
    required Color iconColor,
    required String title,
    Widget? action,
    required Widget child,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: theme.brightness == Brightness.dark
              ? Colors.white.withOpacity(0.08)
              : Colors.black.withOpacity(0.06),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: iconColor, size: 22),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              if (action != null) action,
            ],
          ),
          const Divider(height: 24),
          child,
        ],
      ),
    );
  }
}
