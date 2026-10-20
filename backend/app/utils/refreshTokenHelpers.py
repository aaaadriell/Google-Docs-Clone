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
from datetime import datetime, timedelta, timezone


# Declare Secret Key, Algorithm and Expiration Time
SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY")
ALGORITHM = "HS256"
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_refresh_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),  # Unique identifier for the token
        "refresh" : True # Flag for Refresh Token
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)