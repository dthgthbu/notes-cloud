# Notes Cloud

Сервис приватных текстовых заметок с авторизацией.

Возможности

- Регистрация и вход пользователей.
- Пароли хранятся в виде хэша (bcrypt через passlib).
- Авторизация через JWT в httponly-cookie.
- Каждый пользователь видит и может удалять только свои заметки.
- REST API на FastAPI + статический фронтенд (HTML + JS).
- Хранение данных — SQLite (стандартная библиотека Python).

Стек

- Python 3.10+
- FastAPI
- Uvicorn
- SQLite
- passlib[bcrypt], PyJWT

Запуск локально

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
uvicorn app.main:app --reload --port 8000

Открыть в браузере: http://127.0.0.1:8000

API

POST   /api/register       — регистрация
POST   /api/login          — вход
POST   /api/logout         — выход
GET    /api/me             — текущий пользователь
GET    /api/notes          — список своих заметок
POST   /api/notes          — создать заметку
DELETE /api/notes/{id}     — удалить свою заметку

Деплой

Сервис разворачивается на VPS и запускается через systemd + uvicorn на порту 8000.
