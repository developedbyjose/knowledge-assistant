from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth_session import AuthSession
from app.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[User]:
        return list(self.session.scalars(select(User).order_by(User.created_at.desc())))

    def get(self, user_id: UUID) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalars(select(User).where(User.email == email)).one_or_none()

    def create(self, **values) -> User:  # noqa: ANN003
        user = User(**values)
        self.session.add(user)
        self.session.flush()
        return user

    def count_active_superadmins(self) -> int:
        statement = select(User).where(User.role == "superadmin", User.is_active.is_(True))
        return len(list(self.session.scalars(statement)))

    def delete_expired_sessions(self) -> None:
        expired = self.session.scalars(
            select(AuthSession).where(AuthSession.expires_at <= datetime.now(timezone.utc))
        )
        for session in expired:
            self.session.delete(session)

    def get_session(self, token_hash: str) -> AuthSession | None:
        return self.session.scalars(
            select(AuthSession).where(AuthSession.token_hash == token_hash)
        ).one_or_none()

    def create_session(self, *, user_id: UUID, token_hash: str, expires_at: datetime) -> AuthSession:
        auth_session = AuthSession(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.session.add(auth_session)
        self.session.flush()
        return auth_session

    def revoke_session(self, token_hash: str) -> None:
        auth_session = self.get_session(token_hash)
        if auth_session is not None:
            self.session.delete(auth_session)

    def revoke_user_sessions(self, user_id: UUID) -> None:
        sessions = self.session.scalars(select(AuthSession).where(AuthSession.user_id == user_id))
        for auth_session in sessions:
            self.session.delete(auth_session)
