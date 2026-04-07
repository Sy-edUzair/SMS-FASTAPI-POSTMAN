import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from database.mongodb import connect_db, disconnect_db
from utils.cloudinary import configure_cloudinary
from routers import students_api

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Student Management API...")
    configure_cloudinary()
    await connect_db()
    yield
    logger.info("Shutting down...")
    await disconnect_db()


app = FastAPI(
    title="Student Management API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(students_api.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Student Management API is running 🎓"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
