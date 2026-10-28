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
from sqlalchemy.orm import Session
from app.models import RefreshToken
from datetime import datetime, timedelta, timezone

from app.exceptions import InvalidRefreshTokenError


# Declare Secret Key, Algorithm and Expiration Time
SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY")
ALGORITHM = "HS256"
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Fail fast at startup instead of on the first login / refresh
if not SECRET_KEY:
    raise RuntimeError("REFRESH_SECRET_KEY environment variable is not set.")

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