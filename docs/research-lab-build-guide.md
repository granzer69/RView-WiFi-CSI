# Research Lab build guide

## Export JSON (required before UI)

From the repository root:

```bash
python3 scripts/export_research_lab.py
python3 scripts/export_participant_profiles.py
python3 scripts/export_evaluation_summary.py  # optional; richer evaluation page
```

Outputs:

| Script | Frontend | Reports |
| --- | --- | --- |
| `export_research_lab.py` | `frontend/public/research/generalization.json` | `reports/research/generalization_report.json` |
| `export_participant_profiles.py` | `frontend/public/research/participants.json`, `personalization.json` | — |

## API (optional)

After exports exist:

- `GET /research/generalization`
- `GET /research/participants`

## Frontend

```bash
cd frontend && npm run dev
```

Open `/research` for Generalization, User Profiling, Personalization, and Experiment Details tabs.

## Tests

```bash
python3 -m pytest -q tests/test_research_generalization.py tests/test_research_participant.py tests/test_research_leakage.py
```

Participant metrics export requires ESP-Fi under `data/raw/esp-fi-har` and PyTorch for CNN/GRU families.
