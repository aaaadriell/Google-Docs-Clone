from fastapi import FastAPI, HTTPException, status
from app.database import db_session
from app.schemas import SignUpUserRequest, SignUpUserResponse, LoginUserRequest, LoginUserResponse
from app.models import User
from app.utils.passwordHelpers import check_password, hash_password
from app.utils.jwtTokenHelpers import create_jwt_token
from fastapi.middleware.cors import CORSMiddleware

from backend.app.utils.refreshTokenHelpers import create_refresh_token

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health-check")
def connectivity_check(db: db_session):
    try:
        # Perform a simple query to check database connectivity
        return {"status": "Success", "message": "Successfully connected to Neon DB!."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@app.post("/sign-up", response_model=SignUpUserResponse, status_code=status.HTTP_201_CREATED)
def signup(db: db_session, user_data: SignUpUserRequest):
    try:
        # Check email uniqueness
        existing_user_via_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_user_via_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken.")

        # Check username uniqueness
        existing_user_via_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_user_via_username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken.")
        
        # Hash Password
        hashed_password = hash_password(user_data.password)

        # Create new user
        new_user = User(
            username = user_data.username,
            email = user_data.email,
            hashed_password = hashed_password,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except HTTPException:
        # Let intentional errors (like the 400 above) through unchanged
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Sign-up failed: {str(e)}")

@app.post("/login", response_model=LoginUserResponse, status_code=status.HTTP_200_OK)
def login(db: db_session, user_data: LoginUserRequest):
    try:
        # Email / Username Existence Check
        existing_user = db.query(User).filter((User.username == user_data.emailOrUsername) | (User.email == user_data.emailOrUsername)).first()
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

        # Password Verification
        if not check_password(user_data.password, existing_user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
        # Refresh Token Generation
        refresh_token = create_refresh_token(existing_user.id)

        # JWT Token Generation
        jwt_token = create_jwt_token(existing_user.id)

        return LoginUserResponse(
            id=existing_user.id,
            emailOrUsername=existing_user.username if existing_user.username == user_data.emailOrUsername else existing_user.email,
            jwtToken=jwt_token
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login failed: {str(e)}")
