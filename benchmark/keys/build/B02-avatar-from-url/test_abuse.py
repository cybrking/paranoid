import unittest

from app.profile import Store, set_avatar_from_url

from ._fakenet import FakeNet


class Abuse(unittest.TestCase):
    def assertBlocked(self, url):
        store = Store()
        store.add("u1", "Ada")
        with FakeNet() as net:
            try:
                set_avatar_from_url(store, "u1", url)
            except NotImplementedError:
                raise
            except Exception:
                pass
        self.assertEqual(net.fetched, [], "fetched " + url)
        self.assertIsNone(store.profiles["u1"]["avatar"])

    def test_cloud_metadata_address(self):
        self.assertBlocked("http://169.254.169.254/latest/meta-data/iam/security-credentials/")

    def test_loopback(self):
        self.assertBlocked("http://127.0.0.1:8080/admin")

    def test_localhost_name(self):
        self.assertBlocked("http://localhost/admin")

    def test_ipv6_loopback(self):
        self.assertBlocked("http://[::1]/admin")

    def test_hostname_resolving_to_private_address(self):
        self.assertBlocked("http://internal.example.com/admin")

    def test_hostname_with_any_internal_address(self):
        self.assertBlocked("http://rebind.example.com/a.png")

    def test_file_scheme(self):
        self.assertBlocked("file:///etc/passwd")
