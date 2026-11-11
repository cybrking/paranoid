import unittest

from app.money import format_money


class Functional(unittest.TestCase):
    def test_table_from_the_ticket(self):
        self.assertEqual(format_money(123450, "USD"), "$1,234.50")
        self.assertEqual(format_money(123450, "EUR"), "1.234,50 €")
        self.assertEqual(format_money(5, "USD"), "$0.05")
        self.assertEqual(format_money(-2500, "USD"), "-$25.00")
