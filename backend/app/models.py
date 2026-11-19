from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    department: Optional[str] = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class ComplaintIn(BaseModel):
    category: str
    title: str = Field(min_length=4, max_length=120)
    description: str = Field(min_length=10, max_length=2000)
    image_url: Optional[str] = None

class ComplaintOut(BaseModel):
    id: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    category: str
    department: str
    title: str
    description: str
    image_url: Optional[str] = None
    status: str
    remarks: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class StatusUpdateIn(BaseModel):
    status: Literal["pending", "in_progress", "resolved", "rejected"]
    remarks: Optional[str] = Field(default=None, max_length=1000)