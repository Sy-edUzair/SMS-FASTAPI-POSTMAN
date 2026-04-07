# 🎓 Student Management API

A production-style **FastAPI** backend for managing student records, built as a learning
project covering **Phase 1.2 & Phase 2** concepts from the Tezeract AI Internship curriculum.

---

## Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Framework    | **FastAPI** (async, Pydantic v2)    |
| Database     | **MongoDB** via Motor (async driver)|
| Cloud Storage| **Cloudinary** (photo upload)       |
| Validation   | **Pydantic** models                 |
| Server       | **Uvicorn** (ASGI)                  |

---

## Project Structure

```
student_management/
├── main.py                    # App entry point, lifespan hooks
├── requirements.txt
├── .env.example               # Copy to .env and fill in credentials
│
├── routers/
│   └── students.py            # All CRUD + photo endpoints
│
├── models/
│   └── student.py             # Pydantic request / response models
│
├── database/
│   └── mongodb.py             # Motor async client, indexes, lifecycle
│
└── utils/
    ├── cloudinary_utils.py    # Upload / delete Cloudinary photos
    └── db_helpers.py          # ObjectId conversion, timestamps
```

---

## Setup

### 1. Clone & install
```bash
cd student_management
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your credentials:
#   CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
#   MONGODB_URL  (e.g. mongodb://localhost:27017 or Atlas connection string)
```

### 3. Run
```bash
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## API Endpoints

### Students — `/api/v1/students`

| Method   | Path                            | Description                             |
|----------|---------------------------------|-----------------------------------------|
| `POST`   | `/`                             | Create a new student                    |
| `GET`    | `/`                             | List students (pagination + filters)    |
| `GET`    | `/{id}`                         | Get a single student                    |
| `PUT`    | `/{id}`                         | Update student fields (partial OK)      |
| `DELETE` | `/{id}`                         | Delete student + Cloudinary photo       |
| `POST`   | `/{id}/photo`                   | Upload / replace profile photo          |
| `DELETE` | `/{id}/photo`                   | Remove profile photo only               |
| `GET`    | `/department/{dept}`            | Filter students by department           |
| `GET`    | `/stats/summary`                | Aggregate stats (avg GPA, counts, etc.) |

### Query Parameters for `GET /`

| Param         | Type    | Description                   |
|---------------|---------|-------------------------------|
| `page`        | int     | Page number (default: 1)      |
| `per_page`    | int     | Results per page (default: 10)|
| `department`  | string  | Partial match                 |
| `grade_level` | string  | freshman / sophomore / ...    |
| `min_gpa`     | float   | Minimum GPA filter            |
| `search`      | string  | Name, email, or roll number   |

---

## Example Requests (Postman / curl)

### Create a student
```bash
curl -X POST http://localhost:8000/api/v1/students/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ali Hassan",
    "email": "ali@uni.edu",
    "roll_number": "CS-2024-001",
    "department": "Computer Science",
    "grade_level": "junior",
    "gpa": 3.7,
    "phone": "+92-300-1234567"
  }'
```

### Upload a photo
```bash
curl -X POST http://localhost:8000/api/v1/students/<id>/photo \
  -F "photo=@/path/to/photo.jpg"
```

### List with filters
```bash
curl "http://localhost:8000/api/v1/students/?department=CS&min_gpa=3.5&page=1&per_page=5"
```

### Get stats
```bash
curl http://localhost:8000/api/v1/students/stats/summary
```

---

## Concepts Covered (from Curriculum)

### Phase 1.2 — Advanced Python
- ✅ **Async I/O** — Motor (async MongoDB), async FastAPI endpoints
- ✅ **Cloud Storage** — Cloudinary upload/delete with public URLs
- ✅ **MongoDB** — `pymongo` / `motor`, CRUD, indexes, aggregation pipelines

### Phase 2 — Backend Core
- ✅ **FastAPI** — Routers, Pydantic models, dependency injection pattern
- ✅ **REST principles** — GET / POST / PUT / DELETE with proper status codes
- ✅ **Async endpoints** — `async def` throughout
- ✅ **Background-ready** — `lifespan` context manager for startup/shutdown hooks
- ✅ **File handling** — `UploadFile`, type validation, size limits, Cloudinary streaming
- ✅ **Database integration** — async MongoDB client in FastAPI lifecycle

---

## Cloudinary Setup

1. Sign up at https://cloudinary.com (free tier is sufficient)
2. Go to Dashboard → copy **Cloud Name**, **API Key**, **API Secret**
3. Paste them into your `.env`

Photos are stored under `student_management/students/<student_id>/profile`
with automatic 400×400 face-crop transformation applied.