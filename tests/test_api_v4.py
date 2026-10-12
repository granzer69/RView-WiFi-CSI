"""V4 sensing platform API tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.config import ApiSettings
from api.main import create_app
from datasets.esp_fi import SUBCARRIERS, TIME_STEPS, discover_trials

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "esp-fi-har"
MODEL_DIR = ROOT / "artifacts" / "v2_rf" / "20261010T060000Z" / "in_domain"


@pytest.fixture
def client() -> TestClient:
    settings = ApiSettings.from_env()
    settings = ApiSettings(
        repo_root=settings.repo_root,
        data_root=DATA,
        model_artifact_dir=MODEL_DIR,
        cors_origins=settings.cors_origins,
    )
    return TestClient(create_app(settings))


def test_source_status_live_unavailable():
    settings = ApiSettings.from_env()
    missing_root = settings.repo_root / "data" / "raw" / "esp-fi-har-missing-for-test"
    settings = ApiSettings(
        repo_root=settings.repo_root,
        data_root=missing_root,
        model_artifact_dir=MODEL_DIR,
        cors_origins=settings.cors_origins,
    )
    client = TestClient(create_app(settings))
    response = client.get("/source/status")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "live_unavailable"
    assert body["live_implemented"] is False


@pytest.mark.skipif(not DATA.is_dir(), reason="ESP-Fi data missing")
def test_source_status_dataset_replay(client: TestClient):
    response = client.get("/source/status")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "dataset_replay"
    assert body["live_implemented"] is False


@pytest.mark.skipif(not DATA.is_dir(), reason="ESP-Fi data missing")
def test_activity_trials_and_sample(client: TestClient):
    trials = client.get("/activity/trials")
    assert trials.status_code == 200
    payload = trials.json()
    assert payload["trial_count"] > 0
    session_id = payload["trials"][0]["session_id"]
    sample = client.post(
        "/activity/sample",
        json={"session_id": session_id, "sample_index": 100},
    )
    assert sample.status_code == 200
    result = sample.json()
    assert result["session_id"] == session_id
    assert result["sample_index"] == 100
    assert result["status"] in ("evaluated-correct", "evaluated-incorrect", "error")


@pytest.mark.skipif(not DATA.is_dir(), reason="ESP-Fi data missing")
def test_explorer_catalog_quality_flags(client: TestClient):
    response = client.get("/explorer/catalog")
    assert response.status_code == 200
    trial = response.json()["trials"][0]
    assert "quality_flags" in trial
    assert "shape_ok" in trial["quality_flags"]


@pytest.mark.skipif(not MODEL_DIR.is_dir(), reason="RF artifact missing")
def test_predict_includes_sample_index(client: TestClient):
    import numpy as np

    rng = np.random.default_rng(0)
    amplitude = rng.normal(size=(TIME_STEPS, SUBCARRIERS)).tolist()
    response = client.post(
        "/predict",
        json={
            "amplitude": amplitude,
            "session_id": "test-session",
            "time_index": 50,
            "frame_count": TIME_STEPS,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("sample_index") == 50
    assert body.get("sample_count") == TIME_STEPS


@pytest.mark.skipif(not DATA.is_dir(), reason="ESP-Fi data missing")
def test_real_trial_predict_via_activity(client: TestClient):
    session_id = sorted(discover_trials(DATA), key=lambda r: r.session_id)[0].session_id
    response = client.post(
        "/activity/sample",
        json={"session_id": session_id, "sample_index": 949},
    )
    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
