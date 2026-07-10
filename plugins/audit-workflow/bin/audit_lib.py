"""Runtime shim for the single-file audit CLI.

`bin/audit` imports `audit_lib` before defining its local placeholder regex.
Keeping this shim next to `bin/audit` makes normal plugin execution use the shared
workflow constants while preserving the direct-copy fallback in `bin/audit`.
"""

from __future__ import annotations

import importlib.util
import re as _re
from pathlib import Path

# `bin/audit` historically stripped every single-brace `{...}` block as a
# placeholder. That corrupts real evidence such as JSON/API output:
# `{"error": "null user"}` or `{error: null user}`.
#
# Preserve JSON/config-like brace blocks by refusing placeholder matches when the
# brace body contains a colon or quotes. Plain template tokens such as
# `{description}` and `{path/to/file.py}` are still stripped.
_ORIGINAL_COMPILE = _re.compile
_ORIGINAL_PLACEHOLDER_PATTERN = r"<!--.*?-->|\bTODO\b|\{[^{}]+\}"
_JSON_SAFE_PLACEHOLDER_PATTERN = r"<!--.*?-->|\bTODO\b|\{(?![^{}]*(?::|\"|')[^{}]*\})[^{}]+\}"


def _compile(pattern, flags=0):  # type: ignore[no-untyped-def]
    if pattern == _ORIGINAL_PLACEHOLDER_PATTERN:
        pattern = _JSON_SAFE_PLACEHOLDER_PATTERN
    return _ORIGINAL_COMPILE(pattern, flags)


_re.compile = _compile

_SHARED_LIB = Path(__file__).resolve().parents[1] / "scripts" / "audit_lib.py"
_SPEC = importlib.util.spec_from_file_location("_audit_workflow_shared_audit_lib", _SHARED_LIB)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import bootstrap failure
    raise ModuleNotFoundError(f"cannot load shared audit lib: {_SHARED_LIB}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

ACTOR_ROLES = _MODULE.ACTOR_ROLES
ALLOWED_TRANSITIONS = _MODULE.ALLOWED_TRANSITIONS
VALID_CATEGORIES = _MODULE.VALID_CATEGORIES
VALID_SEVERITIES = _MODULE.VALID_SEVERITIES
VALID_STATUSES = _MODULE.VALID_STATUSES
VERIFICATION_STATUSES = _MODULE.VERIFICATION_STATUSES
_field = _MODULE._field
allowed_statuses = _MODULE.allowed_statuses
can_set_status = _MODULE.can_set_status
parse_ticket_filename = _MODULE.parse_ticket_filename
