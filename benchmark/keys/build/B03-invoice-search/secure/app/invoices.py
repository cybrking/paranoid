"""Invoices. Every tenant's invoices live in the same table."""

import sqlite3

SCHEMA = """
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    memo TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL
);
"""


def connect():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_invoice(conn, tenant_id, customer, amount_cents, memo, created_at):
    cur = conn.execute(
        "INSERT INTO invoices (tenant_id, customer, amount_cents, memo, created_at) VALUES (?, ?, ?, ?, ?)",
        (tenant_id, customer, amount_cents, memo, created_at),
    )
    return cur.lastrowid


def list_invoices(conn, user):
    rows = conn.execute(
        "SELECT id, customer, amount_cents, memo FROM invoices WHERE tenant_id = ? ORDER BY created_at DESC",
        (user["tenant_id"],),
    )
    return [dict(row) for row in rows]


def search_invoices(conn, user, query):
    """Invoices whose customer or memo contains query, newest first (INV-31)."""
    pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    rows = conn.execute(
        "SELECT id, customer, amount_cents, memo FROM invoices WHERE tenant_id = ? "
        "AND (customer LIKE ? ESCAPE '\\' OR memo LIKE ? ESCAPE '\\') ORDER BY created_at DESC",
        (user["tenant_id"], pattern, pattern),
    )
    return [dict(row) for row in rows]
