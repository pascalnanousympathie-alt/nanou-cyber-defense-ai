import sqlite3
from pathlib import Path

from nanou_cyber_ai.models import MalwareMetadata, MalwareMetadataIn


class MalwareMetadataStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir.expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "malware_metadata.sqlite3"
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS malware_metadata "
                "(sha256 TEXT PRIMARY KEY, payload_json TEXT NOT NULL, "
                "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )

    def add(self, item: MalwareMetadataIn) -> MalwareMetadata:
        record = MalwareMetadata(**item.model_dump())
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO malware_metadata (sha256, payload_json) VALUES (?, ?)",
                (record.sha256.lower(), record.model_dump_json()),
            )
        return record

    def list(self, limit: int = 100) -> list[MalwareMetadata]:
        bounded = max(1, min(limit, 500))
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM malware_metadata ORDER BY created_at DESC LIMIT ?",
                (bounded,),
            ).fetchall()
        return [MalwareMetadata.model_validate_json(row["payload_json"]) for row in rows]
