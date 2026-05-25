import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/widgets/app_scaffold_shell.dart';
import '../../features/auth/application/auth_controller.dart';
import '../../features/auth/domain/entities/auth_session_state.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/auth/presentation/pages/register_page.dart';
import '../../features/catalog/presentation/pages/book_detail_page.dart';
import '../../features/catalog/presentation/pages/catalog_page.dart';
import '../../features/catalog/presentation/pages/copy_detail_page.dart';
import '../../features/events/presentation/pages/events_page.dart';
import '../../features/notifications/presentation/pages/notifications_page.dart';
import '../../features/profile/presentation/pages/profile_page.dart';
import '../../features/recommendations/presentation/pages/recommendations_page.dart';
import '../../features/scan/presentation/pages/scan_page.dart';

final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>();

final appRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authControllerProvider);

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/splash',
    routes: <RouteBase>[
      GoRoute(
        path: '/splash',
        name: 'splash',
        builder: (context, state) => const _SplashPage(),
      ),
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: '/register',
        name: 'register',
        builder: (context, state) => const RegisterPage(),
      ),
      ShellRoute(
        builder: (context, state, child) {
          return AppScaffoldShell(currentLocation: state.uri.path, child: child);
        },
        routes: <RouteBase>[
          GoRoute(
            path: '/catalog',
            name: 'catalog',
            builder: (context, state) => const CatalogPage(),
          ),
          GoRoute(
            path: '/events',
            name: 'events',
            builder: (context, state) => const EventsPage(),
          ),
          GoRoute(
            path: '/scan',
            name: 'scan',
            builder: (context, state) => const ScanPage(),
          ),
          GoRoute(
            path: '/recommendations',
            name: 'recommendations',
            builder: (context, state) => const RecommendationsPage(),
          ),
          GoRoute(
            path: '/notifications',
            name: 'notifications',
            builder: (context, state) => const NotificationsPage(),
          ),
          GoRoute(
            path: '/profile',
            name: 'profile',
            builder: (context, state) => const ProfilePage(),
          ),
          GoRoute(
            path: '/books/:id',
            name: 'book_detail',
            builder: (context, state) => BookDetailPage(
              bookId: int.parse(state.pathParameters['id']!),
            ),
          ),
          GoRoute(
            path: '/copies/:id',
            name: 'copy_detail',
            builder: (context, state) => CopyDetailPage(
              copyId: int.parse(state.pathParameters['id']!),
            ),
          ),
        ],
      ),
    ],
    redirect: (context, state) {
      final location = state.uri.path;
      final isAuthRoute = location == '/login' || location == '/register';
      final isSplash = location == '/splash';
      final resolved = authState.valueOrNull;
      final isLoading = authState.isLoading || resolved == null || resolved.status == AuthStatus.unknown;

      if (isLoading) {
        return isSplash ? null : '/splash';
      }

      if (resolved.isAuthenticated) {
        if (isAuthRoute || isSplash) {
          return '/catalog';
        }
        return null;
      }

      if (!isAuthRoute) {
        return '/login';
      }
      return null;
    },
  );
});

class _SplashPage extends StatelessWidget {
  const _SplashPage();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: CircularProgressIndicator(),
      ),
    );
  }
}
