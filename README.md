# BookTrail

BookTrail — система для bookcrossing и трекинга экземпляров книг с опорой на NFC-сценарии, пользовательские отзывы и контентные рекомендации. Проект включает Django web-приложение, mobile API и Flutter-клиент для Android.

## Ключевые возможности

- каталог книг с поиском, карточкой книги и связанными экземплярами;
- карточка экземпляра с текущим статусом, текущим держателем, NFC-привязкой и историей маршрута;
- регистрация, login/logout, профиль пользователя и список активных сессий;
- отзывы, уведомления и персональные рекомендации;
- NFC-привязка UID метки к экземпляру;
- scan flow, в котором сканирование метки автоматически переводит экземпляр текущему пользователю;
- ручная смена статуса экземпляра администратором через mobile API и Flutter UI;
- content-based recommendation engine на `scikit-learn`.

## Технологический стек

- Python 3.12
- Django `>=5.1,<5.2`
- SQLite
- Django Templates
- JavaScript (vanilla, без сборщика)
- Flutter (SDK `>=3.4.0 <4.0.0`)
- flutter_riverpod
- go_router
- Dio
- flutter_secure_storage
- equatable
- scikit-learn `>=1.5,<1.8`

## Архитектура проекта

Проект разделён на три контура:

- `web/` — доменная модель, web views, REST-like JSON API, admin, selectors, services, recommendation engine, тесты;
- `config/` — настройки Django, маршрутизация верхнего уровня, WSGI/ASGI;
- `booktrail_mobile/` — Flutter-клиент, который работает поверх `/api/v1/*`.

Сервисный слой Django разделён на:

- `selectors.py` — чтение и агрегация доменных данных;
- `services.py` — изменение состояния экземпляров, отзывов, уведомлений и scan flow;
- `api_views.py` — mobile API;
- `views.py` — серверный HTML-интерфейс;
- `recommendation_engine.py` — построение и сохранение рекомендаций.

## Структура каталогов

```text
BookTrail/
  manage.py
  requirements.txt
  package.json
  db.sqlite3
  config/
    settings/
      base.py
      dev.py
      prod.py
    urls.py
    asgi.py
    wsgi.py
  web/
    admin.py
    api_auth.py
    api_urls.py
    api_utils.py
    api_views.py
    apps.py
    forms.py
    models.py
    recommendation_engine.py
    selectors.py
    services.py
    tests.py
    urls.py
    utils.py
    views.py
    management/commands/
      seed_booktrail.py
      rebuild_recommendations.py
    migrations/
    static/
      web/
        css/
        js/
        img/
      vendor/
    templates/
      partials/
  sql_scripts/
  media/
  booktrail_mobile/
    lib/
      app/
      core/
      features/
      shared/
      main.dart
    android/
    ios/
    pubspec.yaml
```

## База данных

### Пользователи и доступ

- `auth_user` — стандартная таблица Django для аутентификации.
- `UserProfile` — прикладной профиль пользователя: `avatar`, `status`, `show_profile`, `share_reviews`, `nfc_visibility`.
- `Role` — доменный справочник ролей.
- `UserRole` — связь пользователя с доменной ролью.
- `AuthSession` — прикладная сессия mobile/API auth слоя: устройство, география, `refresh_token_hash`, `current`, `revoked`.

### Книги и экземпляры

- `Genre`, `Language`, `Author` — справочники жанров, языков и авторов.
- `Book` — карточка книги: название, жанр, язык, год, описание, обложка, акцент, ISBN.
- `BookAuthor` — связь многие-ко-многим между книгами и авторами с `sort_order`.
- `CopyStatus` — справочник статусов экземпляров.
- `Copy` — конкретный экземпляр книги. Хранит код экземпляра, текущий статус, инициатора создания и текущего держателя `holder`.

### NFC и маршрут

