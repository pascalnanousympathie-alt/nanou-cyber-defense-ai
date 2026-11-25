"""Persistence for authorized target scopes and local-only simulations."""

from __future__ import annotations

import ipaddress
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert, select, update

from nanou_cyber_ai.attack_simulation import build_simulation_report
from nanou_cyber_ai.storage.database import SecurityDatabase, attack_scopes, attack_simulations


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _scope_payload(row: Any) -> dict[str, Any]:
    expires = _as_utc(row["authorization_expires_at"])
    created = _as_utc(row["created_at"])
    return {
        "id": row["id"],
        "name": row["name"],
        "target": row["target"],
        "target_type": row["target_type"],
        "authorization_basis": row["authorization_basis"],
        "authorization_expires_at": expires.isoformat(),
        "is_active": bool(row["is_active"]),
        "is_authorization_current": bool(row["is_active"] and expires > datetime.now(UTC)),
        "created_at": created.isoformat(),
    }


class AttackSimulationStore:
    def __init__(self, database: SecurityDatabase) -> None:
        self.database = database

    def create_scope(
        self,
        *,
        created_by_user_id: str,
        name: str,
        target: str,
        authorization_basis: str,
        authorization_expires_at: datetime,
    ) -> dict[str, Any]:
        scope_id = uuid.uuid4().hex
        try:
            ipaddress.ip_address(target)
            target_type = "ip"
        except ValueError:
            target_type = "domain"
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            connection.execute(
                insert(attack_scopes).values(
                    id=scope_id,
                    created_by_user_id=created_by_user_id,
                    name=name,
                    target=target,
                    target_type=target_type,
                    authorization_basis=authorization_basis,
                    authorization_expires_at=authorization_expires_at,
                    is_active=True,
                    created_at=now,
                )
            )
            row = (
                connection.execute(select(attack_scopes).where(attack_scopes.c.id == scope_id))
                .mappings()
                .one()
            )
        return _scope_payload(row)

    def list_scopes(self, *, include_inactive: bool = False) -> list[dict[str, Any]]:
        statement = select(attack_scopes).order_by(attack_scopes.c.created_at.desc())
        if not include_inactive:
            statement = statement.where(attack_scopes.c.is_active.is_(True))
        with self.database.engine.connect() as connection:
            rows = connection.execute(statement.limit(200)).mappings()
        return [_scope_payload(row) for row in rows]

    def get_scope(self, scope_id: str) -> dict[str, Any] | None:
        with self.database.engine.connect() as connection:
            row = (
                connection.execute(select(attack_scopes).where(attack_scopes.c.id == scope_id))
                .mappings()
                .first()
            )
        return _scope_payload(row) if row is not None else None

    def deactivate_scope(self, scope_id: str) -> dict[str, Any] | None:
        with self.database.engine.begin() as connection:
            connection.execute(
                update(attack_scopes)
                .where(attack_scopes.c.id == scope_id, attack_scopes.c.is_active.is_(True))
                .values(is_active=False)
            )
            row = (
                connection.execute(select(attack_scopes).where(attack_scopes.c.id == scope_id))
                .mappings()
                .first()
            )
        return _scope_payload(row) if row is not None else None

    def create_simulation(
        self,
        *,
        actor_user_id: str,
        scope_id: str,
        profile: str,
        intensity: str,
        duration_minutes: int,
    ) -> dict[str, Any]:
        simulation_id = uuid.uuid4().hex
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            scope_row = (
                connection.execute(
                    select(attack_scopes).where(attack_scopes.c.id == scope_id).with_for_update()
                )
                .mappings()
                .first()
            )
            if scope_row is None:
                raise LookupError("Tsy hita ny target ao amin'ny allowlist.")
            scope = _scope_payload(scope_row)
            if not scope["is_active"]:
                raise PermissionError("Nesorin'ny Administrator tao amin'ny allowlist ilay target.")
            if not scope["is_authorization_current"]:
                raise PermissionError("Lany daty ny fahazoan-dalana; havaozy amin'ny Admin.")
            report = build_simulation_report(
                simulation_id=simulation_id,
                scope=scope,
                profile=profile,
                intensity=intensity,
                duration_minutes=duration_minutes,
                created_at=now,
            )
            connection.execute(
                insert(attack_simulations).values(
                    id=simulation_id,
                    actor_user_id=actor_user_id,
                    scope_id=scope_id,
                    profile=profile,
                    intensity=intensity,
                    duration_minutes=duration_minutes,
                    result_json=json.dumps(report, ensure_ascii=False, separators=(",", ":")),
                    created_at=now,
                )
            )
        return report

    def list_simulations(self, limit: int = 50) -> list[dict[str, Any]]:
        statement = (
            select(attack_simulations.c.result_json)
            .order_by(attack_simulations.c.created_at.desc())
            .limit(max(1, min(limit, 100)))
        )
        with self.database.engine.connect() as connection:
            rows = connection.execute(statement).all()
        return [json.loads(row[0]) for row in rows]

    def get_simulation(self, simulation_id: str) -> dict[str, Any] | None:
        with self.database.engine.connect() as connection:
            row = connection.execute(
                select(attack_simulations.c.result_json).where(
                    attack_simulations.c.id == simulation_id
                )
            ).first()
        return json.loads(row[0]) if row is not None else None
