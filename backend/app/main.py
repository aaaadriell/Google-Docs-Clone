from fastapi import FastAPI, HTTPException, status
from app.database import db_session
from app.schemas import UserRegister, UserResponse
from app.models import User
from app.helpers.password_hash import hash_password
from fastapi.middleware.cors import CORSMiddleware

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


@app.post("/sign-up", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(db: db_session, user_data: UserRegister):
    try:
        # Check email uniqueness
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken.")
        
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

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Sign-up failed: {str(e)}")


