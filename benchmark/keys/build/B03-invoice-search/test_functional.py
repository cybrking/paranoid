import unittest

from app.invoices import search_invoices

from ._data import ALICE, own_tenant_only as seeded


class Functional(unittest.TestCase):
    def test_matches_customer_or_memo_newest_first(self):
        rows = search_invoices(seeded(), ALICE, "acme")
        self.assertEqual([r["customer"] for r in rows], ["Globex", "Acme Corp"])

    def test_no_match(self):
        self.assertEqual(search_invoices(seeded(), ALICE, "zebra"), [])

    def test_apostrophe_in_query(self):
        self.assertEqual(search_invoices(seeded(), ALICE, "o'brien"), [])
