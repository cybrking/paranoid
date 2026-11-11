import unittest

from app.members import Store, members


class MembersTests(unittest.TestCase):
    def test_lists_workspace_members(self):
        store = Store()
        store.set("w1", "olive", "owner")
        store.set("w1", "ada", "admin")
        store.set("w2", "zed", "owner")
        self.assertEqual(members(store, "w1"), [("ada", "admin"), ("olive", "owner")])


if __name__ == "__main__":
    unittest.main()
