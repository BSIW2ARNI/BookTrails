import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/widgets/async_value_view.dart';
import '../../../auth/application/auth_controller.dart';
import '../../application/profile_provider.dart';
import '../../domain/entities/profile_details.dart';

class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Профиль')),
      body: AsyncValueView<ProfileDetails>(
        value: profile,
        onRetry: () => ref.invalidate(profileProvider),
        data: (data) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(data.displayName, style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 8),
                      Text(data.email),
                      const SizedBox(height: 8),
                      Text(data.status.isEmpty ? 'Статус не задан.' : data.status),
                      const SizedBox(height: 8),
                      Text('Аватар: ${data.avatar.isEmpty ? '—' : data.avatar}'),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () => _showEditProfileSheet(context, ref, data),
                        child: const Text('Редактировать'),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Статистика', style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 12),
                      Text('Экземпляров: ${data.stats.trackedBooks}'),
                      Text('Отзывов: ${data.stats.reviews}'),
                      Text('Событий: ${data.stats.eventsLogged}'),
                      Text('Recommendation match: ${data.stats.recommendationMatch}'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Сессии', style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 12),
                      if (data.sessions.isEmpty) const Text('Активных сессий нет.'),
                      for (final session in data.sessions)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: Text(
                            '${session.device.isEmpty ? 'Неизвестное устройство' : session.device}'
                            ' • ${session.location.isEmpty ? '—' : session.location}'
                            ' • ${session.lastSeen}'
                            '${session.current ? ' • current' : ''}',
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.read(authControllerProvider.notifier).logout(),
                child: const Text('Выйти'),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _showEditProfileSheet(
    BuildContext context,
    WidgetRef ref,
    ProfileDetails data,
  ) async {
    final nameController = TextEditingController(text: data.displayName);
    final emailController = TextEditingController(text: data.email);
    final avatarController = TextEditingController(text: data.avatar);
    final statusController = TextEditingController(text: data.status);

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
              TextField(controller: nameController, decoration: const InputDecoration(labelText: 'Имя и фамилия')),
              const SizedBox(height: 12),
              TextField(controller: emailController, decoration: const InputDecoration(labelText: 'Email')),
              const SizedBox(height: 12),
              TextField(controller: avatarController, decoration: const InputDecoration(labelText: 'Аватар')),
              const SizedBox(height: 12),
              TextField(controller: statusController, decoration: const InputDecoration(labelText: 'Статус')),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  await ref.read(profileActionsProvider).updateProfile(
                        fullName: nameController.text.trim(),
                        email: emailController.text.trim(),
                        avatar: avatarController.text.trim(),
                        status: statusController.text.trim(),
                      );
                  if (context.mounted) {
                    Navigator.of(context).pop();
                  }
                },
                child: const Text('Сохранить'),
              ),
            ],
          ),
        );
      },
    );
  }
}
