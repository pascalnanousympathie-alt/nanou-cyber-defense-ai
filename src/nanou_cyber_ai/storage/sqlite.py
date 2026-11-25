"""Malware metadata persistence backed by SQLite locally or PostgreSQL in hosting."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from nanou_cyber_ai.models import MalwareMetadata, MalwareMetadataIn
from nanou_cyber_ai.storage.database import SecurityDatabase, malware_metadata


class MalwareMetadataStore:
    def __init__(self, database: SecurityDatabase | Path) -> None:
        self.database = (
            database if isinstance(database, SecurityDatabase) else SecurityDatabase(None, database)
        )

    def add(self, item: MalwareMetadataIn) -> MalwareMetadata:
        normalized = item.model_copy(update={"sha256": item.sha256.lower()})
        record = MalwareMetadata(**normalized.model_dump())
        with self.database.engine.begin() as connection:
            values = {
                "sha256": record.sha256,
                "payload_json": record.model_dump_json(),
            }
            if self.database.mode == "sqlite":
                statement = sqlite_insert(malware_metadata).values(**values)
            else:
                statement = postgres_insert(malware_metadata).values(**values)
            statement = statement.on_conflict_do_update(
                index_elements=[malware_metadata.c.sha256],
                set_={
                    "payload_json": statement.excluded.payload_json,
                    "created_at": func.now(),
                },
            )
            connection.execute(statement)
        return record

    def list(self, limit: int = 100) -> list[MalwareMetadata]:
        bounded = max(1, min(limit, 500))
        with self.database.engine.connect() as connection:
            rows = connection.execute(
                select(malware_metadata.c.payload_json)
                .order_by(malware_metadata.c.created_at.desc())
                .limit(bounded)
            ).scalars()
            payloads = list(rows)
        return [MalwareMetadata.model_validate_json(payload) for payload in payloads]
