# Мобильная платформа NumerOM: решение от 15.10.2026

## Рекомендация

Создать отдельное приложение **Expo / React Native / TypeScript** для iOS и Android, подключённое к действующему FastAPI API и той же MongoDB. Общими сделать API-клиент, типы, проверки пользовательского ввода и дизайн-токены; мобильные экраны реализовать нативными компонентами. Веб-интерфейс сохранить отдельным приложением. Это архитектурная рекомендация по изученному коду, а не результат измерения производительности.

| Критерий NumerOM | Expo / React Native | Capacitor |
| --- | --- | --- |
| Повторное использование текущего UI | Перенос экранов; DOM, Radix, Chart.js и CSS напрямую не переносятся | Можно упаковать существующую веб-сборку и сохранить большинство DOM-компонентов |
| Мобильные сценарии | Отдельная нативная навигация, ввод, безопасное хранение, управление медиа | WebView-интерфейс и доступ к устройству через плагины |
| Объём первого этапа | Выше: нужны мобильные экраны | Ниже: нужна адаптация сайта и интеграция контейнера |
| Соответствие цели | Предпочтительно для самостоятельного приложения с длительным развитием | Предпочтительно, если цель — быстро распространять существующий сайт через мобильный контейнер |

Expo официально является React Native framework. Capacitor официально предлагает контейнер для веб-приложений и native Plugin API. Оценка объёма адаптации выше — вывод из `frontend/package.json`, `frontend/src/components/VideoViewer.jsx` и `AuthContext.jsx`, где используются DOM, браузерное хранилище и веб-библиотеки. [Expo](https://docs.expo.dev/get-started/create-a-project/), [Capacitor](https://capacitorjs.com/docs), [установка Capacitor в существующий проект](https://capacitorjs.com/docs/getting-started).

## Совместимые версии

На дату исследования официальная таблица документации содержит **Expo SDK 57 / React Native 0.86 / React 19.2.3**. SDK 58 опубликован в changelog как beta; для первой реализации выбираем stable 57, актуальный patch и lockfile. Требования SDK 57: Node от 22.13.x, Android от 7, target/compile SDK 36, iOS от 16.4, Xcode от 26.4. [Таблица Expo](https://docs.expo.dev/versions/v57.0.0/), [SDK 58 beta](https://expo.dev/changelog/sdk-58-beta).

Не фиксировать первоначальный `57.0.0`: SDK 57 получил исправления Hermes и запуска в `57.0.17`, использующем RN 0.86.3. При Xcode 27 необходимо отдельно проверить настройку scene lifecycle; текущий Mac использует Xcode 26.6. [Release notes SDK 57](https://expo.dev/changelog/sdk-57).

Версионные страницы рекомендуют `expo-router ~57.0.28` и `expo-secure-store ~57.0.4`; совместимые версии остальных модулей выбирает `expo install`. Это снимок документации, не результат установки из npm. [Router](https://docs.expo.dev/versions/v57.0.0/sdk/router/), [SecureStore](https://docs.expo.dev/versions/latest/sdk/securestore/).

## Структура и контракты

Предлагаемая граница: `mobile/src/app` — маршруты Expo Router; `mobile/src/features` — авторизация, расчёты, обучение, профиль; `mobile/src/components` — мобильный UI; `packages/api-client` — независимый от React HTTP-клиент и типы. В монорепозитории нельзя случайно подтянуть второй React или несовместимые native-модули: зависимости каждого приложения должны оставаться согласованными. [Expo monorepos](https://docs.expo.dev/guides/monorepos/).

Включить TypeScript `strict`, наследовать `expo/tsconfig.base`. Expo Router даёт файловую навигацию; генерируемые typed routes пока документированы как beta, поэтому не делать их обязательным условием первой поставки. [TypeScript](https://docs.expo.dev/guides/typescript/), [typed routes](https://docs.expo.dev/router/reference/typed-routes/).

В активном `backend/server.py` существуют `POST /api/auth/login` и `POST /api/auth/register`, возвращающие `access_token` и `user`. Текущий web восстанавливает профиль через `GET /api/user/profile-v2` (`frontend/src/components/AuthContext.jsx`). Мобильное приложение должно использовать те же аккаунты и Bearer API; `backend_clean` нельзя считать активным контрактом без отдельной проверки запуска. Ответы API необходимо проверить на реальном сервере: наличие обработчика в коде не подтверждает работоспособность endpoint.

Для native хранить токен через `expo-secure-store`, удалять его при выходе и подтверждённом 401; сетевой сбой не должен стирать действующую сессию. SecureStore использует iOS Keychain и Android Keystore; это хранилище малых секретов, а не базы профилей/уроков. Web-preview потребует отдельного адаптера: SecureStore не заявляет поддержку Web. Биометрия в Expo Go имеет ограничения; на первом этапе её не включать. [SecureStore](https://docs.expo.dev/versions/latest/sdk/securestore/).

Профиль, доступ к курсам, кредиты и сохранённые расчёты остаются серверными. В `backend/auth.py` срок access token задан как 24 часа; механизм refresh token в исследованных auth-путях не установлен. Нужен понятный повторный вход при истечении. В `backend/server.py` и `backend/auth.py` также найдены логи фрагментов пароля, хеша и токена: убрать их при рефакторинге авторизации.

## Графики, PNG и уроки

- Авторские PNG можно использовать как локальные assets React Native. Для линий, кругов и диаграмм — `react-native-svg`; доступная в Expo библиотека поддерживает iOS/Android/Web. Web Chart.js-компоненты переписываются на представление общих числовых данных. [SVG](https://docs.expo.dev/versions/v57.0.0/sdk/svg/).
- Для прямых видеопотоков/файлов — `expo-video` (`useVideoPlayer`, `VideoView`), для аудио — `expo-audio`. Web iframe YouTube/Vimeo/Bunny нельзя выдавать за прямой видеопоток: сначала установить фактические типы URL в уроках, затем выбрать разрешённый embed или прямой playback. DRM, background playback и права на скачивание требуют отдельной проверки конкретного контента. [Видео](https://docs.expo.dev/versions/v57.0.0/sdk/video/), [аудио](https://docs.expo.dev/versions/v57.0.0/sdk/audio/).
- PDF/Word и push — отдельные интеграции после рабочего входа, расчётов и списка уроков; существующий browser VAPID flow не является native push интеграцией. Не считать открытие web-preview проверкой нативных медиа или уведомлений.

## Команды реализации

Команды ниже предложены для нового каталога `mobile`; в исследовании они **не выполнялись**. При уже созданном приложении scaffold повторно не запускать. После генерации проверить выбранные версии и сохранить один lockfile.

```bash
npx create-expo-app@latest mobile
cd mobile
npx expo install 'expo@^57.0.17' --fix
npx expo install expo-secure-store expo-dev-client react-native-svg expo-video expo-audio
npx expo-doctor@latest
npx tsc --noEmit
npx expo export --platform ios
npx expo export --platform android
npx expo run:ios
```

Создание default template, подбор совместимых зависимостей и команды native build описаны Expo. Если default template уже переехал на более новый стабильный SDK, сначала пересмотреть матрицу совместимости, не делать слепой downgrade. `expo export` проверяет JS/assets bundle, **не собирает IPA/APK**. Native build нужен отдельно. [Создание проекта](https://docs.expo.dev/get-started/create-a-project/), [обновление SDK 57](https://expo.dev/changelog/sdk-57), [локальная сборка](https://docs.expo.dev/guides/local-app-development/).

Основной режим — development build с `expo-dev-client`. Expo Go годится для быстрого просмотра поддерживаемых модулей, но наличие нужного SDK в магазине нельзя предполагать: release notes SDK 57 отмечают задержку публикации. Локальная сборка через Expo CLI не требует Expo-аккаунта; облачная EAS-сборка — отдельный путь. [Development builds](https://docs.expo.dev/develop/development-builds/introduction/), [статус Expo Go](https://expo.dev/changelog/sdk-57).

Для подключения физического телефона API должен иметь доступный ему адрес: `127.0.0.1` телефона не указывает на Mac. Публичный production endpoint должен быть HTTPS; адрес и сетевую доступность следует проверить отдельно.

## Проверено и остаётся проверить

Проверено read-only на данном Mac: `node --version` → **v22.22.2**, `xcodebuild -version` → **Xcode 26.6 / 17F113**. `/usr/libexec/java_home -V` не нашёл Java Runtime. Android SDK, эмуляторы, CocoaPods, доступные iOS runtimes и signing identities не проверялись. Для Android local build сначала нужен рабочий Android toolchain; отсутствие Java не блокирует TypeScript-разработку и проверку bundle. [Требования сборки](https://docs.expo.dev/guides/local-app-development/).

Не проверено: установка npm-зависимостей, Expo Doctor, типизация приложения, bundle/export, сборка native binaries, симуляторы/телефоны, реальные аккаунты/API, видеопотоки, подпись и публикация. Исследование изменяет только этот документ; оно не означает готовность мобильного приложения.
