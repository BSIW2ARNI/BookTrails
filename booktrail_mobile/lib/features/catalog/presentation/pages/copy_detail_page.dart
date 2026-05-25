import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/widgets/async_value_view.dart';
import '../../application/catalog_providers.dart';
import '../../data/catalog_repository.dart';
import '../../domain/entities/copy_detail.dart';

class CopyDetailPage extends ConsumerWidget {
  const CopyDetailPage({required this.copyId, super.key});

  final int copyId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detail = ref.watch(copyDetailProvider(copyId));
    return Scaffold(
      appBar: AppBar(title: const Text('Экземпляр')),
      body: AsyncValueView<CopyDetail>(
        value: detail,
        onRetry: () => ref.invalidate(copyDetailProvider(copyId)),
        data: (copy) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(copy.code, style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 8),
              Text(copy.bookTitle, style: Theme.of(context).textTheme.bodyLarge),
              const SizedBox(height: 8),
              Text('Статус: ${copy.statusTitle}'),
              const SizedBox(height: 8),
              Text(_buildAvailabilityText(copy)),
              const SizedBox(height: 8),
              Text('Активная NFC-метка: ${copy.activeTagUid ?? 'не привязана'}'),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  ElevatedButton(
                    onPressed: () => _showMoveSheet(context, ref, copy),
                    child: const Text('Добавить событие'),
                  ),
                  ElevatedButton(
                    onPressed: () => _showBindSheet(context, ref, copy),
                    child: Text(copy.activeTagUid == null ? 'Привязать NFC' : 'Сменить NFC'),
                  ),
                  if (copy.canUpdateStatus)
                    OutlinedButton(
                      onPressed: () => _showStatusSheet(context, ref, copy),
                      child: const Text('Изменить статус'),
                    ),
                  if (copy.activeTagUid != null)
                    OutlinedButton(
                      onPressed: () async {
                        await ref.read(catalogRepositoryProvider).unbindTag(copyId: copy.id);
                        ref.invalidate(copyDetailProvider(copy.id));
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('NFC-метка отвязана.')),
                          );
                        }
                      },
                      child: const Text('Отвязать NFC'),
                    ),
                ],
              ),
              const SizedBox(height: 20),
              Text('Маршрут', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              if (copy.moves.isEmpty) const Text('Событий пока нет.'),
              for (final move in copy.moves)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(move.eventTitle, style: Theme.of(context).textTheme.titleLarge),
                        const SizedBox(height: 6),
                        Text(move.dateTime),
                        if (move.placeText.isNotEmpty) ...[
                          const SizedBox(height: 6),
                          Text(move.placeText),
                        ],
                        if (move.text.isNotEmpty) ...[
                          const SizedBox(height: 10),
                          Text(move.text),
                        ],
                      ],
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  String _buildAvailabilityText(CopyDetail copy) {
    if (copy.statusCode != 'with_reader') {
      return 'Наличие: сейчас не у читателя';
    }
    if (copy.isHeldByCurrentUser) {
      return 'Наличие: книга у вас на руках';
    }
    if ((copy.holderDisplayName ?? '').isNotEmpty) {
      return 'Наличие: на руках у ${copy.holderDisplayName}';
    }
    return 'Наличие: книга у читателя, но держатель не указан';
  }

  Future<void> _showMoveSheet(
    BuildContext context,
    WidgetRef ref,
    CopyDetail copy,
  ) async {
    final eventTypeController = TextEditingController(text: 'transfer');
    final placeController = TextEditingController();
    final textController = TextEditingController();

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return Padding(
          padding: EdgeInsets.fromLTRB(
            16,
            16,
            16,
            16 + MediaQuery.of(context).viewInsets.bottom,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: eventTypeController,
                decoration: const InputDecoration(
                  labelText: 'Тип события',
                  helperText: 'Например: transfer, waiting, prep',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: placeController,
                decoration: const InputDecoration(labelText: 'Место'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: textController,
                minLines: 3,
                maxLines: 5,
                decoration: const InputDecoration(labelText: 'Комментарий'),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  await ref.read(catalogRepositoryProvider).createMove(
                        copyId: copy.id,
                        eventTypeCode: eventTypeController.text.trim(),
                        placeText: placeController.text.trim(),
                        text: textController.text.trim(),
                      );
                  ref.invalidate(copyDetailProvider(copy.id));
                  if (context.mounted) {
                    Navigator.of(context).pop();
                  }
                },
                child: const Text('Сохранить событие'),
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _showBindSheet(
    BuildContext context,
    WidgetRef ref,
    CopyDetail copy,
  ) async {
    final tagUidController = TextEditingController(text: copy.activeTagUid ?? '');

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return Padding(
          padding: EdgeInsets.fromLTRB(
            16,
            16,
            16,
            16 + MediaQuery.of(context).viewInsets.bottom,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: tagUidController,
                decoration: const InputDecoration(labelText: 'UID NFC-метки'),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  await ref.read(catalogRepositoryProvider).bindTag(
                        copyId: copy.id,
                        tagUid: tagUidController.text.trim(),
                      );
                  ref.invalidate(copyDetailProvider(copy.id));
                  if (context.mounted) {
                    Navigator.of(context).pop();
                  }
                },
                child: const Text('Сохранить привязку'),
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _showStatusSheet(
    BuildContext context,
    WidgetRef ref,
    CopyDetail copy,
  ) async {
    String selectedStatusCode = copy.statusCode;
    final noteController = TextEditingController();

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return Padding(
          padding: EdgeInsets.fromLTRB(
            16,
            16,
            16,
            16 + MediaQuery.of(context).viewInsets.bottom,
          ),
          child: StatefulBuilder(
            builder: (context, setModalState) {
              return Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  DropdownButtonFormField<String>(
                    value: selectedStatusCode,
                    items: copy.availableStatuses
                        .map(
                          (status) => DropdownMenuItem<String>(
                            value: status.code,
                            child: Text(status.title),
                          ),
                        )
                        .toList(),
                    onChanged: (value) {
                      if (value == null) {
                        return;
                      }
                      setModalState(() => selectedStatusCode = value);
                    },
                    decoration: const InputDecoration(labelText: 'Статус экземпляра'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: noteController,
                    minLines: 2,
                    maxLines: 4,
                    decoration: const InputDecoration(
                      labelText: 'Комментарий',
                      helperText: 'Необязательно. Будет добавлен в историю.',
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () async {
                      await ref.read(catalogRepositoryProvider).updateCopyStatus(
                            copyId: copy.id,
                            statusCode: selectedStatusCode,
                            note: noteController.text.trim(),
                          );
                      ref.invalidate(copyDetailProvider(copy.id));
                      if (context.mounted) {
                        Navigator.of(context).pop();
                      }
                    },
                    child: const Text('Сохранить статус'),
                  ),
                ],
              );
            },
          ),
        );
      },
    );
  }
}
