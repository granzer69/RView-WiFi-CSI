#!/usr/bin/env python3
"""Run the V3 FastAPI server."""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=45231,
        reload=False,
        factory=False,
    )


if __name__ == "__main__":
    main()
