#!/usr/bin/env python3
"""Export LOUO summary JSON for docs and the Research Lab."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from research.louo import build_louo_export_payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "frontend" / "public" / "research" / "louo.json",
    )
    args = parser.parse_args()

    payload = build_louo_export_payload(ROOT)
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "status": payload.get("status")}, indent=2))


if __name__ == "__main__":
    main()
