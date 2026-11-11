"""In-memory data store for the exports feature."""


class NotFound(Exception):
    """The thing asked for doesn't exist, or the caller may not know it exists."""


class Forbidden(Exception):
    """The caller isn't allowed to do this."""


class Store:
    def __init__(self):
        self.users = {}        # user_id -> {"id": str, "email": str}
        self.memberships = {}  # (tenant_id, user_id) -> "admin" | "member"
        self.exports = {}      # export_id -> {"id", "tenant_id", "requested_by", "status", "path"}
        self.files = {}        # path -> bytes

    def add_user(self, user_id, email):
        self.users[user_id] = {"id": user_id, "email": email}

    def set_role(self, tenant_id, user_id, role):
        if role is None:
            self.memberships.pop((tenant_id, user_id), None)
        else:
            self.memberships[(tenant_id, user_id)] = role

    def role_of(self, tenant_id, user_id):
        return self.memberships.get((tenant_id, user_id))