- `NfcTagStatus` — статусы NFC-меток.
- `NfcTag` — физическая NFC-метка с `uid`.
- `TagBind` — привязка метки к экземпляру. Поддерживает только одну активную привязку на метку и временные границы `started_at` / `ended_at`.
- `MoveEventType` — типы событий маршрута, включая `scan`, `transfer`, `waiting`, `prep`.
- `MoveSource` — источник события.
- `Move` — история событий экземпляра: тип, дата, место, текст, source, связанная NFC-метка и payload.

### Пользовательский контент и рекомендации

- `ReviewModerationStatus` — статусы модерации отзывов.
- `Review` — отзыв пользователя на книгу с оценкой и текстом.
- `Recommendation` — сохранённая рекомендация книги пользователю со score и explanation.
- `NotificationKind` — типы уведомлений.
- `Notification` — пользовательские уведомления.

### Что создаётся автоматически

- `seed_booktrail` создаёт справочники, пользователей, профили, роли, книги, экземпляры, NFC-метки, привязки, маршруты, отзывы, рекомендации, уведомления и прикладные сессии.
- web/mobile UI создаёт и меняет отзывы, scan-события, привязки, уведомления и профиль.
- `scan` через сервисный слой меняет текущего держателя экземпляра и его статус.
- `rebuild_recommendations` перестраивает содержимое таблицы `Recommendation`.

## Аутентификация и модель доступа

- Гость может открывать `/`, `/catalog/`, `/books/<id>/`, `/events/`.
- Аутентифицированный пользователь web-приложения получает доступ к `/recommendations/`, `/notifications/`, `/profile/`, `/scan/`.
- Mobile API использует bearer access token и refresh token через `AuthSession`.
- `/admin/` использует стандартную модель доступа Django и требует пользователя с `is_staff` / `is_superuser`.
- Доменные роли `member`, `moderator`, `admin` хранятся в `Role` / `UserRole`.
- Ручная смена статуса экземпляра через mobile API разрешена только администратору.

## Web-интерфейс

### Публичные страницы

- `/` — landing, шаблон `landing.html`, показывает краткое описание потока и последние события.
- `/catalog/` — шаблон `catalog.html`, поиск по названию, автору и ISBN, фильтрация по жанру и языку.
- `/books/<id>/` — шаблон `book_detail.html`, карточка книги, отзывы, экземпляры и похожие книги.
- `/copies/<id>/` — шаблон `copy_detail.html`, экземпляр книги, NFC-статус, история маршрута, bind/unbind метки и добавление событий.
- `/events/` — шаблон `events.html`, общая лента событий маршрута.

### Приватные страницы

- `/recommendations/` — шаблон `recommendations.html`, персональные рекомендации.
- `/notifications/` — шаблон `notifications.html`, mark-read и mark-all-read.
- `/profile/` — шаблон `profile.html`, редактирование прикладного профиля, приватности и просмотр активных сессий.
- `/scan/` — шаблон `scan_placeholder.html`, ручной web scan flow по `copy_code`, `tag_uid` или обоим полям.

### Аутентификация

- `/auth/login/`
- `/auth/register/`
- `/auth/logout/`

## Mobile API

