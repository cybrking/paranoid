"""Customer exports."""

import itertools

from .store import Forbidden, NotFound

_ids = itertools.count(1)


def request_export(store, user_id, tenant_id):
    """Queue a customer export. Only tenant admins may request one."""
    if store.role_of(tenant_id, user_id) != "admin":
        raise Forbidden("only tenant admins can request exports")
    export_id = "exp_%d" % next(_ids)
    store.exports[export_id] = {
        "id": export_id,
        "tenant_id": tenant_id,
        "requested_by": user_id,
        "status": "queued",
        "path": None,
    }
    return export_id


def finish_export(store, export_id, data):
    """Called by the background job when the file is ready."""
    path = "exports/%s.csv" % export_id
    store.files[path] = data
    store.exports[export_id].update(status="done", path=path)


def download_export(store, user_id, export_id):
    """Return the CSV bytes of a finished export (EXP-7)."""
    export = store.exports.get(export_id)
    if export is None or export["status"] != "done":
        raise NotFound(export_id)
    return store.files[export["path"]]
