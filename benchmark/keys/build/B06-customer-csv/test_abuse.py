import unittest

from app.reports import customers_csv

from ._csvdata import FORMULA_START, parse, store


class Abuse(unittest.TestCase):
    def export(self, user, account):
        try:
            return customers_csv(store(), user, account)
        except NotImplementedError:
            raise
        except Exception:
            return ""

    def test_no_cell_starts_a_formula(self):
        for row in parse(self.export("ada", "a1"))[1:]:
            for cell in row[:3]:
                self.assertFalse(cell.startswith(FORMULA_START), "formula cell %r" % cell)

    def test_other_account_customers_absent(self):
        self.assertNotIn("Secret Rival Customer", self.export("ada", "a1"))

    def test_admin_of_other_account_denied(self):
        self.assertNotIn("grace@example.test", self.export("zoe", "a1"))

    def test_viewer_denied(self):
        self.assertNotIn("grace@example.test", self.export("vic", "a1"))

    def test_stranger_denied(self):
        self.assertNotIn("grace@example.test", self.export("nobody", "a1"))
