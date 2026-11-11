# NumerOM Foundation and Mobile Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task. Checkboxes record verified outcomes, not intentions.

**Goal:** Начать полный рефакторинг через проверенный модуль аккаунтов, общий API и работающее исходное приложение iPhone/Android.
**Architecture:** Постепенное выделение модулей из действующего сервера; независимый API-пакет; отдельный Expo клиент, существующий сайт сохраняется.
**Tech Stack:** FastAPI, MongoDB/Motor, React 19/CRA, Expo/React Native, TypeScript, Node test runner, unittest.
**Spec:** docs/superpowers/specs/2026-10-15-numerom-platform.md

**Дополнение 16.10.2026:** пользователь впоследствии явно поручил публичную ссылку как у Helper и продолжение работ. Публикация пилота и обновление процессов NumerOM выполнены в этом расширенном объёме; исходный запрет публикации ниже относится только к первому этапу. [Текущее состояние и доказательства](../../refactoring/public-release.md).

## Global Constraints

Сохранять текущий diff и PNG. Никаких production изменений, публикации, списаний реальных баллов и автоматических повторов POST. Не делать коммиты в смешанном пользовательском checkout. Не использовать backend_clean как действующий сервер. Только первый этап ниже является исполняемым планом этой итерации; остальные этапы полного рефакторинга описаны в spec.

## Review Focus

1. Явный URL сервера имеет приоритет; /api не дублируется; URL телефона не берётся из localhost сайта. Проверки: API resolver tests + реальный bundle.
2. Сеть не стирает сессию; 401 удаляет токен; поздний ответ после выхода не возвращает пользователя. Проверки: session tests + review concurrency.
3. PATCH профиля не изменяет роль/баллы и не раскрывает password_hash. Проверки: backend HTTP contract tests + response projection review.
4. Расчёт не списывает повторно из-за double tap или retry; цена и формат даты видимы. Проверки: client tests + UI review; реальное списание не выполняется.
5. Учебные материалы не выдают mock за результат и не передают токен внешним URL. Проверки: error/empty UI inspection + link handling review. Native playback/платежи не объявляются готовыми.

### Task 1: Shared API and session boundary

**Files:** packages/api-client/{package.json,index.js,index.d.ts,test/*.test.js}; frontend/src/utils/backendUrl.js; frontend/src/services/api.js; frontend/craco.config.js; frontend/src/components/AuthContext.jsx.
**Consumes:** Existing /api/auth/login, /auth/register, /user/profile-v2 and /learning-v2/lessons contracts.
**Produces:** resolveBackendUrl; createApiClient; ApiError; createSessionController with injected storage and observable state.

- [x] Write failing behavior tests: configured URL preservation, local and production defaults, auth headers, validation errors, no mutation retry, cancellation and timeout, session restoration/401/network/logout race.
- [x] Run `node --test packages/api-client/test/*.test.js`. Expected: failing before implementation, green afterwards.
- [x] Implement CJS package + TS declarations and adapters; reuse resolver/profile client from web without replacing all legacy axios calls at once.
- [x] Run web tests from frontend. Expected: existing six navigation tests + new URL adapter tests pass.

### Task 2: Account module in the active backend

**Files:** backend/domain/name_numbers.py; backend/services/accounts.py; backend/routers/accounts.py; backend/server.py; backend/auth.py; backend/tests/test_accounts.py.
**Consumes:** Existing users collection; auth password/token functions; User/LoginRequest/TokenResponse models.
**Produces:** create_accounts_router(db), compatible login and profile-v2 endpoints, explicit profile projection and field allowlist.

- [x] Write HTTP-level tests with isolated in-memory repository: good/bad login; expired subscription; missing/current profile; allowlisted update; invalid date; secret exclusion; no secret logs.
- [x] Run `backend/.venv/bin/python -m unittest discover -s backend/tests`. Expected: red before module, green after.
- [x] Move route bodies to router/service with injected db; reuse name calculation; mount once in server; remove sensitive auth diagnostics.
- [x] Compile changed backend files and test app through HTTP without live Mongo. Expected: all tests pass. Production process is not restarted.

### Task 3: Native mobile application

**Files:** mobile/package.json, package-lock.json, app.config.ts, tsconfig.json; mobile/src/app/**; mobile/src/components/**; mobile/src/features/**; mobile/src/lib/**; mobile/assets/**.
**Consumes:** Shared API/session package and existing light PNGs; stable SDK chosen from registry and official research.
**Produces:** Login/register, tabs (overview, calculations, learning, library, profile), safe storage, responsive native screens and deployment configuration.

- [x] Install compatible stable Expo modules and local shared package. Expected: dependency resolution success, no blind old-version downgrade.
- [x] Build screens around the tested session controller and request hooks; use explicit errors, safe form input, refresh, accessibility labels, no fake production data.
- [x] Run TypeScript and Expo dependency checks. Expected: no type/compatibility errors.
- [x] Export iOS and Android bundles. Expected: Metro resolves all routes/assets and succeeds on both platforms. This is not an IPA/APK or a device test.

### Task 4: Integration, review and handoff

**Files:** docs/refactoring/2026-10-15-status.md, mobile/README.md, scripts/check-platform.sh; fixes in changed files only.
**Consumes:** Tasks 1–3 outputs.
**Produces:** Repeatable validation command, runnable source/config, complete evidence and explicit remaining roadmap.

- [x] Run combined unit/HTTP/type checks and production web build. Expected: all implemented-stage checks pass.
- [x] Preview mobile web rendering and inspect errors/empty states using CUA. Attempt native toolchain checks; document missing runtime/signing rather than claim device verification.
- [x] Fresh reviewer assesses implementation, focused on five risks above. Fix important defects with targeted tests.
- [x] Record completed checks, run instructions and remaining full-refactor stages. No commit/push/publication in this iteration.

### Дополнение по бренду (запрос пользователя)

- [x] Векторный SVG вместо JPG в интерфейсе; прозрачность и отдельная палитра для тёмных поверхностей.
- [x] Один мастер, проверяемые копии, общий Brand на каждой платформе; отсутствие внешних шрифтов/растра/SVG transformers.
- [x] Повторно пройдены 34 теста, TypeScript, web/Docker builds, iOS/Android/Web export и Expo doctor 21/21. Визуально проверены три фона и мобильная ширина 390px.

UI-проверка означает браузерный preview: сценарии входа/выхода, расчёта, урока и профиля выполнены на изолированных данных; empty/error ветки также просмотрены в исходном коде. Регистрация проверена как форма, полный registration E2E и native device QA не выполнены.
