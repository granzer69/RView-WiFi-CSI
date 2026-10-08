import json
from pathlib import Path

from datasets.leakage import published_folder_report

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "configs" / "datasets" / "esp_fi_published_split.json"


def test_published_folders_are_one_subject_holdout():
    document = json.loads(MANIFEST.read_text())
    report = published_folder_report(document["records"])
    assert report["train_count"] == 490
    assert report["test_count"] == 70
    assert report["train_participants"] == [2, 3, 4, 5, 6, 7, 8]
    assert report["test_participants"] == [1]
    assert report["train_scenarios"] == [3]
    assert report["test_scenarios"] == [3]
    assert report["shared_session_ids"] == []
    assert report["session_leakage"] is False
    assert report["participant_leakage"] is False
    assert report["single_scenario"] is True
    stems = [row["stem"] for row in document["records"]]
    assert len(stems) == len(set(stems)) == 560
