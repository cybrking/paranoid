import unittest

from app.invoices import search_invoices

from ._data import ALICE, seeded


class Abuse(unittest.TestCase):
    def results(self, query):
        try:
            return search_invoices(seeded(), ALICE, query)
        except NotImplementedError:
            raise
        except Exception:
            return []

    def assertOnlyOwnTenant(self, query):
        customers = {r["customer"] for r in self.results(query)}
        self.assertFalse(customers & {"Acme Holdings", "Hooli"}, "leaked " + repr(customers))

    def test_other_tenant_rows_never_match(self):
        self.assertOnlyOwnTenant("acme")

    def test_injection_cannot_widen_results(self):
        self.assertOnlyOwnTenant("%' OR '1'='1")

    def test_union_injection(self):
        self.assertOnlyOwnTenant("x%' UNION SELECT id, customer, amount_cents, memo FROM invoices --")

    def test_comment_injection(self):
        self.assertOnlyOwnTenant("%' OR 1=1 --")