API расположен под префиксом `/api/v1/`.

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET|PATCH /me`

### Книги и отзывы

- `GET /books`
- `GET /books/<id>`
- `POST /books/<id>/reviews`
- `PATCH /reviews/<id>`

### Экземпляры и NFC

- `GET|PATCH /copies/<id>`
- `POST /copies/<id>/moves`
- `POST /copies/<id>/bind-tag`
- `POST /copies/<id>/unbind-tag`
- `POST /scan`

### Лента, рекомендации и уведомления

- `GET /events`
- `GET /recommendations`
- `GET /notifications`
- `POST /notifications/mark-all-read`
- `POST /notifications/<id>/mark-read`

Ключевые особенности API:

- `POST /scan` находит экземпляр по активной NFC-привязке, назначает экземпляр текущему пользователю, переводит статус в `with_reader`, создаёт `Move` и возвращает `copy_id`.
- `GET /copies/<id>` возвращает текущее состояние экземпляра, holder, историю маршрута, права на смену статуса и список допустимых статусов.
- `PATCH /copies/<id>` предназначен для администратора и меняет статус экземпляра только по `status_code`.

## Мобильное приложение

Flutter-клиент расположен в `booktrail_mobile/`.

Основные подсистемы:

- `features/auth` — login, register, восстановление сессии, logout;
- `features/catalog` — каталог, книга, экземпляр, NFC-привязка и ручная смена статуса;
- `features/events` — лента событий;
- `features/recommendations` — персональная подборка;
- `features/notifications` — чтение уведомлений;
- `features/profile` — профиль и сессии;
- `features/scan` — NFC scan flow.

Mobile-клиент использует:

- `go_router` для навигации;
- `Riverpod` для состояния;
- `Dio` для API;
- `flutter_secure_storage` для токенов.

Текущий mobile flow экземпляра:

- scan screen вызывает платформенный NFC-слой;
- после чтения UID отправляется `POST /scan`;
- backend обновляет holder и статус экземпляра;
- mobile открывает `/copies/<id>`;
- карточка экземпляра показывает статус, текущего держателя, активную метку и маршрут;
- администратор видит отдельный action `Изменить статус` с выпадающим списком допустимых статусов.

## NFC-механизм

### Backend NFC-контур

- NFC-метка идентифицируется через `uid`.
- `TagBind` хранит активную связь между `NfcTag` и `Copy`.
- `bind-tag` привязывает UID к экземпляру.
- `unbind-tag` завершает активную привязку.
- `scan` ищет активный `TagBind` по `tag_uid`.
- После успешного scan:
  - экземпляр назначается текущему пользователю в поле `Copy.holder`;
  - статус экземпляра меняется на `with_reader`;
  - создаётся запись `Move` типа `scan`;
  - клиент получает `copy_id` и открывает карточку экземпляра.

### Mobile NFC-контур

- Flutter использует platform channel `booktrail/nfc`.
- Поддерживаются методы `isAvailable` и `scanTag`.
- Android-реализация находится в `booktrail_mobile/android/app/src/main/kotlin/com/example/booktrail_mobile/MainActivity.kt`.
- Native-слой использует `NfcAdapter.ReaderCallback`, reader mode и возвращает `uid` в hex-формате.
- При ошибках platform layer возвращает `PlatformException`, которая оборачивается в `NfcException`.

## Рекомендательная модель

Рекомендательная подсистема реализована в `web/recommendation_engine.py`.

Характеристики текущей реализации:

- тип модели: content-based recommendation engine;
- библиотека: `scikit-learn`;
- признаки строятся из названия книги, авторов, жанра, языка, описания и текстов отзывов;
- токенизация нормализует латиницу, кириллицу и цифры;
- используется `TfidfVectorizer` с `ngram_range=(1, 2)` и `max_features=5000`;
- схожесть считается через `cosine_similarity`;
- положительными для профиля пользователя считаются книги с review rating `>= 4`;
- профиль пользователя строится как взвешенная сумма TF-IDF-векторов позитивно оценённых книг;
- уже оценённые книги исключаются из выдачи;
- при отсутствии позитивных отзывов используется fallback по популярности, рейтингу и числу отзывов;
- результаты сохраняются в таблицу `Recommendation`.

Служебная команда:

```bash
python manage.py rebuild_recommendations
python manage.py rebuild_recommendations --username reader
```

## Сквозные бизнес-процессы

### Книга и экземпляр

- `Book` хранит метаданные книги.
- `Copy` хранит текущее состояние конкретного физического экземпляра.
- История маршрута живёт в `Move` и не заменяет текущее состояние `Copy`.

### Отзывы

- Пользователь может создать, обновить и удалить свой отзыв на карточке книги.
- Отзывы используются и в UI, и как сигнал для рекомендательной модели.

### Уведомления

- Пользователь может отмечать отдельные уведомления и все уведомления целиком как прочитанные.

### Scan flow

- Web-версия поддерживает ручное сканирование через форму.
- Mobile scan использует NFC UID и автоматически переводит книгу текущему пользователю.
- Scan — это не только запись в историю, но и изменение текущего состояния экземпляра.

### Ручная смена статуса

- Администратор может вручную изменить статус экземпляра.
- Статус выбирается из допустимого набора, а не вводится как произвольный текст.
- При ручной смене статуса создаётся запись в истории маршрута.

## Развёртывание проекта на другом ПК

Раздел описывает полный цикл первичного развёртывания BookTrail на чистой машине: backend (Django + SQLite) и mobile-клиент (Flutter, Android). Команды приведены для PowerShell (Windows), но эквиваленты для macOS/Linux отличаются только активацией venv (`source .venv/bin/activate`).

### 1. Предварительные требования

Установить на целевой ПК:

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| Python | 3.12.x | Backend (Django, scikit-learn) |
| pip | актуальная | Установка Python-зависимостей |
| Git | актуальная | Клонирование репозитория |
| Flutter SDK | `>=3.4.0 <4.0.0` | Сборка mobile-клиента |
| Android Studio | актуальная | Android SDK, emulator, build-tools |
| Java JDK | 17 (для Android Gradle) | Сборка Android |
| ADB | актуальная (входит в Android SDK platform-tools) | Запуск на физическом устройстве |

Проверка установок:

```powershell
python --version
pip --version
git --version
flutter --version
flutter doctor
adb version
```

`flutter doctor` должен показать зелёные галочки для `Flutter`, `Android toolchain`, и (опционально) `Android Studio`. Если есть проблемы — устранить их до продолжения.

### 2. Получение исходного кода

```powershell
git clone https://github.com/BSIW2ARNI/BookTrails.git
cd BookTrails
```

### 3. Backend: Django + SQLite

#### 3.1 Создание виртуального окружения

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Если PowerShell блокирует выполнение скрипта активации, один раз выполнить:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

#### 3.2 Установка зависимостей

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

В `requirements.txt` объявлены:

- `Django>=5.1,<5.2`
- `scikit-learn>=1.5,<1.8`

#### 3.3 Переменные окружения (опционально)

По умолчанию проект работает на dev-настройках (`config/settings/__init__.py` → `dev.py`) с SQLite-базой `db.sqlite3` в корне репозитория. Этих настроек достаточно для запуска на новом ПК. Можно переопределить через переменные среды:

| Переменная | Значение по умолчанию | Назначение |
|------------|----------------------|------------|
| `DJANGO_SECRET_KEY` | dev-ключ | Secret key. На prod обязательно переопределить. |
| `DJANGO_DEBUG` | `True` в dev | Включает debug-режим. |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost,testserver,10.0.2.2` | Список через запятую. |
| `DJANGO_TIME_ZONE` | `UTC` | Таймзона. |
| `DJANGO_LOG_LEVEL` | `INFO` | Уровень логирования. |
| `DB_ENGINE` | `django.db.backends.sqlite3` | Можно переключить на PostgreSQL/MySQL. |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | — | Для не-SQLite БД. |

