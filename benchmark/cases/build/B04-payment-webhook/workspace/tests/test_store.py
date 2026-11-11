import unittest

from app.webhooks import Store


class StoreTests(unittest.TestCase):
    def test_new_invoice_is_unpaid(self):
        store = Store()
        store.add_invoice("inv_1", 500)
        self.assertFalse(store.invoices["inv_1"]["paid"])


if __name__ == "__main__":
    unittest.main()
