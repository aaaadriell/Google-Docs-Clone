# Refresh Tokens are long-lived tokens that are used to refresh JWT tokens. 
# They are typically used to maintain the user's session by providing a way to obtain new JWT tokens without requiring the user to re-authenticate.
# They will be stored in the frontend as an HttpOnly cookie, which is a type of cookie that is not accessible via JavaScript.

# Refresh Tokens are similar to JWT tokens, and are split into three parts: 
# 1) Header
# 2) Payload
# 3) Signature
# The header and payload are base64 encoded, 
# while the signature is generated using a secret key. 
# The resulting token is a string that can be used for authentication and authorization purposes.

import jwt
import uuid
import os
from fastapi import Response 
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.models import RefreshToken
from datetime import datetime, timedelta, timezone
from app.exceptions import InvalidRefreshTokenError


# Declare Secret Key, Algorithm and Expiration Time
SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY")
ALGORITHM = "HS256"
REFRESH_TOKEN_EXPIRE_DAYS = 7
REFRESH_REUSE_GRACE_SECONDS = 20

# Fail fast at startup instead of on the first login / refresh
if not SECRET_KEY:
    raise RuntimeError("REFRESH_SECRET_KEY environment variable is not set.")

###############################################################################
############# Refresh Token Related############################################
###############################################################################
def create_refresh_token(db: Session, user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())  # Unique identifier for the token
    payload = {
        "user_id": user_id,
        "jti": jti,  # Unique identifier for the token
        "iat": now,
        "exp": expire,
        "refresh" : True, # Flag for Refresh Token,
    }

    new_refresh_token = RefreshToken(jti = jti, user_id = user_id, created_at = now, expired_at = expire)
    
    db.add(new_refresh_token)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_refresh_token(token: str) -> dict:
    # Only jwt.decode can raise PyJWT errors, so it's the only thing inside the try
    try:
        # PyJWT automatically checks expiry here
        payload = jwt.decode(token,
                            SECRET_KEY,
                            algorithms=[ALGORITHM],
                            options={"require": ["user_id", "jti", "iat", "exp", "refresh"]})
    except jwt.InvalidTokenError as e:
        # Parent of ExpiredSignatureError, InvalidSignatureError, DecodeError, MissingRequiredClaimError, ...
        raise InvalidRefreshTokenError("Invalid refresh token.") from e

    if payload.get("refresh") is not True:
        raise InvalidRefreshTokenError("Not a refresh token.")
    
    return payload

def revoke_refresh_token_record(record : RefreshToken | None) -> None:
    record.isActive = False
    record.revoked_at = datetime.now(timezone.utc)

def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> None:
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.isActive.is_(True)).update({"isActive": False, "revoked_at": datetime.now(timezone.utc)}, synchronize_session=False)

def was_recently_revoked(record: RefreshToken | None, grace_seconds = REFRESH_REUSE_GRACE_SECONDS) -> bool:
    now = datetime.now(timezone.utc)
    return record.revoked_at is not None and ((now - record.revoked_at) <= grace_seconds )

def get_refresh_token_from_db(db: Session, jti: str, lock: bool = False) -> RefreshToken | None:
    query = db.query(RefreshToken).filter(RefreshToken.jti == jti)
    if lock:
        query = query.with_for_update()
    return query.first()

def delete_stale_refresh_tokens(db: Session, user_id: int | None = None)-> int:
    now = datetime.now(timezone.utc)
    query = db.query(RefreshToken).filter(RefreshToken.expired_at < now)
    if user_id is not None:
        query = query.filter(RefreshToken.user_id == user_id)

    return query.delete(synchronize_session=False)

###############################################################################
############# Cookie Related############################################
###############################################################################
def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(key="refresh_token",
                        value=refresh_token,
                        path="/",
                        httponly=True,
                        secure=True,
                        samesite="strict",
                        max_age=REFRESH_TOKEN_EXPIRE_DAYS*24*60*60
                        )

def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key="refresh_token", path="/",
                            httponly=True,
                            secure=True,
                            samesite="strict"
                            )


def unauthorized_and_clear_cookie() -> JSONResponse:
    errorResponse = JSONResponse(status_code=401, content = {"detail": "Invalid or expired session."})
    clear_refresh_cookie(errorResponse)
    return errorResponse