import unittest

import app.money


class ImportTests(unittest.TestCase):
    def test_module_imports(self):
        self.assertTrue(hasattr(app.money, "format_money"))


if __name__ == "__main__":
    unittest.main()
