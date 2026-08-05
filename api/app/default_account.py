"""Create an explicitly configured local demonstration account during seeding."""

import os

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import User
from app.schemas import RegisterIn


DEFAULT_ACCOUNT_EMAIL_ENV = "DEFAULT_ACCOUNT_EMAIL"
DEFAULT_ACCOUNT_PASSWORD_ENV = "DEFAULT_ACCOUNT_PASSWORD"


def ensure_configured_default_account(db: Session) -> bool:
    """Create the configured account once without changing an existing user."""
    email = os.environ.get(DEFAULT_ACCOUNT_EMAIL_ENV)
    password = os.environ.get(DEFAULT_ACCOUNT_PASSWORD_ENV)
    if not email and not password:
        return False
    if not email or not password:
        raise RuntimeError(
            "DEFAULT_ACCOUNT_EMAIL and DEFAULT_ACCOUNT_PASSWORD must be configured together"
        )

    try:
        credentials = RegisterIn(email=email.strip(), password=password)
    except ValidationError:
        raise RuntimeError(
            "The configured default account must meet the normal registration requirements"
        ) from None

    normalized_email = credentials.email.lower()
    if db.query(User).filter(User.email == normalized_email).first():
        return False

    salt, password_hash = hash_password(credentials.password)
    db.add(User(email=normalized_email, password_hash=password_hash, salt=salt))
    return True
