"""Actions the bot can take on a customer's account."""

from . import billing


def issue_refund(account_id, amount_cents, reason):
    return billing.refund(account_id, amount_cents, reason)


def change_email(account_id, new_email):
    return billing.update_contact(account_id, email=new_email)


def lookup_account(email):
    return billing.find_account(email)


TOOLS = {"issue_refund": issue_refund, "change_email": change_email, "lookup_account": lookup_account}
