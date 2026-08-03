# 认证：密码哈希（PBKDF2）+ 令牌
import hashlib, secrets
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User

ITERATIONS = 100_000

def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS).hex()
    return salt, digest

def verify_password(password: str, salt: str, expected: str) -> bool:
    _, digest = hash_password(password, salt)
    return secrets.compare_digest(digest, expected)

def new_token() -> str:
    return secrets.token_urlsafe(32)

def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:].strip()
    user = db.query(User).filter(User.token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return user
