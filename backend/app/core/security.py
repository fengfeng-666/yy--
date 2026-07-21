import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import get_settings
from app.core.constants import ErrorCode
from app.core.exceptions import AppException


PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 600_000
ACCESS_TOKEN_TYPE = "access"


def create_token_expire_at(minutes: int) -> datetime:
    return datetime.now(UTC) + timedelta(minutes=minutes)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt}${password_hash}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        algorithm_label, iterations, salt, expected_hash = hashed_password.split("$", maxsplit=3)
        algorithm = algorithm_label.removeprefix("pbkdf2_")
        actual_hash = hashlib.pbkdf2_hmac(
            algorithm,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
    except (TypeError, ValueError):
        return False

    return hmac.compare_digest(actual_hash, expected_hash)


def create_access_token(user_id: int) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = create_token_expire_at(settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,
        "iat": datetime.now(UTC),
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise AppException(
            code=ErrorCode.TOKEN_EXPIRED,
            message="登录已过期，请重新登录",
            status_code=401,
        ) from exc
    except InvalidTokenError as exc:
        raise AppException(
            code=ErrorCode.UNAUTHORIZED,
            message="登录凭证无效",
            status_code=401,
        ) from exc

    if payload.get("type") != ACCESS_TOKEN_TYPE or "sub" not in payload:
        raise AppException(
            code=ErrorCode.UNAUTHORIZED,
            message="登录凭证无效",
            status_code=401,
        )

    return payload
