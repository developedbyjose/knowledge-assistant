from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, hash_session_token, new_session_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate, UserRead, UserUpdate


class AuthenticationError(ValueError):
    pass


class AuthorizationError(ValueError):
    pass


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def authenticate(self, *, email: str, password: str) -> User:
        user = self.users.get_by_email(normalize_email(email))
        if user is None or not user.is_active or not verify_password(user.password_hash, password):
            raise AuthenticationError("Invalid email or password.")
        user.last_login_at = datetime.now(timezone.utc)
        return user

    def create_session(self, user: User) -> str:
        token = new_session_token()
        self.users.delete_expired_sessions()
        self.users.create_session(
            user_id=user.id,
            token_hash=hash_session_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.session_lifetime_days),
        )
        self.session.commit()
        return token

    def current_user(self, token: str) -> User | None:
        token_hash = hash_session_token(token)
        auth_session = self.users.get_session(token_hash)
        if auth_session is None:
            return None
        expires_at = auth_session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            self.session.delete(auth_session)
            self.session.commit()
            return None
        user = auth_session.user
        if not user.is_active:
            self.users.revoke_user_sessions(user.id)
            self.session.commit()
            return None
        return user

    def logout(self, token: str) -> None:
        self.users.revoke_session(hash_session_token(token))
        self.session.commit()

    def change_password(self, *, user: User, current_password: str, new_password: str) -> str:
        if not verify_password(user.password_hash, current_password):
            raise AuthenticationError("Current password is incorrect.")
        if verify_password(user.password_hash, new_password):
            raise ValueError("New password must be different from the current password.")
        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        self.users.revoke_user_sessions(user.id)
        token = new_session_token()
        self.users.create_session(
            user_id=user.id,
            token_hash=hash_session_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.session_lifetime_days),
        )
        self.session.commit()
        return token

    def list_users(self) -> list[UserRead]:
        return [UserRead.model_validate(user) for user in self.users.list()]

    def get_user(self, user_id: UUID) -> UserRead:
        return UserRead.model_validate(self._get_required(user_id))

    def create_user(self, payload: UserCreate) -> UserRead:
        try:
            user = self.users.create(
                email=normalize_email(payload.email),
                display_name=payload.display_name.strip(),
                password_hash=hash_password(payload.temporary_password),
                role=payload.role,
                is_active=True,
                must_change_password=True,
            )
            self.session.commit()
            self.session.refresh(user)
        except IntegrityError as exc:
            self.session.rollback()
            raise ValueError("A user with this email already exists.") from exc
        return UserRead.model_validate(user)

    def update_user(self, *, actor: User, user_id: UUID, payload: UserUpdate) -> UserRead:
        user = self._get_required(user_id)
        values = payload.model_dump(exclude_unset=True)
        if not values:
            raise ValueError("Update payload cannot be empty.")
        if any(value is None for value in values.values()):
            raise ValueError("User update fields cannot be null.")
        if actor.id == user.id and (
            values.get("is_active") is False
            or ("role" in values and values["role"] != "superadmin")
        ):
            raise ValueError("You cannot deactivate or demote your own superadmin account.")
        if user.role == "superadmin" and user.is_active and (
            values.get("is_active") is False
            or ("role" in values and values["role"] != "superadmin")
        ) and self.users.count_active_superadmins() <= 1:
            raise ValueError("At least one active superadmin is required.")
        if "display_name" in values:
            user.display_name = values["display_name"].strip()
        if "role" in values:
            user.role = values["role"]
        if "is_active" in values:
            user.is_active = values["is_active"]
        if values.get("is_active") is False:
            self.users.revoke_user_sessions(user.id)
        self.session.commit()
        self.session.refresh(user)
        return UserRead.model_validate(user)

    def reset_password(self, *, user_id: UUID, temporary_password: str) -> UserRead:
        user = self._get_required(user_id)
        user.password_hash = hash_password(temporary_password)
        user.must_change_password = True
        self.users.revoke_user_sessions(user.id)
        self.session.commit()
        self.session.refresh(user)
        return UserRead.model_validate(user)

    def _get_required(self, user_id: UUID) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise LookupError("User not found.")
        return user


def normalize_email(email: str) -> str:
    return email.strip().lower()
