from bson import ObjectId
from datetime import datetime, timezone


def object_id_str(oid):
    return str(oid)


def doc_to_student(doc):
    doc["id"] = str(doc.pop("_id"))
    return doc


def now_utc():
    return datetime.now(timezone.utc)


def is_valid_object_id(value):
    try:
        ObjectId(value)
        return True
    except Exception:
        return False
