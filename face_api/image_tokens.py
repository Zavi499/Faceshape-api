"""Signed URL helpers for temporary image access."""

from __future__ import annotations

import hmac
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import urlencode

from config import IMAGE_URL_SECRET


def _expiry_timestamp(expires_at: datetime) -> int:
    """Convert an expiration datetime into a UTC Unix timestamp."""

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return int(expires_at.timestamp())


def create_image_access_token(filename: str, expires_at: datetime) -> tuple[int, str]:
    """Create a deterministic HMAC token for a filename and expiration time."""

    expires = _expiry_timestamp(expires_at)
    payload = f"{filename}:{expires}".encode("utf-8")
    signature = hmac.new(IMAGE_URL_SECRET.encode("utf-8"), payload, sha256).hexdigest()
    return expires, signature


def build_signed_image_url(filename: str, expires_at: datetime) -> str:
    """Build a relative image URL with signed, expiring query parameters."""

    expires, token = create_image_access_token(filename, expires_at)
    query = urlencode({"expires": str(expires), "token": token})
    return f"/image/{filename}?{query}"


def validate_image_access_token(filename: str, expires: str | None, token: str | None) -> bool:
    """Return whether a signed image token is valid and not expired."""

    if not expires or not token:
        return False

    try:
        expires_at = int(expires)
    except ValueError:
        return False

    if datetime.now(timezone.utc).timestamp() > expires_at:
        return False

    payload = f"{filename}:{expires_at}".encode("utf-8")
    expected = hmac.new(IMAGE_URL_SECRET.encode("utf-8"), payload, sha256).hexdigest()
    return hmac.compare_digest(expected, token)
