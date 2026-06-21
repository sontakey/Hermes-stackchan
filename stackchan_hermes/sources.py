"""Pluggable data sources for apps.

Apps should not hard-code where their data comes from. This helper resolves data
in priority order:

1. An explicit file path (``path`` argument).
2. A JSON file path from an environment variable (``env_var``).
3. Inline JSON from an environment variable (``env_var`` holding JSON, not a path).
4. A built-in demo payload (so everything runs out of the box).

This keeps the starter apps useful immediately while leaving a clean seam to wire
in real Hermes data later (point the env var at a file your gateway/cron writes).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


def load_data(
    *,
    path: Optional[str] = None,
    env_var: Optional[str] = None,
    demo: Any,
) -> tuple[Any, str]:
    """Return ``(data, source_label)`` from the first source that resolves."""
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8")), f"file:{path}"

    if env_var and (raw := os.environ.get(env_var)):
        candidate = Path(raw)
        if candidate.is_file():
            return (json.loads(candidate.read_text(encoding="utf-8")),
                    f"env-file:{env_var}")
        # Treat the value itself as inline JSON.
        return json.loads(raw), f"env-json:{env_var}"

    return demo, "demo"
