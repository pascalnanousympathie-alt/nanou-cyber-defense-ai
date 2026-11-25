"""Database-backed account, session, rate-limit and audit repositories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError

from nanou_cyber_ai.storage.database import (
    SecurityDatabase,
    audit_events,
    auth_attempts,
    platform_state,
    sessions,
    users,
)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def public_user(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"],
        "role": row["role"],
        "is_approved": bool(row["is_approved"]),
        "is_active": bool(row["is_active"]),
        "created_at": _as_utc(row["created_at"]).isoformat(),
    }


class AuthStore:
    def __init__(self, database: SecurityDatabase) -> None:
        self.database = database

    def user_count(self) -> int:
        with self.database.engine.connect() as connection:
            return int(connection.execute(select(func.count()).select_from(users)).scalar_one())

    def bootstrap_available(self) -> bool:
        with self.database.engine.connect() as connection:
            claimed = connection.execute(
                select(platform_state.c.bootstrap_claimed).where(platform_state.c.id == 1)
            ).scalar_one()
        return not bool(claimed) and self.user_count() == 0

    def _audit(
        self,
        connection,
        *,
        actor_user_id: str | None,
        action: str,
        target_type: str,
        target_id: str | None,
        outcome: str,
        request_id: str | None,
        ip_digest: str | None,
    ) -> None:
        connection.execute(
            insert(audit_events).values(
                id=uuid.uuid4().hex,
                actor_user_id=actor_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                outcome=outcome,
                request_id=request_id,
                ip_digest=ip_digest,
            )
        )

    def record_event(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        target_type: str = "platform",
        target_id: str | None = None,
        outcome: str = "success",
        request_id: str | None = None,
        ip_digest: str | None = None,
    ) -> None:
        with self.database.engine.begin() as connection:
            self._audit(
                connection,
                actor_user_id=actor_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                outcome=outcome,
                request_id=request_id,
                ip_digest=ip_digest,
            )

    def allow_attempt(
        self,
        fingerprint: str,
        *,
        maximum: int = 10,
        window_seconds: int = 900,
    ) -> bool:
        cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)
        with self.database.engine.begin() as connection:
            recent = connection.execute(
                select(func.count())
                .select_from(auth_attempts)
                .where(
                    auth_attempts.c.fingerprint == fingerprint,
                    auth_attempts.c.created_at >= cutoff,
                )
            ).scalar_one()
            if int(recent) >= maximum:
                return False
            connection.execute(
                insert(auth_attempts).values(
                    fingerprint=fingerprint,
                    created_at=datetime.now(UTC),
                )
            )
            # Keep the table bounded without a background worker.
            connection.execute(delete(auth_attempts).where(auth_attempts.c.created_at < cutoff))
        return True

    def create_bootstrap_admin(
        self,
        *,
        email: str,
        display_name: str,
        password_hash: str,
        request_id: str | None,
        ip_digest: str | None,
    ) -> dict[str, Any] | None:
        user_id = uuid.uuid4().hex
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            # The single state row serializes simultaneous first-admin attempts.
            claimed = connection.execute(
                update(platform_state)
                .where(platform_state.c.id == 1, platform_state.c.bootstrap_claimed.is_(False))
                .values(bootstrap_claimed=True)
            )
            if claimed.rowcount != 1:
                return None
            count = connection.execute(select(func.count()).select_from(users)).scalar_one()
            if int(count) != 0:
                return None
            connection.execute(
                insert(users).values(
                    id=user_id,
                    email=email,
                    display_name=display_name,
                    password_hash=password_hash,
                    role="admin",
                    is_approved=True,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            self._audit(
                connection,
                actor_user_id=user_id,
                action="auth.bootstrap",
                target_type="user",
                target_id=user_id,
                outcome="success",
                request_id=request_id,
                ip_digest=ip_digest,
            )
            row = connection.execute(select(users).where(users.c.id == user_id)).mappings().one()
        return public_user(row)

    def register(
        self,
        *,
        email: str,
        display_name: str,
        password_hash: str,
        request_id: str | None,
        ip_digest: str | None,
    ) -> dict[str, Any]:
        user_id = uuid.uuid4().hex
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            try:
                connection.execute(
                    insert(users).values(
                        id=user_id,
                        email=email,
                        display_name=display_name,
                        password_hash=password_hash,
                        role="viewer",
                        is_approved=False,
                        is_active=False,
                        created_at=now,
                        updated_at=now,
                    )
                )
            except IntegrityError as exc:
                raise ValueError("An account with this email already exists.") from exc
            self._audit(
                connection,
                actor_user_id=user_id,
                action="auth.register",
                target_type="user",
                target_id=user_id,
                outcome="pending",
                request_id=request_id,
                ip_digest=ip_digest,
            )
            row = connection.execute(select(users).where(users.c.id == user_id)).mappings().one()
        return public_user(row)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self.database.engine.connect() as connection:
            row = connection.execute(select(users).where(users.c.email == email)).mappings().first()
        if row is None:
            return None
        result = public_user(row)
        result["password_hash"] = row["password_hash"]
        return result

    def create_session(
        self,
        *,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            connection.execute(delete(sessions).where(sessions.c.expires_at <= now))
            connection.execute(
                insert(sessions).values(
                    token_hash=token_hash,
                    user_id=user_id,
                    created_at=now,
                    last_seen_at=now,
                    expires_at=expires_at,
                )
            )

    def get_user_for_session(self, token_hash: str) -> dict[str, Any] | None:
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            statement = (
                select(users)
                .select_from(sessions.join(users, sessions.c.user_id == users.c.id))
                .where(
                    sessions.c.token_hash == token_hash,
                    sessions.c.expires_at > now,
                    users.c.is_active.is_(True),
                    users.c.is_approved.is_(True),
                )
            )
            row = connection.execute(statement).mappings().first()
            if row is None:
                connection.execute(delete(sessions).where(sessions.c.token_hash == token_hash))
                return None
            connection.execute(
                update(sessions).where(sessions.c.token_hash == token_hash).values(last_seen_at=now)
            )
        return public_user(row)

    def revoke_session(self, token_hash: str) -> None:
        with self.database.engine.begin() as connection:
            connection.execute(delete(sessions).where(sessions.c.token_hash == token_hash))

    def list_users(self, limit: int = 200) -> list[dict[str, Any]]:
        with self.database.engine.connect() as connection:
            rows = connection.execute(
                select(users).order_by(users.c.created_at.desc()).limit(max(1, min(limit, 500)))
            ).mappings()
        return [public_user(row) for row in rows]

    def update_user(
        self,
        *,
        actor_user_id: str,
        target_user_id: str,
        role: str,
        is_active: bool,
        request_id: str | None,
        ip_digest: str | None,
    ) -> dict[str, Any] | None:
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            target = (
                connection.execute(select(users).where(users.c.id == target_user_id))
                .mappings()
                .first()
            )
            if target is None:
                return None
            if target_user_id == actor_user_id and (not is_active or role != "admin"):
                raise ValueError(
                    "The current administrator cannot demote or deactivate themselves."
                )
            if (
                target["role"] == "admin"
                and bool(target["is_active"])
                and (role != "admin" or not is_active)
            ):
                active_admins = connection.execute(
                    select(users.c.id)
                    .where(users.c.role == "admin", users.c.is_active.is_(True))
                    .with_for_update()
                ).all()
                if len(active_admins) <= 1:
                    raise ValueError("At least one active administrator must remain.")
            connection.execute(
                update(users)
                .where(users.c.id == target_user_id)
                .values(
                    role=role,
                    is_approved=True,
                    is_active=is_active,
                    updated_at=now,
                )
            )
            # Role/suspension changes invalidate every prior session immediately.
            connection.execute(delete(sessions).where(sessions.c.user_id == target_user_id))
            self._audit(
                connection,
                actor_user_id=actor_user_id,
                action="admin.user.update",
                target_type="user",
                target_id=target_user_id,
                outcome="success",
                request_id=request_id,
                ip_digest=ip_digest,
            )
            row = (
                connection.execute(select(users).where(users.c.id == target_user_id))
                .mappings()
                .one()
            )
        return public_user(row)

    def list_audit_events(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.database.engine.connect() as connection:
            rows = connection.execute(
                select(audit_events)
                .order_by(audit_events.c.created_at.desc())
                .limit(max(1, min(limit, 500)))
            ).mappings()
        return [
            {
                "id": row["id"],
                "actor_user_id": row["actor_user_id"],
                "action": row["action"],
                "target_type": row["target_type"],
                "target_id": row["target_id"],
                "outcome": row["outcome"],
                "request_id": row["request_id"],
                "created_at": _as_utc(row["created_at"]).isoformat(),
            }
            for row in rows
        ]