Пример установки в PowerShell:

```powershell
$env:DJANGO_DEBUG = "True"
$env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost,10.0.2.2"
```

#### 3.4 Применение миграций

```powershell
python manage.py migrate
```

В результате создаётся файл `db.sqlite3` со всей доменной схемой (книги, экземпляры, NFC-метки, маршруты, отзывы, рекомендации, уведомления, сессии).

#### 3.5 Загрузка тестовых данных

```powershell
python manage.py seed_booktrail
```

Команда заполняет базу справочниками, тремя учётными записями (`reader`, `moderator`, `admin` с паролем `StrongPass123`), книгами, экземплярами, NFC-привязками, отзывами, рекомендациями и уведомлениями. `admin` создаётся как `is_staff=True` и `is_superuser=True`, поэтому отдельный `createsuperuser` не нужен.

Если требуется свой superuser:

```powershell
python manage.py createsuperuser
```

#### 3.6 Сборка рекомендаций (опционально)

```powershell
python manage.py rebuild_recommendations
```

`seed_booktrail` уже создаёт первичные рекомендации, но команду можно повторно вызывать после изменения отзывов или книг.

#### 3.7 Запуск сервера разработки

```powershell
python manage.py runserver 0.0.0.0:8000
```

Привязка к `0.0.0.0` нужна, если планируется обращаться с физического Android-устройства в той же локальной сети. Для запуска только локально достаточно `python manage.py runserver`.

