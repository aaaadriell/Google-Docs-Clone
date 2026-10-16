# JWT is split into three parts: 
# 1) Header
# 2) Payload
# 3) Signature
# The header and payload are base64 encoded, 
# while the signature is generated using a secret key. 
# The resulting token is a string that can be used for authentication and authorization purposes.

import jwt
import os
from datetime import datetime, timedelta, timezone


# Declare Secret Key, Algorithm and Expiration Time
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_jwt_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)