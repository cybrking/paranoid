"""Reports."""

import csv
import io


class Forbidden(Exception):
    pass


class Store:
    def __init__(self):
        self.roles = {}      # (account_id, user_id) -> "admin" | "viewer"
        self.customers = []  # {"account_id", "name", "email", "signup_source", "total_spent"}

    def add_customer(self, account_id, name, email, signup_source, total_spent):
        self.customers.append({
            "account_id": account_id, "name": name, "email": email,
            "signup_source": signup_source, "total_spent": total_spent,
        })


def customer_count(store, account_id):
    return sum(1 for c in store.customers if c["account_id"] == account_id)


def customers_csv(store, user_id, account_id):
    """CSV text of the account's customers for the admin export (RPT-2)."""
    raise NotImplementedError
