from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer
from sqlalchemy.orm import Session
from typing import Any
from datetime import datetime

from database import get_db
from models.user_models import User
from models.roles_permission import Role
from auth.schema import UserSignup, UserLogin, Token, ChangePassword, RefreshToken
from auth.main import (
    get_password_hash, 
    authenticate_user, 
    create_tokens, 
    get_current_active_user,
    verify_password,
    blacklist_token,
    validate_refresh_token
)


router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    *,
    db: Session = Depends(get_db),
    user_in: UserSignup,
) -> Any:
    """Register a new user with the default 'user' role."""
    
    # Check if email already exists
    user_by_email = db.query(User).filter(User.email == user_in.email).first()
    if user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Fetch the 'user' role
    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default 'user' role not found. Please initialize roles.",
        )
    # Create new user
    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        bio=user_in.bio,
        role_id=user_role.id  # Assign the 'user' role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User created successfully", "user_id": db_user.id, "role": user_role.name}



@router.post("/login", response_model=Token)
def login(
    *,
    db: Session = Depends(get_db),
    login_data: UserLogin,
) -> Any:
    """Login to get access and refresh tokens."""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token, refresh_token = create_tokens(user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    *,
    db: Session = Depends(get_db),
    password_data: ChangePassword,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Change user password."""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/logout")
def logout(
    token: str = Depends(security),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Logout by blacklisting the current token."""
    blacklist_token(db, token.credentials, current_user.id)
    return {"message": "Successfully logged out"}


@router.post("/refresh-token", response_model=Token)
def refresh_token(
    *,
    db: Session = Depends(get_db),
    token_data: RefreshToken,
) -> Any:
    """Generate new access and refresh tokens using a refresh token."""
    user = validate_refresh_token(db, token_data.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Blacklist the old refresh token
    blacklist_token(db, token_data.refresh_token, user.id)
    # Create new tokens
    access_token, refresh_token = create_tokens(user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
