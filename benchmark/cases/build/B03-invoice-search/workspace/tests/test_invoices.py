import unittest

from app.invoices import add_invoice, connect, list_invoices


class ListTests(unittest.TestCase):
    def test_lists_own_tenant_newest_first(self):
        conn = connect()
        add_invoice(conn, "t1", "Acme", 100, "first", 1)
        add_invoice(conn, "t1", "Globex", 200, "second", 2)
        add_invoice(conn, "t2", "Initech", 300, "other tenant", 3)
        rows = list_invoices(conn, {"id": "u1", "tenant_id": "t1"})
        self.assertEqual([r["customer"] for r in rows], ["Globex", "Acme"])


if __name__ == "__main__":
    unittest.main()
