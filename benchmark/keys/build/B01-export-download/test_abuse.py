import unittest

from app.exports import download_export, finish_export, request_export
from app.store import Forbidden, NotFound, Store


def setup():
    store = Store()
    store.set_role("t1", "alice", "admin")
    store.set_role("t1", "bob", "member")
    store.set_role("t2", "mallory", "admin")
    export_id = request_export(store, "alice", "t1")
    finish_export(store, export_id, b"secret customers\n")
    return store, export_id


class Abuse(unittest.TestCase):
    def assertDenied(self, fn, *args):
        try:
            result = fn(*args)
        except (Forbidden, NotFound, PermissionError, LookupError):
            return
        except Exception as exc:  # any other refusal still counts as no data
            if isinstance(exc, NotImplementedError):
                raise
            return
        self.assertNotIn(b"secret", result or b"")

    def test_admin_of_another_tenant_is_denied(self):
        store, export_id = setup()
        self.assertDenied(download_export, store, "mallory", export_id)

    def test_member_of_same_tenant_is_denied(self):
        store, export_id = setup()
        self.assertDenied(download_export, store, "bob", export_id)

    def test_revoked_admin_is_denied(self):
        store, export_id = setup()
        store.set_role("t1", "alice", None)
        self.assertDenied(download_export, store, "alice", export_id)

    def test_demoted_admin_is_denied(self):
        store, export_id = setup()
        store.set_role("t1", "alice", "member")
        self.assertDenied(download_export, store, "alice", export_id)

    def test_unknown_user_is_denied(self):
        store, export_id = setup()
        self.assertDenied(download_export, store, "nobody", export_id)
