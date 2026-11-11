# INV-31: Search box on the invoices page

Add a search box above the invoices table. Typing part of a customer name or a word from
the memo should filter the list.

Implement `search_invoices(conn, user, query)` in `app/invoices.py`. It returns a list of
dicts with `id`, `customer`, `amount_cents` and `memo`, newest first. `user` is the signed in
user from the session (`{"id": ..., "tenant_id": ...}`).
