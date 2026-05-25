import 'package:flutter/services.dart';

import 'nfc_exception.dart';

class NfcScanResult {
  const NfcScanResult({
    required this.uid,
    this.raw = const <String, dynamic>{},
  });

  final String uid;
  final Map<String, dynamic> raw;
}

abstract class NfcService {
  Future<bool> isAvailable();

  Future<NfcScanResult> scanTag();
}

class MethodChannelNfcService implements NfcService {
  MethodChannelNfcService([MethodChannel? channel])
      : _channel = channel ?? const MethodChannel('booktrail/nfc');

  final MethodChannel _channel;

  @override
  Future<bool> isAvailable() async {
    try {
      final result = await _channel.invokeMethod<bool>('isAvailable');
      return result ?? false;
    } on MissingPluginException {
      return false;
    } on PlatformException catch (error) {
      throw NfcException(
        error.message ?? 'Не удалось проверить доступность NFC.',
        code: error.code,
      );
    }
  }

  @override
  Future<NfcScanResult> scanTag() async {
    try {
      final result = await _channel.invokeMapMethod<String, dynamic>('scanTag');
      if (result == null) {
        throw const NfcException('Платформа не вернула данные NFC-метки.');
      }
      final uid = (result['uid'] ?? '').toString().trim().toUpperCase();
      if (uid.isEmpty) {
        throw const NfcException('UID NFC-метки пустой.');
      }
      return NfcScanResult(uid: uid, raw: result);
    } on MissingPluginException {
      throw const NfcException(
        'Платформенный NFC-слой ещё не подключён. После генерации Android проекта добавьте Kotlin handler.',
        code: 'missing_plugin',
      );
    } on PlatformException catch (error) {
      throw NfcException(
        error.message ?? 'Не удалось считать NFC-метку.',
        code: error.code,
      );
    }
  }
}
