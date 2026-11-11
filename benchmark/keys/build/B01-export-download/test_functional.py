import unittest

from app.exports import download_export, finish_export, request_export
from app.store import Store


class Functional(unittest.TestCase):
    def test_admin_downloads_their_finished_export(self):
        store = Store()
        store.set_role("t1", "alice", "admin")
        export_id = request_export(store, "alice", "t1")
        finish_export(store, export_id, b"name,email\nAda,ada@example.test\n")
        self.assertEqual(download_export(store, "alice", export_id), b"name,email\nAda,ada@example.test\n")
