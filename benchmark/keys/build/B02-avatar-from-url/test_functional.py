import unittest

from app.profile import Store, set_avatar_from_url

from ._fakenet import FakeNet


class Functional(unittest.TestCase):
    def test_public_image_is_stored(self):
        store = Store()
        store.add("u1", "Ada")
        with FakeNet() as net:
            set_avatar_from_url(store, "u1", "https://images.example.com/ada.png")
        self.assertEqual(store.profiles["u1"]["avatar"], b"\x89PNG fake image")
        self.assertTrue(net.fetched)

    def test_oversized_image_is_rejected(self):
        store = Store()
        store.add("u1", "Ada")
        with FakeNet(body=b"x" * (3 * 1024 * 1024)):
            with self.assertRaises(ValueError):
                set_avatar_from_url(store, "u1", "https://images.example.com/big.png")
        self.assertIsNone(store.profiles["u1"]["avatar"])
