"""Storage. One table per kind, every row carries tenant_id."""

USERS = {}        # user_id -> {"id", "email", "password_hash"}
MEMBERSHIPS = {}  # (tenant_id, user_id) -> {"tenant_id", "user_id", "role"}
NOTES = {}        # note_id -> {"id", "tenant_id", "author_id", "title", "body"}


def membership(tenant_id, user_id):
    return MEMBERSHIPS.get((tenant_id, user_id))


def remove_member(tenant_id, user_id):
    MEMBERSHIPS.pop((tenant_id, user_id), None)