Проверка работоспособности:

- `http://127.0.0.1:8000/` — landing
- `http://127.0.0.1:8000/catalog/` — каталог
- `http://127.0.0.1:8000/auth/login/` — login
- `http://127.0.0.1:8000/admin/` — Django Admin
- `http://127.0.0.1:8000/api/v1/books` — mobile API

### 4. Mobile-клиент Flutter

#### 4.1 Установка зависимостей

```powershell
cd booktrail_mobile
flutter pub get
```

#### 4.2 Подготовка Android-устройства

Вариант А — Android Emulator (через Android Studio → Device Manager):

1. Создать AVD (Pixel 5, API 33+).
2. Запустить эмулятор.
3. Убедиться, что `flutter devices` его видит.

Эмулятор обращается к хост-машине по адресу `10.0.2.2` — это специальный alias для `127.0.0.1` на хосте.

Вариант Б — физическое Android-устройство по USB:

1. Включить «Параметры разработчика» и «Отладка по USB».
2. Подключить кабелем, разрешить отладку.
3. Проверить: `adb devices` показывает устройство.
4. Пробросить порт хоста на устройство: `adb reverse tcp:8000 tcp:8000`.

#### 4.3 Запуск приложения

Эмулятор:

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

Физическое устройство (с `adb reverse`):

```powershell
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Физическое устройство без `adb reverse` (одна Wi-Fi сеть с ПК):

```powershell
flutter run --dart-define=API_BASE_URL=http://<IP-вашего-ПК>:8000/api/v1
```

В этом сценарии Django нужно запустить как `python manage.py runserver 0.0.0.0:8000`, и `DJANGO_ALLOWED_HOSTS` должен содержать IP машины.

#### 4.4 Production-сборка APK (опционально)

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://<your-prod-host>/api/v1
```

APK появится в `booktrail_mobile/build/app/outputs/flutter-apk/app-release.apk`.

### 5. Smoke-test после развёртывания

1. Открыть `http://127.0.0.1:8000/` — landing загружается.
2. Войти на web под `reader / StrongPass123`.
3. Перейти в `/catalog/`, открыть любую книгу, затем экземпляр.
4. Открыть `/recommendations/` — должны быть подобраны книги.
5. В mobile-клиенте: войти под `reader`, открыть catalog, открыть экземпляр.
6. На карточке экземпляра выполнить bind-tag/unbind-tag.
7. На экране Scan приложить NFC-метку (или ввести UID в web-форму `/scan/`).
8. Под `admin` проверить ручную смену статуса экземпляра в mobile UI.

