"""CSI Explorer and Experiment Workbench API tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import scipy.io as sio
from fastapi.testclient import TestClient

from api.config import ApiSettings
from api.main import create_app
from datasets.esp_fi import SUBCARRIERS, TIME_STEPS

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "artifacts" / "v2_rf" / "20261010T060000Z" / "in_domain"


@pytest.fixture
def esp_fi_tmp(tmp_path: Path) -> Path:
    """Minimal ESP-Fi layout: one unverified trial mat file."""
    mat_dir = tmp_path / "scenario1" / "mat"
    mat_dir.mkdir(parents=True)
    amp = np.random.default_rng(0).normal(size=(TIME_STEPS, SUBCARRIERS))
    sio.savemat(mat_dir / "1-1-2-1.mat", {"CSIamp": amp})
    return tmp_path


@pytest.fixture
def client(esp_fi_tmp: Path) -> TestClient:
    settings = ApiSettings.from_env()
    settings = ApiSettings(
        repo_root=settings.repo_root,
        data_root=esp_fi_tmp,
        model_artifact_dir=MODEL_DIR,
        cors_origins=settings.cors_origins,
    )
    return TestClient(create_app(settings))


@pytest.mark.skipif(not MODEL_DIR.is_dir(), reason="RF artifact missing")
def test_explorer_catalog_and_amplitude(client: TestClient):
    catalog = client.get("/explorer/catalog")
    assert catalog.status_code == 200
    body = catalog.json()
    assert body["trial_count"] == 1
    assert body["shape"]["time_steps"] == TIME_STEPS

    amp = client.get("/explorer/trials/1-1-2-1/amplitude")
    assert amp.status_code == 200
    matrix = amp.json()
    assert matrix["shape"] == [TIME_STEPS, SUBCARRIERS]
    assert len(matrix["amplitude"]) == TIME_STEPS


@pytest.mark.skipif(not MODEL_DIR.is_dir(), reason="RF artifact missing")
def test_explorer_subcarrier_and_stats(client: TestClient):
    detail = client.get("/explorer/trials/1-1-2-1")
    assert detail.status_code == 200
    stats = detail.json()["statistics"]
    assert stats["empty"] is False
    assert stats["finite_fraction"] == 1.0

    trace = client.get("/explorer/trials/1-1-2-1/subcarrier/0")
    assert trace.status_code == 200
    assert len(trace.json()["values"]) == TIME_STEPS


@pytest.mark.skipif(not MODEL_DIR.is_dir(), reason="RF artifact missing")
def test_explorer_prediction(client: TestClient):
    pred = client.get("/explorer/trials/1-1-2-1/prediction")
    assert pred.status_code == 200
    payload = pred.json()
    assert payload["ground_truth_label"]
    assert payload["prediction"]["activity"]


def test_experiments_schema(client: TestClient):
    schema = client.get("/experiments/schema")
    assert schema.status_code == 200
    body = schema.json()
    assert "logreg" in body["families"]
    assert "mlp" in body["families"]
    assert "gbdt" in body["families"]
    assert "tcn" in body["families"]
    assert "in_domain" in body["split_strategies"]


def test_experiments_preview(client: TestClient):
    response = client.post(
        "/experiments/runs",
        json={
            "family": "logreg",
            "preview_only": True,
            "strategies": ["in_domain"],
            "model": {"C": 1.0},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "preview"
    assert body["preview"]["cli_export"]


def test_experiments_rejects_unknown_hyperparam(client: TestClient):
    response = client.post(
        "/experiments/runs",
        json={
            "family": "logreg",
            "preview_only": True,
            "model": {"not_a_real_param": 1},
        },
    )
    assert response.status_code == 422
