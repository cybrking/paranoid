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
    if store.roles.get((account_id, user_id)) != "admin":
        raise Forbidden("admins only")

    def safe(value):
        text = str(value)
        return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["name", "email", "signup_source", "total_spent"])
    for c in store.customers:
        if c["account_id"] == account_id:
            writer.writerow([safe(c["name"]), safe(c["email"]), safe(c["signup_source"]), c["total_spent"]])
    return out.getvalue()
