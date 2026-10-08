import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta

import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 24 * 7
COOKIE_NAME = "access_token"

PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iters)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def create_token(user_id: int) -> str:
    exp = datetime.utcnow() + timedelta(hours=TOKEN_TTL_HOURS)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except Exception:
        return None
