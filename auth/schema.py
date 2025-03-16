from pydantic import BaseModel, EmailStr
from typing import Optional


class UserSignup(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    token_type: Optional[str] = None


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class RefreshToken(BaseModel):
    refresh_token: str