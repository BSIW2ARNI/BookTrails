# Android NFC channel setup for BookTrail Mobile

Этот документ нужен после установки `Flutter SDK` и генерации Android-проекта.

## Что уже готово в Dart-слое

В проекте уже есть platform channel:
- channel name: `booktrail/nfc`
- method `isAvailable`
- method `scanTag`

Файлы:
- [lib/core/nfc/nfc_service.dart](/abs/path/C:/Users/Asus/PycharmProjects/BookTrail/booktrail_mobile/lib/core/nfc/nfc_service.dart)
- [lib/core/nfc/nfc_providers.dart](/abs/path/C:/Users/Asus/PycharmProjects/BookTrail/booktrail_mobile/lib/core/nfc/nfc_providers.dart)
- [lib/features/scan/presentation/pages/scan_page.dart](/abs/path/C:/Users/Asus/PycharmProjects/BookTrail/booktrail_mobile/lib/features/scan/presentation/pages/scan_page.dart)

## Что нужно сделать после `flutter create .`

1. В корне `booktrail_mobile` выполнить:

```powershell
flutter create .
```

Это создаст:
- `android/`
- `ios/`
- платформенные entrypoint'ы проекта

2. В `android/app/src/main/AndroidManifest.xml` добавить NFC permission:

```xml
<uses-permission android:name="android.permission.NFC" />
<uses-feature android:name="android.hardware.nfc" android:required="false" />
```

3. В `MainActivity.kt` подключить `MethodChannel("booktrail/nfc")`

Нужно обработать методы:
- `isAvailable`
- `scanTag`

Ожидаемый формат ответа для `scanTag`:

```json
{
  "uid": "04A1B2C3D4"
}
```

4. Логика Android-слоя должна:
- проверить наличие `NfcAdapter`
- открыть режим ожидания считывания тега
- получить `Tag.id`
- перевести байты UID в верхний hex-формат
- вернуть `uid` назад в Flutter

## Минимальный контракт для Android handler

`isAvailable`:
- возвращает `true`, если NFC доступен на устройстве и включён
- возвращает `false`, если NFC недоступен или отключён

`scanTag`:
- возвращает `uid`, если метка считана успешно
- выбрасывает platform error, если:
  - NFC отключён
  - устройство не поддерживает NFC
  - считывание отменено
  - tag не прочитан

## Почему сейчас нет Android-кода в репозитории

Потому что в текущем mobile workspace пока нет сгенерированного `android/` проекта.
Без `flutter create .` правильнее не выдумывать вручную неполную Android-структуру.

Сейчас Dart-слой уже готов, и после генерации Android-папок останется добавить только native handler.
