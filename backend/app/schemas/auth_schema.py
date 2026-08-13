"""
GovGuide AI — Authentication Schemas
"""

from pydantic import BaseModel, field_validator
from datetime import datetime
from app.security.input_validator import validate_email, validate_password_strength


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v):
        return validate_email(v)


class RegisterRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v):
        return validate_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        validate_password_strength(v)
        return v


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserProfile(BaseModel):
    user_id: str
    email: str
    role: str
    created_at: datetime
