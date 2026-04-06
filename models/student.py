from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class GradeLevel(str, Enum):
    FRESHMAN = "freshman"
    SOPHOMORE = "sophomore"
    JUNIOR = "junior"
    SENIOR = "senior"
    GRADUATE = "graduate"


class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    roll_number: str
    department: str
    grade_level: GradeLevel
    gpa: float
    phone: Optional[str] = Field(None, example="+92-300-1234567")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip().title()

    @field_validator("roll_number")
    @classmethod
    def roll_number_uppercase(cls, v: str) -> str:
        return v.strip().upper()


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    grade_level: Optional[GradeLevel] = None
    gpa: Optional[float] = None
    phone: Optional[str] = Field(None, example="+92-300-1234567")


class StudentResponse(BaseModel):
    id: str
    name: str
    email: str
    roll_number: str
    department: str
    grade_level: GradeLevel
    gpa: float
    phone: Optional[str]
    photo_url: Optional[str] = None
    photo_public_id: Optional[str] = None


class StudentListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    students: list[StudentResponse]


class MessageResponse(BaseModel):
    message: str
    student_id: Optional[str] = None
