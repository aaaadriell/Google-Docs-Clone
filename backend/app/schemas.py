# Solely for input / output validation
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime

#######################################################################################################################
# Sign-up Request / Response Schema
#######################################################################################################################
class SignUpUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=70)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class SignUpUserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

#######################################################################################################################
# Login User Request / Response Schema
#######################################################################################################################
class LoginUserRequest(BaseModel):
    emailOrUsername : str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=70)

class LoginUserResponse(BaseModel):
    id: int
    emailOrUsername : str
    jwtToken: str
    refreshToken: str

    class Config:
        from_attributes = True
