from nanou_cyber_ai.models import MalwareMetadataIn
from nanou_cyber_ai.storage.sqlite import MalwareMetadataStore


def test_metadata_store_round_trip(tmp_path) -> None:
    store = MalwareMetadataStore(tmp_path)
    item = MalwareMetadataIn(
        sha256="b" * 64, label="malicious", source="test-fixture",
        features={"entropy_mean": 5.2},
    )
    saved = store.add(item)
    items = store.list()
    assert saved.sha256 == "b" * 64
    assert len(items) == 1
    assert items[0].features["entropy_mean"] == 5.2
