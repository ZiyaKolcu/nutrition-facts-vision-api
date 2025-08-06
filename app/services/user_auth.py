"""User authentication service for Firebase token verification."""

from firebase_admin import auth
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.firebase_auth import verify_firebase_token
from dotenv import load_dotenv

load_dotenv()


def authenticate_user(db: Session, id_token: str) -> User:
    """
    Authenticates a user using Firebase ID token and returns the user from database.
    If user doesn't exist, creates a new user record.

    Args:
        db (Session): Database session
        id_token (str): Firebase ID token from client

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: If token verification fails
    """
    print(f"Starting authentication for token: {id_token[:20]}...")

    try:
        print("Verifying Firebase token...")
        firebase_uid = verify_firebase_token(id_token)
        user_record = auth.get_user(firebase_uid)
        email = user_record.email

        user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

        if user:
            return user
        else:
            print("Creating new user in database...")
            user_data = UserCreate(firebase_uid=firebase_uid, email=email)
            new_user = User(firebase_uid=user_data.firebase_uid, email=user_data.email)

            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        ) from exc


def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> User:
    """
    Retrieves a user from database by Firebase UID.

    Args:
        db (Session): Database session
        firebase_uid (str): Firebase UID of the user

    Returns:
        User: The user object if found, None otherwise
    """
    return db.query(User).filter(User.firebase_uid == firebase_uid).first()
