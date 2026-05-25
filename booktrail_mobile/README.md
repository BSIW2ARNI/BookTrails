# BookTrail Mobile

Каркас мобильного клиента `BookTrail` на `Flutter`.

Что уже подготовлено:
- базовая структура `presentation / application / domain / data`
- `go_router` для навигации
- `Riverpod` как точка входа для state management
- `dio` + interceptor-каркас для API
- `flutter_secure_storage` для токенов
- app shell с основными разделами
- auth-слой с восстановлением сессии, route guard'ами и logout
- read-only экраны каталога, книги, экземпляра, событий, рекомендаций, уведомлений и профиля
- write-flow для профиля, отзыва, уведомлений, move, bind/unbind и manual scan
- NFC app-layer через platform channel с fallback на ручной UID

Что ещё не сделано:
- полировка UX, валидации и ошибок на mobile экранах
- более чистое разделение mobile-кода на feature-level use cases и actions
- Android native handler для `booktrail/nfc` после `flutter create .`

## Структура

```text
booktrail_mobile/
  lib/
    app/
      router/
      theme/
    core/
      env/
      errors/
      network/
      storage/
      widgets/
    features/
      auth/
      catalog/
      events/
      notifications/
      profile/
    shared/
      presentation/widgets/
```

## Запуск

После установки `Flutter SDK`:

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

Для локальной разработки с Android Emulator:
- backend обычно доступен как `http://10.0.2.2:8000`

Для физического устройства:
- использовать IP машины в локальной сети

## Следующий шаг

Следующий этап для mobile skeleton:
- реализовать `/auth/*` и `/me` на backend
- заменить временные auth-формы на полностью рабочий flow с реальными ответами сервера
- заменить placeholder-экраны на реальные feature flows


Remove-Item -Force "C:\Users\Asus\.gradle\wrapper\dists\gradle-8.14-all\c2qonpi39x1mddn7hk5gh9iqj\gradle-8.14-all.zip"

Remove-Item -Force "C:\Users\Asus\.gradle\wrapper\dists\gradle-8.14-all\c2qonpi39x1mddn7hk5gh9iqj\gradle-8.14-all.zip.lck"

Get-Item "C:\Users\Asus\.gradle\wrapper\dists\gr flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/
api/v1adle-8.14-all\c2qonpi39x1mddn7hk5gh9iqj\gradle-8.14-all.zip" | Select-Object Name, Length