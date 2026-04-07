import logging
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif"}
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def configure_cloudinary():
    cloudinary.config(
        secure=True,
    )
    logger.info("Cloudinary configured.")


def _validate_image(file: UploadFile):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. "
            f"Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )


async def upload_student_photo(file, student_id, old_public_id):
    _validate_image(file)

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE_MB} MB limit.",
        )
    # delete old photo if it exists
    if old_public_id:
        await delete_student_photo(old_public_id)

    public_id = f"students/{student_id}/profile"

    try:
        result = cloudinary.uploader.upload(
            contents,
            public_id=public_id,
            overwrite=True,
            unique_filename=False,
            resource_type="auto",
            folder="student_images",
            transformation=[
                {"width": 400, "height": 400, "crop": "fill", "gravity": "face"}
            ],
            eager=[{"width": 100, "height": 100, "crop": "thumb", "gravity": "face"}],
            eager_async=True,
            tags=["student", student_id],
        )
        logger.info(f"Photo uploaded for student {student_id}: {result['public_id']}")
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
        }
    except Exception as e:
        logger.error(f"Cloudinary upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Photo upload failed: {str(e)}",
        )


async def delete_student_photo(public_id):
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="auto")
        if result.get("result") == "ok":
            logger.info(f"Deleted Cloudinary asset: {public_id}")
            return True
        logger.warning(f"Cloudinary delete returned: {result}")
        return False
    except Exception as e:
        logger.error(f"Cloudinary delete error for {public_id}: {e}")
        return False
