import 'package:flutter_test/flutter_test.dart';
import 'package:audioscribe/models/audio_analysis_result.dart';

void main() {
  group('AudioAnalysisResult Tests', () {
    test('fromGeminiJson to\'g\'ri parse qiladi', () {
      final geminiMockJson = {
        'language_detected': 'uz',
        'transcription': 'Salom, ertaga soat 10:00 da majlis bo\'ladi. Narxi 500 dollar.',
        'summary': 'Ertangi majlis va narx haqida ovozli xabar.',
        'key_points': ['Ertaga majlis', 'Narx 500 dollar'],
        'action_items': ['Soat 10:00 da qatnashish'],
        'entities': {
          'dates': ['ertaga', '10:00'],
          'numbers_amounts': ['500 dollar'],
          'people_contacts': ['Rahbar'],
          'locations': ['Ofis']
        }
      };

      final result = AudioAnalysisResult.fromGeminiJson(
        aiJson: geminiMockJson,
        filePath: '/storage/sample.mp3',
        fileName: 'sample.mp3',
        fileSizeBytes: 102400,
        durationSeconds: 45,
      );

      expect(result.languageDetected, 'uz');
      expect(result.formattedLanguage, "O'zbekcha");
      expect(result.transcription, contains('Salom'));
      expect(result.summary, contains('majlis'));
      expect(result.keyPoints.length, 2);
      expect(result.actionItems.length, 1);
      expect(result.entities['dates']?.length, 2);
      expect(result.entities['numbers_amounts']?.first, '500 dollar');
      expect(result.formattedDuration, '00:45');
    });

    test('toJson va fromJson to\'liq ma\'lumotni saqlaydi va qayta tiklaydi', () {
      final original = AudioAnalysisResult(
        id: 'test_123',
        fileName: 'test.mp3',
        filePath: '/path/test.mp3',
        fileSizeBytes: 2048,
        durationSeconds: 75,
        createdAt: DateTime(2026, 9, 4, 12, 0),
        languageDetected: 'ru',
        transcription: 'Привет, нужно отправить отчет до пятницы.',
        summary: 'Отправка отчета до пятницы.',
        keyPoints: ['Срок в пятницу'],
        actionItems: ['Отправить отчет'],
        entities: {
          'dates': ['пятница'],
        },
      );

      final jsonMap = original.toJson();
      final restored = AudioAnalysisResult.fromJson(jsonMap);

      expect(restored.id, original.id);
      expect(restored.fileName, original.fileName);
      expect(restored.languageDetected, 'ru');
      expect(restored.formattedLanguage, 'Ruscha');
      expect(restored.durationSeconds, 75);
      expect(restored.formattedDuration, '01:15');
      expect(restored.keyPoints, original.keyPoints);
      expect(restored.actionItems, original.actionItems);
      expect(restored.entities['dates']?.first, 'пятница');
    });
  });
}
