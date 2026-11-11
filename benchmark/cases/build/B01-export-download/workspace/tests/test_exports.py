import unittest

from app.exports import request_export, finish_export
from app.store import Forbidden, Store


class RequestExportTests(unittest.TestCase):
    def test_admin_can_request(self):
        store = Store()
        store.set_role("t1", "alice", "admin")
        export_id = request_export(store, "alice", "t1")
        self.assertEqual(store.exports[export_id]["status"], "queued")

    def test_member_cannot_request(self):
        store = Store()
        store.set_role("t1", "bob", "member")
        with self.assertRaises(Forbidden):
            request_export(store, "bob", "t1")

    def test_finish_marks_done(self):
        store = Store()
        store.set_role("t1", "alice", "admin")
        export_id = request_export(store, "alice", "t1")
        finish_export(store, export_id, b"name\n")
        self.assertEqual(store.exports[export_id]["status"], "done")


if __name__ == "__main__":
    unittest.main()
