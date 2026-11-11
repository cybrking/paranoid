import unittest

from app.webhooks import handle_payco_webhook

from ._payco import Clock, body_for, sign, store_with_invoice


class Functional(unittest.TestCase):
    def test_signed_event_marks_invoice_paid(self):
        store = store_with_invoice()
        body = body_for()
        with Clock():
            status = handle_payco_webhook(store, sign(body), body)
        self.assertTrue(200 <= status < 300)
        self.assertTrue(store.invoices["inv_42"]["paid"])

    def test_lowercase_header_name(self):
        store = store_with_invoice()
        body = body_for()
        headers = {k.lower(): v for k, v in sign(body).items()}
        with Clock():
            status = handle_payco_webhook(store, headers, body)
        self.assertTrue(200 <= status < 300)
        self.assertTrue(store.invoices["inv_42"]["paid"])

    def test_other_event_types_are_acknowledged(self):
        store = store_with_invoice()
        body = body_for(event_type="payment.created")
        with Clock():
            status = handle_payco_webhook(store, sign(body), body)
        self.assertTrue(200 <= status < 300)
        self.assertFalse(store.invoices["inv_42"]["paid"])
