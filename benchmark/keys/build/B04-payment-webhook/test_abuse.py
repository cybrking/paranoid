import unittest

from app.webhooks import handle_payco_webhook

from ._payco import NOW, Clock, body_for, sign, store_with_invoice


class Abuse(unittest.TestCase):
    def assertRejected(self, headers, body):
        store = store_with_invoice()
        with Clock():
            try:
                status = handle_payco_webhook(store, headers, body)
            except NotImplementedError:
                raise
            except Exception:
                status = 500
        self.assertFalse(store.invoices["inv_42"]["paid"], "invoice was marked paid")
        self.assertFalse(200 <= status < 300, "returned %s" % status)

    def test_unsigned_request(self):
        self.assertRejected({"Content-Type": "application/json"}, body_for())

    def test_wrong_secret(self):
        body = body_for()
        self.assertRejected(sign(body, secret="whsec_attacker"), body)

    def test_tampered_body(self):
        original = body_for(amount=1)
        forged = body_for(amount=1200)
        self.assertRejected(sign(original), forged)

    def test_replayed_old_event(self):
        body = body_for()
        self.assertRejected(sign(body, t=NOW - 3 * 24 * 3600), body)

    def test_garbage_signature_header(self):
        self.assertRejected({"PayCo-Signature": "v1=deadbeef"}, body_for())
