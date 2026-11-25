import hashlib
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from nanou_cyber_ai.api import app
from nanou_cyber_ai.malware.inference import (
    LoadedMalwareModel,
    classify_features,
    expected_feature_names,
    load_verified_model,
)
from nanou_cyber_ai.models import MalwareInferenceIn
from nanou_cyber_ai.settings import settings


class FakeClassifier:
    classes_ = [0, 1]
    n_features_in_ = 2568

    def predict_proba(self, rows):
        assert len(rows) == 1
        return [[0.15, 0.85]]


def test_ember_feature_schema_accepts_exact_numeric_vector() -> None:
    request = MalwareInferenceIn(
        dataset_id="ember2024-apk",
        features=[0.25] * 2568,
    )
    assert len(request.features) == 2568
    assert request.schema_version == 1


def test_lamda_feature_schema_preserves_signed_int8_values() -> None:
    request = MalwareInferenceIn(
        dataset_id="lamda-apk-2022-train-2023-test",
        features=[-128, -1, 0, 127] + [1] * 4557,
    )
    assert request.features[:4] == [-128.0, -1.0, 0.0, 127.0]


@pytest.mark.parametrize(
    "payload",
    [
        {"dataset_id": "ember2024-apk", "features": [0.0] * 2567},
        {
            "dataset_id": "lamda-apk-2022-train-2023-test",
            "features": [128.0] + [0.0] * 4560,
        },
        {"dataset_id": "ember2024-apk", "features": [0.0] * 2567 + [float("nan")]},
        {"dataset_id": "ember2024-apk", "features": [True] + [0.0] * 2567},
        {"dataset_id": "ember2024-apk", "features": [0.0] * 2567 + [1e20]},
        {"dataset_id": "ember2024-apk", "features": [0.0] * 2568, "apk": "file.apk"},
    ],
)
def test_inference_request_rejects_wrong_schema_or_unsafe_values(payload) -> None:
    with pytest.raises(ValidationError):
        MalwareInferenceIn.model_validate(payload)


def test_unsupported_dataset_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported malware model dataset"):
        expected_feature_names("unknown-dataset")


def test_model_artifact_hash_is_checked_before_deserialization(tmp_path) -> None:
    artifact = tmp_path / "model.joblib"
    artifact.write_bytes(b"not a trusted model")
    with pytest.raises(ValueError, match="SHA-256"):
        load_verified_model(
            str(artifact),
            "0" * 64,
            "ember2024-apk",
        )


def test_classifier_uses_explicit_threshold_and_returns_provenance() -> None:
    model = LoadedMalwareModel(
        dataset_id="ember2024-apk",
        feature_names=expected_feature_names("ember2024-apk"),
        model=FakeClassifier(),
        sha256="a" * 64,
    )
    result = classify_features(model, [0.0] * 2568, threshold=0.8)
    assert result["classification"] == "malicious"
    assert result["malicious_probability"] == 0.85
    assert result["decision_threshold"] == 0.8
    assert result["model_sha256"] == "a" * 64


def test_inference_endpoint_requires_bearer_token_and_verified_model(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "metadata_api_token", SecretStr("test-only-token"))
    monkeypatch.setattr(settings, "malware_model_path", tmp_path / "model.joblib")
    monkeypatch.setattr(settings, "malware_model_sha256", "a" * 64)
    monkeypatch.setattr(settings, "malware_model_dataset_id", "ember2024-apk")

    with TestClient(app) as client:
        denied = client.post(
            "/api/malware/inference",
            json={"dataset_id": "ember2024-apk", "features": [0.0] * 2568},
        )

    assert denied.status_code in (401, 403)


def test_inference_endpoint_runs_only_after_authenticated_model_load(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "metadata_api_token", SecretStr("test-only-token"))
    monkeypatch.setattr(settings, "malware_model_path", tmp_path / "model.joblib")
    monkeypatch.setattr(settings, "malware_model_sha256", "a" * 64)
    monkeypatch.setattr(settings, "malware_model_dataset_id", "ember2024-apk")
    loaded = LoadedMalwareModel(
        dataset_id="ember2024-apk",
        feature_names=expected_feature_names("ember2024-apk"),
        model=FakeClassifier(),
        sha256="a" * 64,
    )
    monkeypatch.setattr("nanou_cyber_ai.api.load_configured_malware_model", lambda: loaded)

    with TestClient(app) as client:
        response = client.post(
            "/api/malware/inference",
            headers={"Authorization": "Bearer test-only-token"},
            json={"dataset_id": "ember2024-apk", "features": [0.0] * 2568},
        )

    assert response.status_code == 200
    assert response.json()["classification"] == "malicious"
    assert response.json()["feature_count"] == 2568
    assert response.json()["model_sha256"] == "a" * 64


def test_inference_status_reports_no_model_when_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "malware_model_path", None)
    monkeypatch.setattr(settings, "malware_model_sha256", None)
    monkeypatch.setattr(settings, "malware_model_dataset_id", None)

    with TestClient(app) as client:
        response = client.get("/api/malware/inference/status")

    assert response.status_code == 200
    assert response.json()["available"] is False


def test_verified_loader_checks_digest_and_exact_feature_names(monkeypatch, tmp_path) -> None:
    model_file = tmp_path / "trusted-model.joblib"
    payload = b"operator-approved-test-artifact"
    model_file.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    fake_joblib = SimpleNamespace(
        load=lambda stream: {
            "dataset_id": "ember2024-apk",
            "schema_version": 1,
            "feature_names": expected_feature_names("ember2024-apk"),
            "model": FakeClassifier(),
        }
    )
    monkeypatch.setitem(sys.modules, "joblib", fake_joblib)
    loaded = load_verified_model(
        str(model_file),
        digest,
        "ember2024-apk",
    )
    assert loaded.sha256 == digest
    assert len(loaded.feature_names) == 2568


def test_verified_loader_rejects_wrong_model_schema(monkeypatch, tmp_path) -> None:
    model_file = tmp_path / "wrong-schema.joblib"
    payload = b"operator-approved-test-artifact-with-wrong-schema"
    model_file.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    fake_joblib = SimpleNamespace(
        load=lambda stream: {
            "dataset_id": "ember2024-apk",
            "schema_version": 1,
            "feature_names": ("feature_wrong",),
            "model": FakeClassifier(),
        }
    )
    monkeypatch.setitem(sys.modules, "joblib", fake_joblib)
    with pytest.raises(ValueError, match="feature names"):
        load_verified_model(
            str(model_file),
            digest,
            "ember2024-apk",
        )
