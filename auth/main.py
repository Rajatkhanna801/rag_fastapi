from datetime import datetime, timedelta
from typing import Optional, Union, Any, Tuple
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from config import settings
from models.user_models import User, TokenBlacklist


ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """Get the current user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


def create_tokens(user_id: int) -> Tuple[str, str]:
    """Create access and refresh tokens for a user."""
    # Create access token with shorter expiry
    access_expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_payload = {
        "exp": access_expire, 
        "sub": str(user_id),
        "token_type": ACCESS_TOKEN_TYPE
    }
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
    
    # Create refresh token with longer expiry
    refresh_expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
    refresh_payload = {
        "exp": refresh_expire, 
        "sub": str(user_id),
        "token_type": REFRESH_TOKEN_TYPE
    }
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256")
    return access_token, refresh_token


def blacklist_token(db: Session, token: str, user_id: int) -> TokenBlacklist:
    """Add a token to the blacklist."""
    db_token = TokenBlacklist(token=token, user_id=user_id)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def decode_token(token: str) -> dict:
    """Decode a JWT token and return its payload."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        
def validate_refresh_token(db: Session, refresh_token: str) -> Optional[User]:
    """Validate a refresh token and return the associated user."""
    try:
        # Check if token is blacklisted
        blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token == refresh_token).first()
        if blacklisted:
            return None
            
        # Decode the token
        payload = decode_token(refresh_token)
        # Verify it's a refresh token
        if payload.get("token_type") != REFRESH_TOKEN_TYPE:
            return None
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        # Get the user
        user = db.query(User).filter(
            User.id == int(user_id),
            User.is_active == True,
            User.is_deleted == False
        ).first()
        
        return user
    except JWTError:
        return None