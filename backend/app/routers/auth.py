from fastapi import APIRouter, HTTPException
from ..models import RegisterIn, LoginIn, TokenOut, UserOut
from ..security import hash_password, verify_password, make_token
from .. import db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn):
    if db.select("users", email=f"eq.{body.email}"):
        raise HTTPException(400, "Email already registered")
    user = db.insert("users", {
        "name": body.name,
        "email": body.email,
        "password_hash": hash_password(body.password),
        "role": "student",
    })
    return TokenOut(access_token=make_token(user), user=UserOut(**user))

@router.post("/login", response_model=TokenOut)
def login(body: LoginIn):
    rows = db.select("users", email=f"eq.{body.email}")
    if not rows or not verify_password(body.password, rows[0]["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    user = rows[0]
    return TokenOut(access_token=make_token(user), user=UserOut(**user))