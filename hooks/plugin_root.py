#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


def plugin_root() -> Path:
    """Resolve bundled resources from this installed copy, not inherited overrides."""
    return Path(__file__).resolve().parents[1]


def project_dir(payload: dict | None = None) -> Path:
    payload = payload or {}
    for key in ("AUDIT_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        value = os.environ.get(key)
        if value:
            return Path(value).expanduser().resolve()
    value = next((payload[k] for k in ("cwd", "project_dir", "projectDir")
                  if isinstance(payload.get(k), str) and payload[k]), None)
    current = Path(value).expanduser().resolve() if value else Path.cwd().resolve()
    # A session opened below the project root still observes its existing audit.
    # Do not cross a nested repository/worktree boundary to find someone else's state.
    for candidate in (current, *current.parents):
        if (candidate / "audit").is_dir() or (candidate / ".git").exists():
            return candidate
    return current
