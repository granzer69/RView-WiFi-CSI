from research.louo import build_louo_export_payload, summarize_louo_macro_f1


def test_summarize_louo_macro_f1():
    entries = [
        {"family": "logreg", "test_macro_f1": 0.4},
        {"family": "logreg", "test_macro_f1": 0.5},
        {"family": "rf", "test_macro_f1": 0.3},
    ]
    summary = summarize_louo_macro_f1(entries)
    assert summary["logreg"]["fold_count"] == 2
    assert summary["logreg"]["mean_macro_f1"] == 0.45
    assert summary["rf"]["mean_macro_f1"] == 0.3


def test_build_louo_export_payload_without_artifacts():
    payload = build_louo_export_payload()
    assert payload["evaluation_protocol"] == "leave_one_user_out"
    assert payload["status"] in {"pending", "complete"}
