from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


DEFAULT_USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "password": "admin123",
        "role": "admin",
    },
    {
        "email": "agent@example.com",
        "username": "agent",
        "password": "agent123",
        "role": "agent",
    },
    {
        "email": "viewer@example.com",
        "username": "viewer",
        "password": "viewer123",
        "role": "viewer",
    },
]


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
            )
        return user

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.repository.get_by_id(user_id)

    def ensure_default_users(self) -> list[User]:
        created_or_existing: list[User] = []
        for user_data in DEFAULT_USERS:
            existing = self.repository.get_by_email(user_data["email"])
            if existing:
                created_or_existing.append(existing)
                continue

            created_or_existing.append(
                self.repository.create(
                    email=user_data["email"],
                    username=user_data["username"],
                    hashed_password=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                )
            )
        return created_or_existing
