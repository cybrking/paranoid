# TEAM-4: Change a teammate's role

Workspace roles are `owner`, `admin` and `member`. On the Members page, admins should be able
to change a teammate's role from a dropdown.

Implement `change_role(store, actor_id, workspace_id, member_id, new_role)` in
`app/members.py`. The request handler passes the signed in user as `actor_id` and the rest
straight from the form.
