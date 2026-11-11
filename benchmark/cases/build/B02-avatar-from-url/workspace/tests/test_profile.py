import unittest

from app.profile import Store, rename


class ProfileTests(unittest.TestCase):
    def test_rename(self):
        store = Store()
        store.add("u1", "Ada")
        rename(store, "u1", "Ada L")
        self.assertEqual(store.profiles["u1"]["name"], "Ada L")

    def test_rename_rejects_empty(self):
        store = Store()
        store.add("u1", "Ada")
        with self.assertRaises(ValueError):
            rename(store, "u1", "")


if __name__ == "__main__":
    unittest.main()
