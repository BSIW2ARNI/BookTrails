import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppScaffoldShell extends StatelessWidget {
  const AppScaffoldShell({
    required this.currentLocation,
    required this.child,
    super.key,
  });

  final String currentLocation;
  final Widget child;

  static const _destinations = <({String label, String path, IconData icon})>[
    (label: 'Каталог', path: '/catalog', icon: Icons.auto_stories_outlined),
    (label: 'События', path: '/events', icon: Icons.timeline_outlined),
    (label: 'Скан', path: '/scan', icon: Icons.nfc_outlined),
    (label: 'Для вас', path: '/recommendations', icon: Icons.auto_awesome_outlined),
    (label: 'Уведомления', path: '/notifications', icon: Icons.notifications_none),
    (label: 'Профиль', path: '/profile', icon: Icons.person_outline),
  ];

  int _resolveIndex() {
    final index = _destinations.indexWhere((item) => currentLocation.startsWith(item.path));
    return index < 0 ? 0 : index;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _resolveIndex(),
        onDestinationSelected: (index) => context.go(_destinations[index].path),
        destinations: [
          for (final item in _destinations)
            NavigationDestination(
              icon: Icon(item.icon),
              label: item.label,
            ),
        ],
      ),
    );
  }
}
