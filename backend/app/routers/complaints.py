from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models import ComplaintIn, ComplaintOut
from ..config import CATEGORY_MAP
from ..deps import current_user, require_role
from .. import db

router = APIRouter(prefix="/complaints", tags=["complaints"])

@router.get("/categories", response_model=List[str])
def categories():
    return list(CATEGORY_MAP.keys())

@router.post("", response_model=ComplaintOut)
def create(body: ComplaintIn, user: dict = Depends(require_role("student"))):
    dept = CATEGORY_MAP.get(body.category)
    if not dept:
        raise HTTPException(400, "Unknown category")
    row = db.insert("complaints", {
        "student_id": user["sub"],
        "student_name": user["name"],
        "category": body.category,
        "department": dept,          # automatic routing
        "title": body.title,
        "description": body.description,
        "image_url": body.image_url,
        "status": "pending",
    })
    return row

@router.get("/mine", response_model=List[ComplaintOut])
def mine(user: dict = Depends(require_role("student"))):
    return db.select("complaints", student_id=f"eq.{user['sub']}",
                     order="created_at.desc")

@router.get("/{cid}", response_model=ComplaintOut)
def one(cid: str, user: dict = Depends(current_user)):
    rows = db.select("complaints", id=f"eq.{cid}")
    if not rows:
        raise HTTPException(404, "Complaint not found")
    c = rows[0]
    role = user["role"]
    if role == "super_admin":
        return c
    if role == "dept_admin" and c["department"] == user.get("department"):
        return c
    if role == "student" and c["student_id"] == user["sub"]:
        return c
    raise HTTPException(403, "You are not allowed to access this complaint")