"""Database-backed account, session, rate-limit and audit repositories."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import case, delete, func, insert, inspect, or_, select, update
from sqlalchemy.exc import IntegrityError

from nanou_cyber_ai.storage.database import (
    SecurityDatabase,
    api_keys,
    audit_events,
    auth_attempts,
    google_identities,
    platform_state,
    sessions,
    users,
)

ADMIN_PAIRING_TTL_SECONDS = 90
ADMIN_BRIDGE_TTL_SECONDS = 15 * 60
_ADMIN_PAIRING_SCOPE = '["admin:bridge:pair"]'
_ADMIN_BRIDGE_SCOPE = '["admin:bridge:read"]'


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


def public_api_key(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "token_prefix": row["token_prefix"],
        "scopes": json.loads(row["scopes"]),
        "created_at": _as_utc(row["created_at"]).isoformat(),
        "expires_at": _as_utc(row["expires_at"]).isoformat(),
        "last_used_at": _as_utc(row["last_used_at"]).isoformat()
        if row["last_used_at"] is not None
        else None,
        "revoked_at": _as_utc(row["revoked_at"]).isoformat()
        if row["revoked_at"] is not None
        else None,
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

    def google_identity_storage_available(self) -> bool:
        schema = "public" if self.database.mode == "postgresql" else None
        return inspect(self.database.engine).has_table("google_identities", schema=schema)

    def get_user_by_google_subject(self, subject: str) -> dict[str, Any] | None:
        with self.database.engine.connect() as connection:
            row = connection.execute(
                select(users)
                .select_from(google_identities.join(users, google_identities.c.user_id == users.c.id))
                .where(google_identities.c.google_subject == subject)
            ).mappings().first()
        return public_user(row) if row is not None else None

    def has_google_identity(self, user_id: str) -> bool:
        with self.database.engine.connect() as connection:
            subject = connection.execute(
                select(google_identities.c.google_subject).where(
                    google_identities.c.user_id == user_id
                )
            ).first()
        return subject is not None

    def register_google(
        self,
        *,
        subject: str,
        email: str,
        display_name: str,
        password_hash: str,
        request_id: str | None,
        ip_digest: str | None,
    ) -> dict[str, Any]:
        user_id = uuid.uuid4().hex
        now = datetime.now(UTC)
        try:
            with self.database.engine.begin() as connection:
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
                connection.execute(
                    insert(google_identities).values(
                        google_subject=subject,
                        user_id=user_id,
                        email_at_link=email,
                        created_at=now,
                    )
                )
                self._audit(
                    connection,
                    actor_user_id=user_id,
                    action="auth.google_register",
                    target_type="user",
                    target_id=user_id,
                    outcome="pending",
                    request_id=request_id,
                    ip_digest=ip_digest,
                )
                row = connection.execute(
                    select(users).where(users.c.id == user_id)
                ).mappings().one()
        except IntegrityError as exc:
            raise ValueError(
                "The Google identity or email is already linked to an account."
            ) from exc
        return public_user(row)

    def link_google_identity(self, *, user_id: str, subject: str, email: str) -> None:
        try:
            with self.database.engine.begin() as connection:
                existing = connection.execute(
                    select(google_identities.c.user_id).where(
                        google_identities.c.google_subject == subject
                    )
                ).scalar_one_or_none()
                if existing is not None and existing != user_id:
                    raise ValueError("This Google account is already linked to another account.")
                linked = connection.execute(
                    select(google_identities.c.google_subject).where(
                        google_identities.c.user_id == user_id
                    )
                ).scalar_one_or_none()
                if linked is not None and linked != subject:
                    raise ValueError("A different Google account is already linked.")
                if existing == subject and linked == subject:
                    return
                connection.execute(
                    insert(google_identities).values(
                        google_subject=subject,
                        user_id=user_id,
                        email_at_link=email,
                    )
                )
        except IntegrityError as exc:
            raise ValueError("This Google identity is already linked.") from exc

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

    def change_password(
        self,
        *,
        user_id: str,
        password_hash: str,
        request_id: str | None,
        ip_digest: str | None,
    ) -> bool:
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            account = (
                connection.execute(
                    select(users)
                    .where(
                        users.c.id == user_id,
                        users.c.is_active.is_(True),
                        users.c.is_approved.is_(True),
                    )
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if account is None:
                return False
            connection.execute(
                update(users)
                .where(users.c.id == user_id)
                .values(password_hash=password_hash, updated_at=now)
            )
            # Password rotation invalidates all browser sessions and any short-lived
            # Admin bridge/pairing credentials; ordinary Developer API keys are separate.
            connection.execute(delete(sessions).where(sessions.c.user_id == user_id))
            connection.execute(
                update(api_keys)
                .where(
                    api_keys.c.owner_user_id == user_id,
                    api_keys.c.scopes.in_([_ADMIN_PAIRING_SCOPE, _ADMIN_BRIDGE_SCOPE]),
                    api_keys.c.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            self._audit(
                connection,
                actor_user_id=user_id,
                action="auth.password.change",
                target_type="user",
                target_id=user_id,
                outcome="success",
                request_id=request_id,
                ip_digest=ip_digest,
            )
        return True

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
            connection.execute(
                update(api_keys)
                .where(api_keys.c.owner_user_id == target_user_id, api_keys.c.revoked_at.is_(None))
                .values(revoked_at=now)
            )
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

    def create_api_key(
        self,
        *,
        owner_user_id: str,
        name: str,
        token_prefix: str,
        token_hash: str,
        scopes: list[str],
        expires_at: datetime,
        request_id: str | None,
        ip_digest: str | None,
    ) -> dict[str, Any]:
        key_id = uuid.uuid4().hex
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            active_count = connection.execute(
                select(func.count())
                .select_from(api_keys)
                .where(
                    api_keys.c.owner_user_id == owner_user_id,
                    api_keys.c.revoked_at.is_(None),
                    api_keys.c.expires_at > now,
                )
            ).scalar_one()
            if int(active_count) >= 10:
                raise ValueError("Each account can have at most 10 active API keys.")
            connection.execute(
                insert(api_keys).values(
                    id=key_id,
                    owner_user_id=owner_user_id,
                    name=name,
                    token_prefix=token_prefix,
                    token_hash=token_hash,
                    scopes=json.dumps(scopes, separators=(",", ":")),
                    created_at=now,
                    expires_at=expires_at,
                    request_count=0,
                )
            )
            self._audit(
                connection,
                actor_user_id=owner_user_id,
                action="developer.api_key.create",
                target_type="api-key",
                target_id=key_id,
                outcome="success",
                request_id=request_id,
                ip_digest=ip_digest,
            )
            row = (
                connection.execute(select(api_keys).where(api_keys.c.id == key_id)).mappings().one()
            )
        return public_api_key(row)

    def create_admin_pairing(
        self,
        *,
        owner_user_id: str,
        token_prefix: str,
        token_hash: str,
        request_id: str | None,
        ip_digest: str | None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ADMIN_PAIRING_TTL_SECONDS)
        key_id = uuid.uuid4().hex
        with self.database.engine.begin() as connection:
            owner = (
                connection.execute(
                    select(users).where(
                        users.c.id == owner_user_id,
                        users.c.role == "admin",
                        users.c.is_approved.is_(True),
                        users.c.is_active.is_(True),
                    )
                )
                .mappings()
                .first()
            )
            if owner is None:
                raise ValueError("An active approved administrator is required.")
            replaced = (
                connection.execute(
                    update(api_keys)
                    .where(
                        api_keys.c.owner_user_id == owner_user_id,
                        api_keys.c.scopes.in_([_ADMIN_PAIRING_SCOPE, _ADMIN_BRIDGE_SCOPE]),
                        api_keys.c.revoked_at.is_(None),
                    )
                    .values(revoked_at=now)
                    .returning(api_keys.c.id)
                )
                .scalars()
                .all()
            )
            for replaced_id in replaced:
                self._audit(
                    connection,
                    actor_user_id=owner_user_id,
                    action="auth.admin_bridge.replaced",
                    target_type="admin-bridge",
                    target_id=replaced_id,
                    outcome="revoked",
                    request_id=request_id,
                    ip_digest=ip_digest,
                )
            active_count = connection.execute(
                select(func.count())
                .select_from(api_keys)
                .where(
                    api_keys.c.owner_user_id == owner_user_id,
                    api_keys.c.revoked_at.is_(None),
                    api_keys.c.expires_at > now,
                )
            ).scalar_one()
            if int(active_count) >= 10:
                raise ValueError("Too many active API credentials; revoke an unused key first.")
            connection.execute(
                insert(api_keys).values(
                    id=key_id,
                    owner_user_id=owner_user_id,
                    name="Termux Admin pairing code",
                    token_prefix=token_prefix,
                    token_hash=token_hash,
                    scopes=_ADMIN_PAIRING_SCOPE,
                    created_at=now,
                    expires_at=expires_at,
                    request_count=0,
                )
            )
            self._audit(
                connection,
                actor_user_id=owner_user_id,
                action="auth.admin_bridge.pairing_created",
                target_type="admin-bridge",
                target_id=key_id,
                outcome="success",
                request_id=request_id,
                ip_digest=ip_digest,
            )
        return {"id": key_id, "expires_at": expires_at}

    def exchange_admin_pairing(
        self,
        *,
        pairing_token_hash: str,
        bridge_token_prefix: str,
        bridge_token_hash: str,
        request_id: str | None,
        ip_digest: str | None,
    ) -> dict[str, Any] | None:
        now = datetime.now(UTC)
        bridge_expires_at = now + timedelta(seconds=ADMIN_BRIDGE_TTL_SECONDS)
        bridge_key_id = uuid.uuid4().hex
        with self.database.engine.begin() as connection:
            consumed = (
                connection.execute(
                    update(api_keys)
                    .where(
                        api_keys.c.token_hash == pairing_token_hash,
                        api_keys.c.scopes == _ADMIN_PAIRING_SCOPE,
                        api_keys.c.revoked_at.is_(None),
                        api_keys.c.expires_at > now,
                        api_keys.c.request_count == 0,
                    )
                    .values(
                        revoked_at=now,
                        last_used_at=now,
                        request_count=1,
                    )
                    .returning(api_keys.c.owner_user_id)
                )
                .mappings()
                .first()
            )
            if consumed is None:
                return None
            owner_user_id = consumed["owner_user_id"]
            owner = (
                connection.execute(
                    select(users).where(
                        users.c.id == owner_user_id,
                        users.c.role == "admin",
                        users.c.is_approved.is_(True),
                        users.c.is_active.is_(True),
                    )
                )
                .mappings()
                .first()
            )
            if owner is None:
                return None
            connection.execute(
                insert(api_keys).values(
                    id=bridge_key_id,
                    owner_user_id=owner_user_id,
                    name="Termux Admin read-only bridge",
                    token_prefix=bridge_token_prefix,
                    token_hash=bridge_token_hash,
                    scopes=_ADMIN_BRIDGE_SCOPE,
                    created_at=now,
                    expires_at=bridge_expires_at,
                    request_count=0,
                )
            )
            self._audit(
                connection,
                actor_user_id=owner_user_id,
                action="auth.admin_bridge.exchanged",
                target_type="admin-bridge",
                target_id=bridge_key_id,
                outcome="success",
                request_id=request_id,
                ip_digest=ip_digest,
            )
        return {
            "id": bridge_key_id,
            "user": public_user(owner),
            "expires_at": bridge_expires_at,
        }

    def get_admin_bridge_principal(self, token_hash: str) -> dict[str, Any] | None:
        now = datetime.now(UTC)
        statement = (
            select(
                users,
                api_keys.c.id.label("api_key_id"),
                api_keys.c.name.label("api_key_name"),
            )
            .select_from(api_keys.join(users, api_keys.c.owner_user_id == users.c.id))
            .where(
                api_keys.c.token_hash == token_hash,
                api_keys.c.scopes == _ADMIN_BRIDGE_SCOPE,
                api_keys.c.revoked_at.is_(None),
                api_keys.c.expires_at > now,
                users.c.role == "admin",
                users.c.is_active.is_(True),
                users.c.is_approved.is_(True),
            )
        )
        with self.database.engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        principal = public_user(row)
        principal["api_key_id"] = row["api_key_id"]
        principal["api_key_name"] = row["api_key_name"]
        return principal

    def revoke_admin_bridge(
        self,
        token_hash: str,
        *,
        request_id: str | None,
        ip_digest: str | None,
    ) -> bool:
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            row = (
                connection.execute(
                    update(api_keys)
                    .where(
                        api_keys.c.token_hash == token_hash,
                        api_keys.c.scopes == _ADMIN_BRIDGE_SCOPE,
                        api_keys.c.revoked_at.is_(None),
                    )
                    .values(revoked_at=now)
                    .returning(api_keys.c.owner_user_id, api_keys.c.id)
                )
                .mappings()
                .first()
            )
            if row is None:
                return False
            self._audit(
                connection,
                actor_user_id=row["owner_user_id"],
                action="auth.admin_bridge.revoked",
                target_type="admin-bridge",
                target_id=row["id"],
                outcome="success",
                request_id=request_id,
                ip_digest=ip_digest,
            )
        return True

    def list_api_keys(self, owner_user_id: str) -> list[dict[str, Any]]:
        with self.database.engine.connect() as connection:
            rows = connection.execute(
                select(api_keys)
                .where(
                    api_keys.c.owner_user_id == owner_user_id,
                    api_keys.c.scopes.notin_([_ADMIN_PAIRING_SCOPE, _ADMIN_BRIDGE_SCOPE]),
                )
                .order_by(api_keys.c.created_at.desc())
                .limit(100)
            ).mappings()
        return [public_api_key(row) for row in rows]

    def revoke_api_key(
        self,
        *,
        owner_user_id: str,
        key_id: str,
        request_id: str | None,
        ip_digest: str | None,
    ) -> dict[str, Any] | None:
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            row = (
                connection.execute(
                    select(api_keys).where(
                        api_keys.c.id == key_id,
                        api_keys.c.owner_user_id == owner_user_id,
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                return None
            if row["revoked_at"] is None:
                connection.execute(
                    update(api_keys)
                    .where(api_keys.c.id == key_id, api_keys.c.owner_user_id == owner_user_id)
                    .values(revoked_at=now)
                )
                self._audit(
                    connection,
                    actor_user_id=owner_user_id,
                    action="developer.api_key.revoke",
                    target_type="api-key",
                    target_id=key_id,
                    outcome="success",
                    request_id=request_id,
                    ip_digest=ip_digest,
                )
            updated = (
                connection.execute(select(api_keys).where(api_keys.c.id == key_id)).mappings().one()
            )
        return public_api_key(updated)

    def get_api_key_principal(self, token_hash: str) -> dict[str, Any] | None:
        now = datetime.now(UTC)
        statement = (
            select(
                users,
                api_keys.c.id.label("api_key_id"),
                api_keys.c.name.label("api_key_name"),
                api_keys.c.scopes.label("api_key_scopes_json"),
            )
            .select_from(api_keys.join(users, api_keys.c.owner_user_id == users.c.id))
            .where(
                api_keys.c.token_hash == token_hash,
                api_keys.c.revoked_at.is_(None),
                api_keys.c.expires_at > now,
                users.c.is_active.is_(True),
                users.c.is_approved.is_(True),
            )
        )
        with self.database.engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        principal = public_user(row)
        principal["api_key_id"] = row["api_key_id"]
        principal["api_key_name"] = row["api_key_name"]
        principal["api_key_scopes"] = json.loads(row["api_key_scopes_json"])
        return principal

    def consume_api_key_request(
        self,
        key_id: str,
        *,
        maximum: int = 60,
        window_seconds: int = 60,
    ) -> bool:
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=window_seconds)
        reset_window = or_(
            api_keys.c.rate_window_started_at.is_(None),
            api_keys.c.rate_window_started_at <= cutoff,
        )
        statement = (
            update(api_keys)
            .where(
                api_keys.c.id == key_id,
                or_(reset_window, api_keys.c.request_count < maximum),
                api_keys.c.revoked_at.is_(None),
                api_keys.c.expires_at > now,
            )
            .values(
                rate_window_started_at=case(
                    (reset_window, now),
                    else_=api_keys.c.rate_window_started_at,
                ),
                request_count=case(
                    (reset_window, 1),
                    else_=api_keys.c.request_count + 1,
                ),
                last_used_at=now,
            )
            .returning(api_keys.c.id)
        )
        with self.database.engine.begin() as connection:
            row = connection.execute(statement).first()
        return row is not None

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
