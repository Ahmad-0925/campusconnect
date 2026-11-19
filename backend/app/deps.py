from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .security import decode_token

bearer = HTTPBearer(auto_error=True)

def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        return decode_token(cred.credentials)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

def require_role(*roles: str):
    def _check(user: dict = Depends(current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted for your role")
        return user
    return _check