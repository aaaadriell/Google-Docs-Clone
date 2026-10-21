# JWT Tokens are short-lived tokens that are used for authentication and authorization purposes. 
# They are typically used to verify the identity of a user and grant access to protected resources. 
# However, since they have a short expiration time, they need to be refreshed periodically (via interaction with Refresh Tokens)t
# to maintain the user's session.
# JWT Tokens will be stored in the frontend in memory (e.g., in a variable or state management library) and will be sent in the Authorization header of each request to protected endpoints.

# JWT is split into three parts: 
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
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_jwt_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()), # Unique identifier for the token
        "refresh" : False # Flag for non-Refresh Token
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)