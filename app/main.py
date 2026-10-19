from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .auth import (COOKIE_NAME, create_token, decode_token, hash_password,
                   verify_password)
from .database import get_db, init_db

app = FastAPI(title="Notes Cloud")

init_db()


class RegisterIn(BaseModel):
    username: str
    password: str


class LoginIn(BaseModel):
    username: str
    password: str


class NoteIn(BaseModel):
    title: str
    body: str


def current_user(access_token: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    if not access_token:
        return None
    user_id = decode_token(access_token)
    if user_id is None:
        return None
    db = get_db()
    row = db.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    return dict(row) if row else None


@app.post("/api/register")
def register(data: RegisterIn, response: Response):
    username = data.username.strip()
    if len(username) < 3 or len(data.password) < 6:
        raise HTTPException(400, "Логин >= 3 символов, пароль >= 6 символов")

    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        db.close()
        raise HTTPException(400, "Такой пользователь уже есть")

    db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, hash_password(data.password)),
    )
    db.commit()
    user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()

    token = create_token(user_id)
    response.set_cookie(
        COOKIE_NAME, token,
        httponly=True, samesite="lax", max_age=60 * 60 * 24 * 7,
    )
    return {"ok": True, "username": username}


@app.post("/api/login")
def login(data: LoginIn, response: Response):
    db = get_db()
    row = db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (data.username.strip(),),
    ).fetchone()
    db.close()

    if row is None or not verify_password(data.password, row["password_hash"]):
        raise HTTPException(401, "Неверный логин или пароль")

    token = create_token(row["id"])
    response.set_cookie(
        COOKIE_NAME, token,
        httponly=True, samesite="lax", max_age=60 * 60 * 24 * 7,
    )
    return {"ok": True, "username": row["username"]}


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@app.get("/api/me")
def me(user=Depends(current_user)):
    if user is None:
        raise HTTPException(401, "not authenticated")
    return user


@app.get("/api/notes")
def list_notes(user=Depends(current_user)):
    if user is None:
        raise HTTPException(401, "not authenticated")
    db = get_db()
    rows = db.execute(
        "SELECT id, title, body, created_at FROM notes "
        "WHERE user_id = ? ORDER BY id DESC",
        (user["id"],),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]

@app.get("/api/notes/count")
def count_notes(user=Depends(current_user)):
    if user is None:
        raise HTTPException(401, "not authenticated")
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) AS c FROM notes WHERE user_id = ?",
        (user["id"],),
    ).fetchone()
    db.close()
    return {"count": row["c"]}



@app.post("/api/notes")
def create_note(data: NoteIn, user=Depends(current_user)):
    if user is None:
        raise HTTPException(401, "not authenticated")
    title, body = data.title.strip(), data.body.strip()
    if not title or not body:
        raise HTTPException(400, "Заполни заголовок и текст")

    db = get_db()
    db.execute(
        "INSERT INTO notes (user_id, title, body) VALUES (?, ?, ?)",
        (user["id"], title[:200], body),
    )
    db.commit()
    db.close()
    return {"ok": True}


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int, user=Depends(current_user)):
    if user is None:
        raise HTTPException(401, "not authenticated")
    db = get_db()
    db.execute(
        "DELETE FROM notes WHERE id = ? AND user_id = ?",
        (note_id, user["id"]),
    )
    db.commit()
    db.close()
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
