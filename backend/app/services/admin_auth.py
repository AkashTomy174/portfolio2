"""
app/services/admin_auth.py

Admin session cookie signing and verification.

Uses itsdangerous.TimestampSigner so cookies:
  - are cryptographically signed (tamper-proof)
  - carry an embedded timestamp (max_age enforced on verify)
  - contain no sensitive data (payload is just the literal string "admin")

Cookie name : ADMIN_COOKIE
Max age     : 8 hours (configurable via MAX_AGE_SECONDS)
Algorithm   : HMAC-SHA1 (itsdangerous default, sufficient for this use case)
"""
from __future__ import annotations

from itsdangerous import TimestampSigner, SignatureExpired, BadSignature

ADMIN_COOKIE = "admin_session"
MAX_AGE_SECONDS = 8 * 60 * 60   # 8 hours
_PAYLOAD = "admin"


def make_cookie(secret: str) -> str:
    """Return a signed cookie value for the admin session."""
    signer = TimestampSigner(secret)
    return signer.sign(_PAYLOAD).decode()


def verify_cookie(value: str, secret: str) -> bool:
    """
    Return True if the cookie value is a valid, unexpired admin session.

    Returns False (never raises) for any invalid or expired value so callers
    can redirect to login without try/except at the call site.
    """
    signer = TimestampSigner(secret)
    try:
        signer.unsign(value, max_age=MAX_AGE_SECONDS)
        return True
    except (SignatureExpired, BadSignature, Exception):
        return False
