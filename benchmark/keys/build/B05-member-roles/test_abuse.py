import unittest

from app.members import change_role

from ._team import team


class Abuse(unittest.TestCase):
    def attempt(self, *args):
        store = team()
        before = dict(store.roles)
        try:
            change_role(store, *args)
        except NotImplementedError:
            raise
        except Exception:
            pass
        return before, store.roles

    def assertUnchanged(self, *args):
        before, after = self.attempt(*args)
        self.assertEqual(before, after, "roles changed by %r" % (args,))

    def test_member_promotes_self(self):
        self.assertUnchanged("bob", "w1", "bob", "admin")

    def test_member_changes_someone_else(self):
        self.assertUnchanged("bob", "w1", "cy", "admin")

    def test_admin_of_other_workspace(self):
        self.assertUnchanged("max", "w2", "bob", "admin")

    def test_admin_targets_other_workspace_member_through_own_workspace(self):
        self.assertUnchanged("max", "w1", "bob", "admin")

    def test_admin_grants_owner(self):
        self.assertUnchanged("ada", "w1", "bob", "owner")

    def test_admin_demotes_owner(self):
        self.assertUnchanged("ada", "w1", "olive", "member")

    def test_unknown_role(self):
        self.assertUnchanged("ada", "w1", "bob", "superadmin")

    def test_adds_non_member(self):
        self.assertUnchanged("ada", "w1", "mallory", "admin")
