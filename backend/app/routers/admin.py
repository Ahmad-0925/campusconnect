from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from collections import Counter
from ..models import ComplaintOut, StatusUpdateIn
from ..config import DEPARTMENTS, STATUSES
from ..deps import require_role
from .. import db

router = APIRouter(prefix="/admin", tags=["admin"])

def _scope(user: dict) -> Optional[str]:
    return None if user["role"] == "super_admin" else user.get("department")

@router.get("/complaints", response_model=List[ComplaintOut])
def list_complaints(
    status: Optional[str] = None,
    department: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    user: dict = Depends(require_role("dept_admin", "super_admin")),
):
    f = {"order": "created_at.desc"}
    scope = _scope(user)
    if scope:                                  # dept admin is locked to own dept
        f["department"] = f"eq.{scope}"
    elif department:
        f["department"] = f"eq.{department}"
    if status:
        f["status"] = f"eq.{status}"
    if category:
        f["category"] = f"eq.{category}"
    if q:
        f["or"] = f"(title.ilike.*{q}*,description.ilike.*{q}*)"
    return db.select("complaints", **f)

@router.patch("/complaints/{cid}", response_model=ComplaintOut)
def update_status(cid: str, body: StatusUpdateIn,
                  user: dict = Depends(require_role("dept_admin", "super_admin"))):
    rows = db.select("complaints", id=f"eq.{cid}")
    if not rows:
        raise HTTPException(404, "Complaint not found")
    scope = _scope(user)
    if scope and rows[0]["department"] != scope:
        raise HTTPException(403, "This complaint belongs to another department")
    if body.status in ("resolved", "rejected") and not body.remarks:
        raise HTTPException(400, "Remarks are required to resolve or reject")
    return db.update("complaints", cid, {
        "status": body.status,
        "remarks": body.remarks,
        "updated_at": "now()",
    })

@router.get("/stats")
def stats(user: dict = Depends(require_role("dept_admin", "super_admin"))):
    scope = _scope(user)
    f = {}
    if scope:
        f["department"] = f"eq.{scope}"
    rows = db.select("complaints", **f)
    by_status = Counter(r["status"] for r in rows)
    by_dept = Counter(r["department"] for r in rows)
    by_cat = Counter(r["category"] for r in rows)
    return {
        "scope": scope or "All Departments",
        "total": len(rows),
        "by_status": {s: by_status.get(s, 0) for s in STATUSES},
        "by_department": {d: by_dept.get(d, 0) for d in DEPARTMENTS},
        "by_category": dict(by_cat),
    }