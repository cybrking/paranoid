import unittest

from app.reports import Store, customer_count


class ReportTests(unittest.TestCase):
    def test_counts_one_account(self):
        store = Store()
        store.add_customer("a1", "Ada", "ada@example.test", "web", 10)
        store.add_customer("a2", "Bo", "bo@example.test", "web", 5)
        self.assertEqual(customer_count(store, "a1"), 1)


if __name__ == "__main__":
    unittest.main()
