"""HTTP handlers. Each takes the parsed session and request values."""

import itertools

from . import db

_ids = itertools.count(1)


class HttpError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def list_notes(session):
    return [n for n in db.NOTES.values() if n["tenant_id"] == session["tenant_id"]]


def create_note(session, title, body):
    note_id = "n%d" % next(_ids)
    db.NOTES[note_id] = {
        "id": note_id,
        "tenant_id": session["tenant_id"],
        "author_id": session["user_id"],
        "title": title,
        "body": body,
    }
    return db.NOTES[note_id]


def get_note(session, note_id):
    note = db.NOTES.get(note_id)
    if note is None:
        raise HttpError(404, "not found")
    return note


def delete_note(session, note_id):
    if session["role"] != "admin":
        raise HttpError(403, "admins only")
    note = db.NOTES.get(note_id)
    if note is None or note["tenant_id"] != session["tenant_id"]:
        raise HttpError(404, "not found")
    del db.NOTES[note_id]


def remove_member(session, user_id):
    if session["role"] != "admin":
        raise HttpError(403, "admins only")
    db.remove_member(session["tenant_id"], user_id)
