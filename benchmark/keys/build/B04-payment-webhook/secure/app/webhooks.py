"""Incoming webhooks."""

import hashlib
import hmac
import json
import os
import time

TOLERANCE_SECONDS = 300


class Store:
    def __init__(self):
        self.invoices = {}  # invoice_id -> {"amount_cents": int, "paid": bool}

    def add_invoice(self, invoice_id, amount_cents):
        self.invoices[invoice_id] = {"amount_cents": amount_cents, "paid": False}


def handle_payco_webhook(store, headers, body):
    """Mark the invoice paid on payment.succeeded (PAY-9). Returns an HTTP status code."""
    secret = os.environ.get("PAYCO_WEBHOOK_SECRET")
    lowered = {k.lower(): v for k, v in headers.items()}
    header = lowered.get("payco-signature", "")
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    if not secret or "t" not in parts or "v1" not in parts or not parts["t"].isdigit():
        return 400
    if abs(time.time() - int(parts["t"])) > TOLERANCE_SECONDS:
        return 400
    expected = hmac.new(secret.encode(), parts["t"].encode() + b"." + body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, parts["v1"]):
        return 400
    event = json.loads(body)
    if event.get("type") == "payment.succeeded":
        invoice = store.invoices.get(event.get("data", {}).get("invoice_id"))
        if invoice is not None:
            invoice["paid"] = True
    return 200
