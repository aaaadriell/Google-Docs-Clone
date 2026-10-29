#############################################################################
# The get_current_user is a dependency that can be used as a middleware 
# to protect routes, requiring authentication before allowing access
#############################################################################


from app.database import db_session
from app.models import User
from app.utils.jwtTokenHelpers import decode_jwt_token
from app.exceptions import ExpiredJWTTokenError, InvalidJWTTokenError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

# HTTPBearer reads the Authorization: Bearer <token> header and gives us the token string
bearer_scheme = HTTPBearer(auto_error=False)

# Takes in the JWT Access Token from Authorization header
# Decodes token
# If token is valid, retuns the User object from database
def get_current_user(db: db_session, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]) -> User:
    # JWT Access Token Check
    if not credentials:
        raise HTTPException(401, "Not Authenticated", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = decode_jwt_token(credentials.credentials)
    
    except ExpiredJWTTokenError:
        raise HTTPException(401, "JWT Access token has expired", headers={"WWW-Authenticate": "Bearer"})
    
    except InvalidJWTTokenError:
        raise HTTPException(401, "Invalid JWT Access token", headers={"WWW-Authenticate": "Bearer"})

    user = db.get(User, payload["user_id"])
    if not user:
        raise HTTPException(401, "User not found", headers={"WWW-Authenticate": "Bearer"})
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]