import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/nfc/nfc_exception.dart';
import '../../../../core/nfc/nfc_providers.dart';
import '../../../../core/providers/core_providers.dart';

class ScanPage extends ConsumerStatefulWidget {
  const ScanPage({super.key});

  @override
  ConsumerState<ScanPage> createState() => _ScanPageState();
}

class _ScanPageState extends ConsumerState<ScanPage> {
  final _copyCodeController = TextEditingController();
  final _tagUidController = TextEditingController();
  final _placeController = TextEditingController();
  final _textController = TextEditingController();
  bool _submitting = false;
  bool _checkingNfc = true;
  bool _nfcAvailable = false;
  String? _nfcStatusMessage;

  @override
  void initState() {
    super.initState();
    _checkNfcAvailability();
  }

  @override
  void dispose() {
    _copyCodeController.dispose();
    _tagUidController.dispose();
    _placeController.dispose();
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Сканирование')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Экран поддерживает и ручной ввод, и native NFC через platform channel. Пока платформенный Android-слой не подключён, ручной fallback остаётся основным сценарием.',
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('NFC', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 8),
                  Text(
                    _checkingNfc
                        ? 'Проверяем доступность NFC...'
                        : _nfcAvailable
                            ? 'NFC доступен. Можно считать метку, зарегистрировать scan и сразу открыть экземпляр.'
                            : (_nfcStatusMessage ?? 'NFC пока недоступен. Используйте ручной ввод UID.'),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: [
                      ElevatedButton(
                        onPressed: _checkingNfc || !_nfcAvailable || _submitting ? null : _scanNfcTag,
                        child: const Text('Считать NFC-метку'),
                      ),
                      OutlinedButton(
                        onPressed: _checkingNfc ? null : _checkNfcAvailability,
                        child: const Text('Проверить NFC снова'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _copyCodeController,
            decoration: const InputDecoration(labelText: 'Код экземпляра'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _tagUidController,
            decoration: const InputDecoration(labelText: 'UID NFC-метки'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _placeController,
            decoration: const InputDecoration(labelText: 'Место'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _textController,
            minLines: 3,
            maxLines: 5,
            decoration: const InputDecoration(labelText: 'Комментарий'),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _submitting ? null : _submit,
            child: Text(_submitting ? 'Сохраняем...' : 'Сохранить scan-событие'),
          ),
        ],
      ),
    );
  }

  Future<void> _checkNfcAvailability() async {
    setState(() {
      _checkingNfc = true;
      _nfcStatusMessage = null;
    });
    try {
      final available = await ref.read(nfcServiceProvider).isAvailable();
      if (!mounted) {
        return;
      }
      setState(() {
        _nfcAvailable = available;
        _checkingNfc = false;
        if (!available) {
          _nfcStatusMessage = 'На этой сборке NFC ещё не подключён или устройство его не поддерживает.';
        }
      });
    } on NfcException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _nfcAvailable = false;
        _checkingNfc = false;
        _nfcStatusMessage = error.message;
      });
    }
  }

  Future<void> _scanNfcTag() async {
    try {
      final result = await ref.read(nfcServiceProvider).scanTag();
      if (!mounted) {
        return;
      }
      setState(() {
        _tagUidController.text = result.uid;
        _nfcStatusMessage = 'UID считан: ${result.uid}';
      });
      await _submit();
    } on NfcException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _nfcStatusMessage = error.message;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.message)),
      );
    }
  }

  Future<void> _submit() async {
    setState(() => _submitting = true);
    try {
      final response = await ref.read(apiClientProvider).dio.post<Map<String, dynamic>>(
            '/scan',
            data: {
              'copy_code': _copyCodeController.text.trim(),
              'tag_uid': _tagUidController.text.trim(),
              'place_text': _placeController.text.trim(),
              'text': _textController.text.trim(),
            },
          );
      final copyId = response.data?['copy_id'] as int?;
      if (!mounted) {
        return;
      }
      _copyCodeController.clear();
      _tagUidController.clear();
      _placeController.clear();
      _textController.clear();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            copyId == null
                ? 'Scan-событие сохранено.'
                : 'Метка распознана. Открываем экземпляр книги.',
          ),
        ),
      );
      if (copyId != null) {
        context.push('/copies/$copyId');
      }
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Не удалось сохранить scan-событие: $error')),
      );
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }
}