### 6. Запуск тестов

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test web
```

### 7. Production-развёртывание (краткая памятка)

Полноценная prod-конфигурация выходит за рамки шаблона, но при переходе на боевой контур обязательно:

- задать `DJANGO_SECRET_KEY` через переменную среды;
- `DJANGO_DEBUG=False`;
- `DJANGO_ALLOWED_HOSTS` со списком реальных доменов;
- перевести БД на PostgreSQL через `DB_ENGINE=django.db.backends.postgresql` и заполнить `DB_*` переменные;
- использовать `config.settings.prod` (через `DJANGO_SETTINGS_MODULE=config.settings.prod`);
- собрать статические файлы: `python manage.py collectstatic --noinput`;
- запускать через `gunicorn config.wsgi:application` или `uvicorn config.asgi:application` за reverse-proxy (nginx);
- включить HTTPS и соответствующие `DJANGO_CSRF_COOKIE_SECURE`, `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SECURE_HSTS_SECONDS`.

### 8. Решение типовых проблем

| Симптом | Причина | Решение |
|---------|---------|---------|
| `Activate.ps1 cannot be loaded ... execution of scripts is disabled` | PowerShell ExecutionPolicy. | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`. |
| `ModuleNotFoundError: No module named 'django'` | Venv не активирован. | `.venv\Scripts\Activate.ps1` и повторить установку. |
| Mobile получает `Connection refused` к API | Android-эмулятор не видит `127.0.0.1` хоста. | Использовать `10.0.2.2` (эмулятор) или `adb reverse` (USB). |
| Mobile получает `DisallowedHost` | IP машины не в `ALLOWED_HOSTS`. | Добавить IP в `DJANGO_ALLOWED_HOSTS`. |
| `flutter doctor` ругается на Android licenses | Не приняты лицензии SDK. | `flutter doctor --android-licenses`. |
| `seed_booktrail` падает на повторном запуске | Дубли пользователей/тегов. | Удалить `db.sqlite3` и снова выполнить `migrate` + `seed_booktrail`. |
| Не строятся рекомендации | Нет отзывов с rating >= 4. | Войти под `reader` и поставить отзывы, затем `rebuild_recommendations`. |

## Тестовые данные

Команда:

```powershell
python manage.py seed_booktrail
```

Создаёт:

- справочники статусов, типов событий, ролей и уведомлений;
- пользователей `reader`, `moderator`, `admin`;
- профили и ролевые назначения;
- книги, авторов, жанры, языки и экземпляры;
- NFC-метки и активные привязки;
- историю перемещений;
- отзывы;
- рекомендации;
- уведомления;
- прикладные auth-сессии.

## Тестовые учётные записи

- `reader / StrongPass123`
- `moderator / StrongPass123`
- `admin / StrongPass123`

`admin` также создаётся с `is_staff=True` и `is_superuser=True`.

## Проверка работоспособности

- web: `http://127.0.0.1:8000/`
- каталог: `http://127.0.0.1:8000/catalog/`
- login: `http://127.0.0.1:8000/auth/login/`
- профиль: `http://127.0.0.1:8000/profile/`
- scan: `http://127.0.0.1:8000/scan/`
- admin: `http://127.0.0.1:8000/admin/`

Минимальная ручная проверка:

1. Войти под `reader`.
2. Открыть книгу и экземпляр.
3. Привязать UID метки к экземпляру.
4. Выполнить scan из mobile-клиента.
5. Убедиться, что экземпляр открылся и статус стал `with_reader`.
6. Под `admin` проверить ручную смену статуса через mobile UI.

## Тестирование

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test web
```

Тесты покрывают:

- auth flow;
- profile update;
- review CRUD;
- catalog search;
- notifications;
- copy moves;
- NFC bind/unbind;
- scan flow;
- mobile API;
- model-level validation.

## Ограничения текущей реализации

- Локальная база по умолчанию — SQLite.
- Web и mobile используют разные интерфейсные сценарии поверх одного backend.
- Рекомендательная модель content-based и зависит от наличия пользовательских отзывов и описаний книг.
- Flutter-клиент ориентирован на Android NFC reader mode через platform channel.
- Системный back-office как отдельный модуль отсутствует; административные операции сосредоточены в Django Admin и прикладном mobile/API-сценарии смены статуса экземпляра.
