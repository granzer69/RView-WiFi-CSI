"""Workbench validation smoke for mlp, gbdt, tcn."""

from __future__ import annotations

from pathlib import Path

import yaml

from api.workbench import SUPPORTED_FAMILIES, experiment_schema, validate_run_request

ROOT = Path(__file__).resolve().parents[1]


def test_experiment_schema_lists_new_families():
    schema = experiment_schema()
    for family in ("mlp", "gbdt", "tcn"):
        assert family in schema["families"]
        assert family in schema["hyperparameters"]


def test_yaml_configs_parse_for_new_families():
    for name in ("v2_mlp_esp_fi.yaml", "v2_gbdt_esp_fi.yaml", "v2_tcn_esp_fi.yaml"):
        payload = yaml.safe_load((ROOT / "configs" / "experiments" / name).read_text())
        assert payload["artifacts"]["root"].startswith("artifacts/v2_")


def test_workbench_preview_validates_mlp_gbdt_tcn(tmp_path: Path):
    data_root = tmp_path / "esp"
    data_root.mkdir()
    for family in ("mlp", "gbdt", "tcn"):
        assert family in SUPPORTED_FAMILIES
        validated = validate_run_request(
            {"family": family, "strategies": ["in_domain"], "model": {}},
            data_root=data_root,
            repo_root=tmp_path,
        )
        assert validated["family"] == family
        assert validated["artifacts_root"].name == family
        assert validated["artifacts_root"].parent.name == "workbench"
