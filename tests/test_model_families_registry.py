"""Registry discovery and load for mlp, gbdt, tcn."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.config import ApiSettings
from api.main import create_app
from api.model_registry import FAMILY_LOADERS, ModelRegistry
from datasets.esp_fi import SUBCARRIERS, TIME_STEPS
from ingestion.ml_contract import LABEL_TO_ID
from models.gbdt import train_gbdt
from models.mlp import train_mlp

pytest.importorskip("torch")
from models.tcn import train_tcn  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


def _tiny(n: int, times: int = 32, subcarriers: int = 8):
    rng = np.random.default_rng(9)
    x = rng.normal(size=(n, times, subcarriers))
    y = np.arange(n, dtype=np.int64) % len(LABEL_TO_ID)
    return x.astype(np.float64), y


def _esp_shaped(n: int):
    rng = np.random.default_rng(9)
    x = rng.normal(size=(n, TIME_STEPS, SUBCARRIERS))
    y = np.arange(n, dtype=np.int64) % len(LABEL_TO_ID)
    return x.astype(np.float64), y


def _write_classical_artifact(tmp_path: Path, family: str, train_fn, **kwargs) -> Path:
    train_x, train_y = _esp_shaped(12)
    model = train_fn(train_x, train_y, random_state=0, **kwargs)
    strategy_dir = tmp_path / "artifacts" / f"v2_{family}" / "fixture_run" / "in_domain"
    model.save(strategy_dir)
    return strategy_dir


def _write_tcn_artifact(tmp_path: Path) -> Path:
    train_x, train_y = _esp_shaped(10)
    val_x, val_y = _esp_shaped(4)
    model = train_tcn(train_x, train_y, val_x, val_y, epochs=1, batch_size=4, device="cpu", channels=16)
    strategy_dir = tmp_path / "artifacts" / "v2_tcn" / "fixture_run" / "in_domain"
    model.save(strategy_dir)
    return strategy_dir


def test_family_loaders_include_new_families():
    for family in ("mlp", "gbdt", "tcn"):
        assert family in FAMILY_LOADERS


def test_registry_discover_and_load_new_families(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    mlp_dir = _write_classical_artifact(tmp_path, "mlp", train_mlp, max_iter=50, hidden_layer_sizes=(16,))
    gbdt_dir = _write_classical_artifact(tmp_path, "gbdt", train_gbdt, max_iter=15, max_depth=3)
    tcn_dir = _write_tcn_artifact(tmp_path)

    settings = ApiSettings.from_env()
    settings = ApiSettings(
        repo_root=tmp_path,
        data_root=tmp_path / "data",
        model_artifact_dir=mlp_dir,
        cors_origins=settings.cors_origins,
    )
    registry = ModelRegistry(settings)
    entries = registry.discover_entries()
    families = {e["family"] for e in entries}
    assert {"mlp", "gbdt", "tcn"}.issubset(families)

    for family, strategy_dir in (
        ("mlp", mlp_dir),
        ("gbdt", gbdt_dir),
        ("tcn", tcn_dir),
    ):
        model_id = f"v2_{family}_in_domain_fixture_run"
        loaded = registry.load_by_id(model_id)
        assert loaded.family == family
        probe, _ = _esp_shaped(2)
        proba = loaded.backend.predict_proba(probe)
        assert proba.shape[0] == 2


def test_predict_api_with_mlp_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    strategy_dir = _write_classical_artifact(tmp_path, "mlp", train_mlp, max_iter=40, hidden_layer_sizes=(16,))
    settings = ApiSettings.from_env()
    settings = ApiSettings(
        repo_root=tmp_path,
        data_root=tmp_path / "data",
        model_artifact_dir=strategy_dir,
        cors_origins=settings.cors_origins,
    )
    client = TestClient(create_app(settings))
    amp = np.random.default_rng(0).normal(size=(TIME_STEPS, SUBCARRIERS)).tolist()
    response = client.post("/predict", json={"amplitude": amp, "session_id": "s1"})
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "model"
    assert body["activity"] in body.get("probabilities", {})
