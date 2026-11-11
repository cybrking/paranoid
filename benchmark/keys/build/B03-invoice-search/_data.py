from app.invoices import add_invoice, connect

ALICE = {"id": "alice", "tenant_id": "t1"}


def own_tenant_only():
    conn = connect()
    add_invoice(conn, "t1", "Acme Corp", 1200, "March retainer", 1)
    add_invoice(conn, "t1", "Globex", 5000, "Acme referral bonus", 2)
    add_invoice(conn, "t1", "Umbrella", 700, "printer toner", 3)
    return conn


def seeded():
    conn = own_tenant_only()
    add_invoice(conn, "t2", "Acme Holdings", 990000, "confidential settlement", 4)
    add_invoice(conn, "t2", "Hooli", 4400, "other tenant", 5)
    return conn
