from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.security import get_password_hash
from models.user import User
from schemas.user import UserCreate


def normalize_email(email: str) -> str:
    """Normalize an email address for consistent case-insensitive lookups."""
    return email.strip().lower()


def get_user_by_email(db: Session, email: str):
    """Retrieve a user by their normalized email address."""
    normalized = normalize_email(email)
    return db.query(User).filter(User.email == normalized).first()


def create_user(db: Session, user: UserCreate):
    """Create a new user in the database with a hashed password."""
    hashed_password = get_password_hash(user.password)

    db_user = User(
        email=normalize_email(str(user.email)),
        full_name=user.full_name,
        hashed_password=hashed_password,
    )

    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_user)
    return db_user
