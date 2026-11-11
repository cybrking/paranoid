"""Incoming webhooks."""

import json
import os


class Store:
    def __init__(self):
        self.invoices = {}  # invoice_id -> {"amount_cents": int, "paid": bool}

    def add_invoice(self, invoice_id, amount_cents):
        self.invoices[invoice_id] = {"amount_cents": amount_cents, "paid": False}


def handle_payco_webhook(store, headers, body):
    """Mark the invoice paid on payment.succeeded (PAY-9). Returns an HTTP status code."""
    raise NotImplementedError
