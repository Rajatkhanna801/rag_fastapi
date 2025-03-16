from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from models.user_models import User
from user_management.schema import UserUpdate


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def update_user_profile(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
    """Update a user's profile."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_data.dict(exclude_unset=True)
    
    # Update user fields
    for field, value in update_data.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)
    
    # Set updated_at timestamp
    db_user.updated_at = datetime.utcnow()    
    db.commit()
    db.refresh(db_user)
    return db_user


def soft_delete_user(db: Session, user_id: int) -> Optional[User]:
    """Soft delete a user."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    # Set deletion fields
    db_user.is_deleted = True
    db_user.deleted_at = datetime.utcnow()
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user