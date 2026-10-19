# Контракты API — Notes Cloud

Все эндпоинты возвращают JSON. Ошибки всегда вида `{"detail": "строка"}`.
Авторизация — JWT в httponly-cookie `access_token`.

## POST /api/register

Запрос: `{"username": str (>= 3), "password": str (>= 6)}`

200: `{"ok": true, "username": str}` + Set-Cookie: access_token
400: `{"detail": "Логин >= 3 символов, пароль >= 6 символов"}`
400: `{"detail": "Такой пользователь уже есть"}`
422: если тело не JSON или не прошло валидацию Pydantic

## POST /api/login

Запрос: `{"username": str, "password": str}`

200: `{"ok": true, "username": str}` + Set-Cookie: access_token
401: `{"detail": "Неверный логин или пароль"}`
422: если тело не JSON или не прошло валидацию Pydantic

## GET /health

Публичный эндпоинт без авторизации. Используется для проверки, что сервис жив.

200: `{"status": "ok"}`


## POST /api/logout

Запрос: пусто

200: `{"ok": true}` + удаление cookie

## GET /api/me

Требует авторизации.

200: `{"id": int, "username": str}`
401: `{"detail": "not authenticated"}`


## GET /api/notes

Требует авторизации.

Query-параметр (опциональный): `sort` — `"desc"` (по умолчанию) или `"asc"`.
Любое другое значение трактуется как `"desc"`.

200: массив объектов `{"id": int, "title": str, "body": str, "created_at": str}`
     Отсортирован по id: DESC (свежие сверху) или ASC. Только заметки текущего пользователя.
401: `{"detail": "not authenticated"}`


## GET /api/notes/count

Требует авторизации.

200: `{"count": int}` — количество заметок текущего пользователя
401: `{"detail": "not authenticated"}`


## POST /api/notes

Требует авторизации.

Запрос: `{"title": str, "body": str}`

200: `{"ok": true}`
400: `{"detail": "Заполни заголовок и текст"}`
401: `{"detail": "not authenticated"}`

## DELETE /api/notes/{note_id}

Требует авторизации. `note_id` — целое число в пути.

200: `{"ok": true}`
     Удаляет только если заметка принадлежит текущему пользователю.
     Если нет — возвращает 200, но ничего не удаляет.
401: `{"detail": "not authenticated"}`

## База данных

### Таблица users
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `username` TEXT UNIQUE NOT NULL
- `password_hash` TEXT NOT NULL (формат: `pbkdf2_sha256$<iters>$<salt_hex>$<hash_hex>`)

### Таблица notes
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id` INTEGER NOT NULL (FK → users.id)
- `title` TEXT NOT NULL (макс. 200 символов)
- `body` TEXT NOT NULL
- `created_at` TEXT DEFAULT CURRENT_TIMESTAMP (UTC)

## Правило обратной совместимости

-  Можно: добавлять новые поля в ответ, добавлять новые эндпоинты.
-  Нельзя: удалять поля, переименовывать, менять тип, менять коды ответов.
- Если нужно ломающее изменение — новый префикс `/api/v2/...`, старая версия продолжает работать.

## Как проверяются контракты

Тесты в `tests/test_api.py`. Запуск:

    pytest -v

Если тест упал — значит контракт нарушен.
