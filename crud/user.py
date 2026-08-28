from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate
from core.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    """Retrieve a user by their email address."""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    """Create a new user in the database with a hashed password."""
    hashed_password = get_password_hash(user.password)
    
    # Create a SQLAlchemy model instance
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    
    # Add to the session and commit to the database
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Get the newly generated ID
    return db_user
