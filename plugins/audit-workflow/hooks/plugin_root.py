#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


def plugin_root() -> Path:
    env = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.environ.get("AUDIT_PLUGIN_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def project_dir(payload: dict | None = None) -> Path:
    payload = payload or {}
    env = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("AUDIT_PROJECT_DIR")
    if env:
        return Path(env).expanduser().resolve()
    for key in ("cwd", "project_dir", "projectDir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return Path(value).expanduser().resolve()
    return Path.cwd().resolve()
