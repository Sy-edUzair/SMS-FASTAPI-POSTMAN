"""Endpoints:
POST   /students/                   → create student
GET    /students/                   → list all (with pagination & filters)
GET    /students/{id}               → get one
PUT    /students/{id}               → update student fields
DELETE /students/{id}               → delete student + Cloudinary photo
POST   /students/{id}/photo         → upload / replace profile photo
DELETE /students/{id}/photo         → remove profile photo only
GET    /students/department/{dept}  → filter by department
"""

import logging

from bson import ObjectId
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from database.mongodb import get_students_collection
from models.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListResponse,
    MessageResponse,
)
from utils.cloudinary import upload_student_photo, delete_student_photo
from utils.db_helpers import doc_to_student, now_utc, is_valid_object_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/students", tags=["Students"])


def require_valid_id(student_id: str) -> ObjectId:
    if not is_valid_object_id(student_id):
        raise HTTPException(status_code=400, detail="Invalid student ID format.")
    return ObjectId(student_id)


async def get_or_404(student_id: str) -> dict:
    oid = require_valid_id(student_id)
    col = get_students_collection()
    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(
            status_code=404, detail=f"Student '{student_id}' not found."
        )
    return doc


@router.post(
    "/",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new student",
)
async def create_student(payload: StudentCreate):
    col = get_students_collection()
    ts = now_utc()

    existing = await col.find_one(
        {"$or": [{"email": payload.email}, {"roll_number": payload.roll_number}]}
    )
    if existing:
        duplicate_field = (
            "email" if existing.get("email") == payload.email else "roll_number"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A student with this {duplicate_field} already exists.",
        )

    document = {
        **payload.model_dump(),
        "photo_url": None,
        "photo_public_id": None,
        "created_at": ts,
        "updated_at": ts,
    }

    try:
        result = await col.insert_one(document)
    except DuplicateKeyError as exc:
        field = "email" if "email" in str(exc) else "roll_number"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A student with this {field} already exists.",
        )

    created = await col.find_one({"_id": result.inserted_id})
    logger.info(f"Student created: {result.inserted_id}")
    return doc_to_student(created)


@router.get(
    "/",
    response_model=StudentListResponse,
    summary="List all students",
)
async def list_students(
    page: int = 1,
    per_page: int = 10,
    department: str = None,
    grade_level: str = None,
    min_gpa: float = None,
    search: str = None,
):
    col = get_students_collection()
    query: dict = {}

    if department:
        query["department"] = {"$regex": department, "$options": "i"}
    if grade_level:
        query["grade_level"] = grade_level
    if min_gpa is not None:
        query["gpa"] = {"$gte": min_gpa}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"roll_number": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    skip = (page - 1) * per_page
    total = await col.count_documents(query)
    docs = (
        await col.find(query)
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(per_page)
        .to_list(per_page)
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "students": [doc_to_student(d) for d in docs],
    }


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    summary="Get a student by ID",
)
async def get_student(student_id: str):
    doc = await get_or_404(student_id)
    return doc_to_student(doc)


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    summary="Update student fields (partial update supported)",
)
async def update_student(student_id: str, payload: StudentUpdate):
    oid = require_valid_id(student_id)
    col = get_students_collection()
    changes = payload.model_dump(exclude_none=True)

    if not changes:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    changes["updated_at"] = now_utc()

    try:
        result = await col.update_one({"_id": oid}, {"$set": changes})
    except DuplicateKeyError as exc:
        field = "email" if "email" in str(exc) else "roll_number"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A student with this {field} already exists.",
        )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404, detail=f"Student '{student_id}' not found."
        )

    updated = await col.find_one({"_id": oid})
    logger.info(f"Student updated: {student_id}")
    return doc_to_student(updated)


@router.delete(
    "/{student_id}",
    response_model=MessageResponse,
    summary="Delete a student (also removes Cloudinary photo)",
)
async def delete_student(student_id: str):
    doc = await get_or_404(student_id)
    col = get_students_collection()
    oid = ObjectId(student_id)

    if doc.get("photo_public_id"):
        await delete_student_photo(doc["photo_public_id"])

    await col.delete_one({"_id": oid})
    logger.info(f"Student deleted: {student_id}")
    return {
        "message": f"Student '{doc['name']}' deleted successfully.",
        "student_id": student_id,
    }


@router.post(
    "/{student_id}/photo",
    response_model=StudentResponse,
    summary="Upload or replace the student's profile photo (Cloudinary)",
)
async def upload_photo(
    student_id: str,
    photo: UploadFile = File(...),
):
    doc = await get_or_404(student_id)
    col = get_students_collection()
    oid = ObjectId(student_id)

    cloud_data = await upload_student_photo(
        file=photo,
        student_id=student_id,
        old_public_id=doc.get("photo_public_id"),
    )

    ts = now_utc()
    await col.update_one(
        {"_id": oid},
        {
            "$set": {
                "photo_url": cloud_data["url"],
                "photo_public_id": cloud_data["public_id"],
                "updated_at": ts,
            }
        },
    )

    updated = await col.find_one({"_id": oid})
    logger.info(f"Photo uploaded for student {student_id}: {cloud_data['public_id']}")
    return doc_to_student(updated)


@router.delete(
    "/{student_id}/photo",
    response_model=MessageResponse,
    summary="Remove profile photo from Cloudinary without deleting student",
)
async def delete_photo(student_id: str):
    doc = await get_or_404(student_id)
    col = get_students_collection()
    oid = ObjectId(student_id)

    if not doc.get("photo_public_id"):
        raise HTTPException(
            status_code=404, detail="This student has no profile photo."
        )

    await delete_student_photo(doc["photo_public_id"])
    await col.update_one(
        {"_id": oid},
        {"$set": {"photo_url": None, "photo_public_id": None, "updated_at": now_utc()}},
    )

    return {"message": "Profile photo removed.", "student_id": student_id}


@router.get(
    "/department/{department}",
    response_model=StudentListResponse,
    summary="Get all students in a specific department",
)
async def students_by_department(
    department: str,
    page: int = 1,
    per_page: int = 10,
):
    col = get_students_collection()
    query = {"department": {"$regex": department, "$options": "i"}}
    skip = (page - 1) * per_page
    total = await col.count_documents(query)
    docs = (
        await col.find(query)
        .sort("name", 1)
        .skip(skip)
        .limit(per_page)
        .to_list(per_page)
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "students": [doc_to_student(d) for d in docs],
    }
