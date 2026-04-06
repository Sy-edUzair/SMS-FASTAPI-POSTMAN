import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger(__name__)
_client = None


def _get_required_env(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    joined = " or ".join(keys)
    raise RuntimeError(f"Missing required environment variable: {joined}")


def get_client():
    global _client
    if _client is None:
        url = _get_required_env("MONGODB_URL")
        _client = AsyncIOMotorClient(url)
    return _client


def get_database():
    db_name = _get_required_env("MONGODB_DB_NAME", "MONGO_DB_NAME")
    return get_client()[db_name]


def get_students_collection():
    return get_database()["students"]


async def connect_db() -> None:
    try:
        client = get_client()
        await client.admin.command("ping")
        logger.info("MongoDB connected successfully.")

        col = get_students_collection()
        indexes = [
            ([("email", ASCENDING)], {"unique": True, "name": "email_unique_idx"}),
            (
                [("roll_number", ASCENDING)],
                {"unique": True, "name": "roll_number_unique_idx"},
            ),
            ([("department", ASCENDING)], {"name": "department_idx"}),
            ([("grade_level", ASCENDING)], {"name": "grade_level_idx"}),
            ([("gpa", DESCENDING)], {"name": "gpa_idx"}),
            ([("created_at", DESCENDING)], {"name": "created_at_idx"}),
        ]

        for keys, options in indexes:
            try:
                await col.create_index(keys, **options)
            except DuplicateKeyError as exc:
                logger.warning(
                    "Skipped index '%s': existing duplicate data must be cleaned first (%s)",
                    options.get("name", "unnamed_index"),
                    exc,
                )

        logger.info("MongoDB indexes ensured.")
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise


async def disconnect_db() -> None:
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("MongoDB client closed.")
