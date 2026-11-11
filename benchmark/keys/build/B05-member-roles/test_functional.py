import unittest

from app.members import change_role

from ._team import team


class Functional(unittest.TestCase):
    def test_admin_promotes_member_to_admin(self):
        store = team()
        change_role(store, "ada", "w1", "bob", "admin")
        self.assertEqual(store.get("w1", "bob"), "admin")

    def test_admin_demotes_admin_to_member(self):
        store = team()
        store.set("w1", "cy", "admin")
        change_role(store, "ada", "w1", "cy", "member")
        self.assertEqual(store.get("w1", "cy"), "member")

    def test_owner_promotes_member(self):
        store = team()
        change_role(store, "olive", "w1", "bob", "admin")
        self.assertEqual(store.get("w1", "bob"), "admin")
