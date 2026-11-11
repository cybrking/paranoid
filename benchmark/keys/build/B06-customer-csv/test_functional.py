import unittest

from app.reports import Store, customers_csv

from ._csvdata import parse


def plain_store():
    s = Store()
    s.roles[("a1", "ada")] = "admin"
    s.add_customer("a1", "Grace Hopper", "grace@example.test", "web", 120)
    s.add_customer("a1", "Lovelace, Ada", "ada@example.test", "referral", 75.5)
    return s


class Functional(unittest.TestCase):
    def test_header_and_rows(self):
        rows = parse(customers_csv(plain_store(), "ada", "a1"))
        self.assertEqual(rows[0], ["name", "email", "signup_source", "total_spent"])
        self.assertEqual([r[0] for r in rows[1:]], ["Grace Hopper", "Lovelace, Ada"])
        self.assertEqual(rows[2][1], "ada@example.test")
