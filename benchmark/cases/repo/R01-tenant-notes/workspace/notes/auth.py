"""Login and sessions."""

import hashlib
import hmac
import json
import os
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode

SESSION_KEY = os.environ.get("SESSION_KEY", "dev-session-key").encode()
SESSION_TTL = 24 * 3600


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def check_password(user, password):
    return user["password_hash"] == hash_password(password)


def issue_session(user, membership):
    payload = {
        "user_id": user["id"],
        "tenant_id": membership["tenant_id"],
        "role": membership["role"],
        "exp": int(time.time()) + SESSION_TTL,
    }
    body = urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(SESSION_KEY, body.encode(), hashlib.sha256).hexdigest()
    return body + "." + sig


def read_session(token):
    body, _, sig = token.partition(".")
    expected = hmac.new(SESSION_KEY, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    payload = json.loads(urlsafe_b64decode(body))
    if payload["exp"] < time.time():
        return None
    return payload
