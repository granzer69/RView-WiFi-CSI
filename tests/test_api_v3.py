"""V3 API smoke tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.config import ApiSettings
from api.main import create_app
from datasets.esp_fi import SUBCARRIERS, TIME_STEPS

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


def test_health_and_models(client: TestClient):
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True

    models = client.get("/models")
    assert models.status_code == 200
    payload = models.json()
    assert payload["active_model_id"]
    assert any(m["model_type"] == "random_forest" for m in payload["models"])


@pytest.mark.skipif(not MODEL_DIR.is_dir(), reason="RF artifact missing")
def test_predict_endpoint(client: TestClient):
    rng = np.random.default_rng(0)
    amplitude = rng.normal(size=(TIME_STEPS, SUBCARRIERS)).tolist()
    response = client.post(
        "/predict",
        json={
            "amplitude": amplitude,
            "session_id": "test-session",
            "environment_id": "scenario-1",
            "time_index": 100,
            "frame_count": TIME_STEPS,
        },
    )
    assert response.status_code == 200
    prediction = response.json()
    assert prediction["source"] == "model"
    assert prediction["activity"] in prediction.get("probabilities", {})
    assert prediction["spatial"]["simulated"] is True


def test_predict_rejects_oversized_payload(client: TestClient):
    row = [0.0] * SUBCARRIERS
    huge = [row] * 1000
    response = client.post("/predict", json={"amplitude": huge})
    assert response.status_code == 422


@pytest.mark.skipif(not DATA.exists(), reason="ESP-Fi data missing")
def test_websocket_stream_predictions(client: TestClient):
    from datasets.esp_fi import discover_trials

    session_id = sorted(discover_trials(DATA), key=lambda r: r.session_id)[0].session_id
    with client.websocket_connect("/ws/stream") as websocket:
        websocket.send_json({"type": "open_session", "session_id": session_id})
        started = websocket.receive_json()
        assert started["type"] == "session_started"
        websocket.send_json({"type": "control", "action": "play", "speed": 8})
        saw_prediction = False
        for _ in range(30):
            message = websocket.receive_json()
            if message["type"] == "prediction":
                payload = message["payload"]
                assert payload["source"] == "dataset_replay"
                assert payload["spatial"]["simulated"] is True
                assert "confidence" in payload
                saw_prediction = True
                break
        websocket.send_json({"type": "control", "action": "stop"})
        assert saw_prediction
