"""Workspace membership and roles."""

ROLES = ("owner", "admin", "member")


class Forbidden(Exception):
    pass


class Store:
    def __init__(self):
        self.roles = {}  # (workspace_id, user_id) -> role

    def set(self, workspace_id, user_id, role):
        self.roles[(workspace_id, user_id)] = role

    def get(self, workspace_id, user_id):
        return self.roles.get((workspace_id, user_id))


def members(store, workspace_id):
    return sorted((uid, role) for (wid, uid), role in store.roles.items() if wid == workspace_id)


def change_role(store, actor_id, workspace_id, member_id, new_role):
    """Change member_id's role in workspace_id (TEAM-4)."""
    if new_role not in ROLES:
        raise ValueError(new_role)
    if store.get(workspace_id, actor_id) not in ("owner", "admin"):
        raise Forbidden("admins only")
    store.set(workspace_id, member_id, new_role)
