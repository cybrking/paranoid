"""Stand-in for the billing service client."""

ACCOUNTS = {}


def find_account(email):
    return next((a for a in ACCOUNTS.values() if a["email"] == email), None)


def refund(account_id, amount_cents, reason):
    ACCOUNTS[account_id]["refunds"].append((amount_cents, reason))
    return {"ok": True}


def update_contact(account_id, email):
    ACCOUNTS[account_id]["email"] = email
    return {"ok": True}
