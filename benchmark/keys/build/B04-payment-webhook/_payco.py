import hashlib
import hmac
import json
import os
import time
from contextlib import ExitStack
from unittest import mock

SECRET = "whsec_test_4f1c2e"
NOW = 1_800_000_000


def body_for(invoice_id="inv_42", amount=1200, event_type="payment.succeeded"):
    return json.dumps({"id": "evt_1", "type": event_type,
                       "data": {"invoice_id": invoice_id, "amount_cents": amount}}).encode()


def sign(body, t=NOW, secret=SECRET):
    mac = hmac.new(secret.encode(), str(t).encode() + b"." + body, hashlib.sha256).hexdigest()
    return {"PayCo-Signature": "t=%d,v1=%s" % (t, mac), "Content-Type": "application/json"}


class Clock:
    def __enter__(self):
        self._stack = ExitStack()
        self._stack.enter_context(mock.patch.dict(os.environ, {"PAYCO_WEBHOOK_SECRET": SECRET}))
        self._stack.enter_context(mock.patch("time.time", lambda: float(NOW)))
        self._stack.enter_context(mock.patch("time.monotonic", lambda: float(NOW)))
        return self

    def __exit__(self, *exc):
        self._stack.close()
        return False


def store_with_invoice():
    from app.webhooks import Store
    store = Store()
    store.add_invoice("inv_42", 1200)
    return store
