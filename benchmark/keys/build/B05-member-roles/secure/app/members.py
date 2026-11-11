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
    actor_role = store.get(workspace_id, actor_id)
    current = store.get(workspace_id, member_id)
    if new_role not in ROLES or actor_role not in ("owner", "admin") or current is None:
        raise Forbidden("not allowed")
    if actor_role != "owner" and ("owner" in (new_role, current)):
        raise Forbidden("only owners can grant or change ownership")
    store.set(workspace_id, member_id, new_role)
