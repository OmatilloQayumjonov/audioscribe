import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/audio_analysis_result.dart';
import '../utils/constants.dart';

class GeminiAudioService {
  final String apiKey;

  GeminiAudioService({required this.apiKey});

  String _getMimeType(String filePath) {
    final lower = filePath.toLowerCase();
    if (lower.endsWith('.mp3')) return 'audio/mp3';
    if (lower.endsWith('.m4a')) return 'audio/m4a';
    if (lower.endsWith('.wav')) return 'audio/wav';
    if (lower.endsWith('.ogg') || lower.endsWith('.oga') || lower.endsWith('.opus')) {
      return 'audio/ogg';
    }
    if (lower.endsWith('.aac')) return 'audio/aac';
    if (lower.endsWith('.flac')) return 'audio/flac';
    return 'audio/mp3';
  }

  Future<AudioAnalysisResult> analyzeAudioFile({
    required File audioFile,
    required String fileName,
    int durationSeconds = 0,
  }) async {
    if (apiKey.trim().isEmpty) {
      throw Exception(
        'Gemini API kaliti kiritilmagan! Iltimos, Sozlamalar bo\'limida bepul API kalitni kiriting.',
      );
    }

    if (!await audioFile.exists()) {
      throw Exception('Audio fayl topilmadi: ${audioFile.path}');
    }

    final bytes = await audioFile.readAsBytes();
    final fileSizeBytes = bytes.length;
    final base64Audio = base64Encode(bytes);
    final mimeType = _getMimeType(audioFile.path);

    final url = Uri.parse(
      '${AppConstants.geminiApiEndpoint}/${AppConstants.geminiModel}:generateContent?key=$apiKey',
    );

    final requestBody = {
      'contents': [
        {
          'parts': [
            {
              'inline_data': {
                'mime_type': mimeType,
                'data': base64Audio,
              }
            },
            {
              'text': AppConstants.geminiAudioSystemPrompt,
            }
          ]
        }
      ],
      'generationConfig': {
        'response_mime_type': 'application/json',
        'temperature': 0.2,
      }
    };

    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode(requestBody),
    );

    if (response.statusCode != 200) {
      String errorMessage = 'Server xatosi: ${response.statusCode}';
      try {
        final errJson = jsonDecode(response.body);
        if (errJson['error']?['message'] != null) {
          errorMessage = errJson['error']['message'];
        }
      } catch (_) {}
      throw Exception(errorMessage);
    }

    final responseJson = jsonDecode(response.body);
    final candidates = responseJson['candidates'] as List?;
    if (candidates == null || candidates.isEmpty) {
      throw Exception('AI tomonidan javob qaytarilmadi.');
    }

    final parts = candidates[0]['content']?['parts'] as List?;
    if (parts == null || parts.isEmpty) {
      throw Exception('AI javobi bo\'sh.');
    }

    String rawText = parts[0]['text'] as String? ?? '';
    rawText = rawText.trim();

    // Agar markdown formatida (```json ... ```) qaytgan bo'lsa tozalash
    if (rawText.startsWith('```json')) {
      rawText = rawText.substring(7);
    } else if (rawText.startsWith('```')) {
      rawText = rawText.substring(3);
    }
    if (rawText.endsWith('```')) {
      rawText = rawText.substring(0, rawText.length - 3);
    }
    rawText = rawText.trim();

    Map<String, dynamic> parsedAiJson;
    try {
      parsedAiJson = jsonDecode(rawText) as Map<String, dynamic>;
    } catch (e) {
      // JSON parse xatosi bo'lsa, xom matnni transkripsiya sifatida saqlash
      parsedAiJson = {
        'language_detected': 'uz',
        'transcription': rawText,
        'summary': 'Transkripsiyadan xulosa chiqarildi.',
        'key_points': <String>[],
        'action_items': <String>[],
        'entities': <String, dynamic>{},
      };
    }

    return AudioAnalysisResult.fromGeminiJson(
      aiJson: parsedAiJson,
      filePath: audioFile.path,
      fileName: fileName,
      fileSizeBytes: fileSizeBytes,
      durationSeconds: durationSeconds,
    );
  }
}
