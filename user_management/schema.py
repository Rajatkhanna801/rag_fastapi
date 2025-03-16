from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None


class UserUpdate(UserBase):
    # Email is removed from this model to prevent updates
    pass


# You may need this if returning role details
class RoleInfo(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    id: int
    email: EmailStr  # Email is included in response but not in update
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool
    role: Optional[RoleInfo] = None
    
    class Config:
        orm_mode = True
