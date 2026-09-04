import 'dart:convert';

class AudioAnalysisResult {
  final String id;
  final String fileName;
  final String filePath;
  final int fileSizeBytes;
  final int durationSeconds;
  final DateTime createdAt;
  final String languageDetected;
  final String transcription;
  final String summary;
  final List<String> keyPoints;
  final List<String> actionItems;
  final Map<String, List<String>> entities;

  AudioAnalysisResult({
    required this.id,
    required this.fileName,
    required this.filePath,
    required this.fileSizeBytes,
    required this.durationSeconds,
    required this.createdAt,
    required this.languageDetected,
    required this.transcription,
    required this.summary,
    required this.keyPoints,
    required this.actionItems,
    required this.entities,
  });

  String get formattedLanguage {
    switch (languageDetected.toLowerCase()) {
      case 'uz':
        return "O'zbekcha";
      case 'ru':
        return 'Ruscha';
      case 'en':
        return 'Inglizcha';
      case 'mixed':
        return 'Aralash (Ko\'p tilli)';
      default:
        return languageDetected.toUpperCase();
    }
  }

  String get formattedDuration {
    final minutes = (durationSeconds ~/ 60).toString().padLeft(2, '0');
    final seconds = (durationSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'fileName': fileName,
      'filePath': filePath,
      'fileSizeBytes': fileSizeBytes,
      'durationSeconds': durationSeconds,
      'createdAt': createdAt.toIso8601String(),
      'languageDetected': languageDetected,
      'transcription': transcription,
      'summary': summary,
      'keyPoints': keyPoints,
      'actionItems': actionItems,
      'entities': entities,
    };
  }

  factory AudioAnalysisResult.fromJson(Map<String, dynamic> json) {
    // Entities xavfsiz o'qish
    final Map<String, List<String>> parsedEntities = {};
    if (json['entities'] is Map) {
      final rawEntities = json['entities'] as Map;
      rawEntities.forEach((key, val) {
        if (val is List) {
          parsedEntities[key.toString()] =
              val.map((item) => item.toString()).toList();
        }
      });
    }

    return AudioAnalysisResult(
      id: json['id'] as String? ?? DateTime.now().millisecondsSinceEpoch.toString(),
      fileName: json['fileName'] as String? ?? 'Audio',
      filePath: json['filePath'] as String? ?? '',
      fileSizeBytes: json['fileSizeBytes'] as int? ?? 0,
      durationSeconds: json['durationSeconds'] as int? ?? 0,
      createdAt: json['createdAt'] != null
          ? DateTime.tryParse(json['createdAt'] as String) ?? DateTime.now()
          : DateTime.now(),
      languageDetected: json['languageDetected'] as String? ?? 'uz',
      transcription: json['transcription'] as String? ?? '',
      summary: json['summary'] as String? ?? '',
      keyPoints: (json['keyPoints'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      actionItems: (json['actionItems'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      entities: parsedEntities,
    );
  }

  factory AudioAnalysisResult.fromGeminiJson({
    required Map<String, dynamic> aiJson,
    required String filePath,
    required String fileName,
    required int fileSizeBytes,
    required int durationSeconds,
  }) {
    final Map<String, List<String>> parsedEntities = {};
    if (aiJson['entities'] is Map) {
      final rawEntities = aiJson['entities'] as Map;
      rawEntities.forEach((key, val) {
        if (val is List) {
          parsedEntities[key.toString()] =
              val.map((item) => item.toString()).toList();
        }
      });
    }

    return AudioAnalysisResult(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      fileName: fileName,
      filePath: filePath,
      fileSizeBytes: fileSizeBytes,
      durationSeconds: durationSeconds,
      createdAt: DateTime.now(),
      languageDetected: aiJson['language_detected'] as String? ?? 'uz',
      transcription: aiJson['transcription'] as String? ?? '',
      summary: aiJson['summary'] as String? ?? '',
      keyPoints: (aiJson['key_points'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      actionItems: (aiJson['action_items'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      entities: parsedEntities,
    );
  }
}
