import 'package:dio/dio.dart';

import '../env/app_env.dart';
import '../storage/token_storage.dart';
import 'auth_interceptor.dart';

class ApiClient {
  ApiClient({required TokenStorage tokenStorage})
      : dio = Dio(
          BaseOptions(
            baseUrl: AppEnv.apiBaseUrl,
            connectTimeout: const Duration(seconds: 15),
            receiveTimeout: const Duration(seconds: 20),
            headers: const {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
          ),
        )..interceptors.add(AuthInterceptor(tokenStorage: tokenStorage));

  final Dio dio;
}

