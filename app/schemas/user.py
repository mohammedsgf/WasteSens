"""
Pydantic schemas for user authentication requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class SignUpRequest(BaseModel):
    """Schema for user registration"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=6, max_length=128)


class SignInRequest(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
