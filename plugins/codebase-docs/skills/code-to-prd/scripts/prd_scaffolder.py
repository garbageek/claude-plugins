#!/usr/bin/env python3
"""Generate an evidence-first PRD workspace from codebase_analyzer JSON."""
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime
from pathlib import Path
from typing import Any


def slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", text.lower().replace("/", "-").replace(":", "-").replace("*", "-"))).strip("-") or "item"


def page_name(path: str) -> str:
    if path == "/": return "Home"
    parts = [p.strip(":*?") for p in path.strip("/").split("/") if p]
    return " ".join(x.replace("-", " ").replace("_", " ").title() for x in parts) or "Page"


def source_note(item: dict[str, Any]) -> str:
    line = f":{item['line']}" if item.get("line") else ""
    return f"`{item.get('source', 'unknown')}{line}`"


def generate_readme(name: str, pages: list[dict], endpoints: list[dict], summary: dict, date: str) -> str:
    lines = [f"# {name} — Product Requirements Document", "", f"> Generated from static code evidence: {date}", "", "## Evidence Status", "", "- **Extracted facts:** source locations and static inventory entries below; verify composed routes and coverage limits.", "- **Inferred product meaning:** headings/names and any later interpretation require source-backed confirmation.", "- **Unknown behavior:** `[TBC]` marks unresolved intent, runtime behavior, or missing evidence; it is not a completed requirement.", "", "## System Overview", "", "[TBC] Confirm product purpose, users, and business context from code and stakeholder evidence.", "", "## Inventory", "", "| Artifact | Count |", "|---|---:|", f"| Frontend pages | {len(pages)} |", f"| Backend endpoints | {len(endpoints)} |", f"| Outbound API calls | {summary.get('api_endpoints',0)} |", f"| Models / DTOs | {summary.get('models',0)} |", f"| Enums | {summary.get('enums',0)} |", "", "## Frontend Page Inventory", "", "| # | Page | Route | Source | Document |", "|---:|---|---|---|---|"]
    for i, p in enumerate(pages, 1):
        fn = f"{i:02d}-{slugify(page_name(p['path']))}.md"
        lines.append(f"| {i} | {page_name(p['path'])} | `{p['path']}` | {source_note(p)} | [Open](pages/{fn}) |")
    lines += ["", "## Backend Endpoint Inventory", "", "| # | Method | Path | Framework | Source | Document |", "|---:|---|---|---|---|---|"]
    for i, e in enumerate(endpoints, 1):
        fn = f"{i:02d}-{slugify(e.get('method','unknown')+'-'+e['path'])}.md"
        lines.append(f"| {i} | {e.get('method','UNKNOWN')} | `{e['path']}` | {e.get('framework','unknown')} | {source_note(e)} | [Open](endpoints/{fn}) |")
    lines += ["", "## Evidence Gaps", "", "Static extraction is an inventory aid, not the completed PRD. Resolve `[TBC]` entries through targeted source review; never infer product meaning without evidence.", ""]
    return "\n".join(lines)


def generate_page(item: dict, date: str) -> str:
    return f"""# {page_name(item['path'])}

> **Route:** `{item['path']}`\x20\x20
> **Source:** {source_note(item)}\x20\x20
> **Generated:** {date}
> **Evidence:** route/source metadata is extracted; the display title is inferred; `[TBC]` remains unresolved.

## Product Purpose
[TBC] Derive the user goal and business outcome from page code, labels, navigation, and API usage.

## Layout and Regions
[TBC] Enumerate visible regions and responsive behavior from the rendered component tree.

## Fields and Controls
| Label | Control | Required | Default | Validation | Visibility condition | Evidence |
|---|---|---:|---|---|---|---|
| [TBC] | | | | | | |

## Data Presentation
| Element / Column | Format | Sort / Filter | Empty state | Evidence |
|---|---|---|---|---|
| [TBC] | | | | |

## Actions and Interactions
| Trigger | Visibility / permission | System response | Success | Failure | Evidence |
|---|---|---|---|---|---|
| [TBC] | | | | | |

## API Dependencies
| Direction | Method | Path | Trigger | Request | Response | Evidence |
|---|---|---|---|---|---|---|
| [TBC] | | | | | | |

## Navigation and Data Coupling
- **Inbound navigation:** [TBC]
- **Outbound navigation:** [TBC]
- **Route parameters:** [TBC]
- **Cross-page refresh / shared state:** [TBC]

## Business Rules and States
- Loading: [TBC]
- Empty: [TBC]
- Error: [TBC]
- Permission-denied: [TBC]
- Conditional rules: [TBC]
"""


def generate_endpoint(item: dict, date: str) -> str:
    return f"""# {item.get('method','UNKNOWN')} {item['path']}

> **Framework:** {item.get('framework','unknown')}\x20\x20
> **Source:** {source_note(item)}\x20\x20
> **Generated:** {date}\x20\x20
> **Path status:** {"[TBC] unresolved composed prefix" if item.get("unresolved_prefix") else "statically resolved"}

## Evidence Status
Method, path, and source are static inventory facts, subject to the path status above. Product meaning and runtime behavior remain unconfirmed until the source pass.

## Purpose
[TBC] Describe the product capability exposed by this endpoint from handler/service evidence.

## Contract
| Area | Definition | Evidence |
|---|---|---|
| Path parameters | [TBC] | |
| Query parameters | [TBC] | |
| Headers / authentication | [TBC] | |
| Request body | [TBC] | |
| Success response | [TBC] | |
| Error responses / status codes | [TBC] | |

## Validation and Permissions
- Validation rules: [TBC]
- Guards / middleware / decorators: [TBC]
- Role or ownership conditions: [TBC]

## Processing and Side Effects
- Service calls: [TBC]
- Database reads/writes: [TBC]
- Events / jobs / external calls: [TBC]
- Transaction and idempotency behavior: [TBC]

## Failure Behavior
- Expected domain failures: [TBC]
- Retry behavior: [TBC]
- Environment-dependent behavior: [TBC]
"""


def api_inventory(apis: list[dict]) -> str:
    lines = ["# Outbound API Inventory", "", "Only client/service-originated calls belong here; inbound routes are documented separately.", "", "| Method | Path | Source | Static client call detected | Mock-like text nearby |", "|---|---|---|---:|---:|"]
    for a in apis:
        lines.append(f"| {a.get('method','?')} | `{a.get('path','?')}` | {source_note(a)} | {'Yes' if a.get('integrated') else 'No'} | {'Yes' if a.get('mock_detected') else 'No'} |")
    if not apis: lines.append("| — | No calls detected | — | — | — |")
    return "\n".join(lines)+"\n"


def enum_inventory(enums: list[dict]) -> str:
    lines=["# Enum and Constant Dictionary",""]
    for e in enums:
        lines += [f"## {e['name']}", f"Source: {source_note(e)}", "", "| Key | Source value | Product meaning |", "|---|---|---|"]
        for k,v in (e.get('values') or {}).items(): lines.append(f"| `{k}` | `{v}` | [TBC] |")
        lines.append("")
    if not enums: lines.append("No enums detected; verify manually.")
    return "\n".join(lines)+"\n"


def model_inventory(models: list[dict]) -> str:
    lines=["# Models, Schemas, and DTOs",""]
    for m in models:
        lines += [f"## {m['name']}", f"Framework: {m.get('framework','unknown')}  ", f"Source: {source_note(m)}", "", "| Field | Type | Default / constraints | Product meaning |", "|---|---|---|---|"]
        for f in m.get('fields',[]): lines.append(f"| `{f.get('name','')}` | `{f.get('type','')}` | `{f.get('args') or f.get('default','')}` | [TBC] |")
        lines.append("")
    if not models: lines.append("No models detected; verify manually.")
    return "\n".join(lines)+"\n"


def scaffold(data: dict[str, Any], output: Path, name: str | None = None) -> None:
    """Create a new workspace. Never replace or merge an existing collection."""
    if not isinstance(data, dict) or "error" in data:
        raise ValueError("Expected a successful analyzer JSON object")
    if not isinstance(data.get("project"), dict) or not isinstance(data.get("routes"), dict):
        raise ValueError("Analysis must contain project and routes objects")
    if output.is_symlink() or (output.exists() and (not output.is_dir() or any(output.iterdir()))):
        raise ValueError(f"Destination must be absent or empty; existing content preserved: {output}")

    date = datetime.now().strftime("%Y-%m-%d")
    project = name or data["project"].get("name", "Project")
    pages = data["routes"].get("frontend_pages", [])
    endpoints = data["routes"].get("backend_endpoints", [])
    apis = data.get("apis", {}).get("endpoints", [])
    enums = data.get("enums", {}).get("definitions", [])
    models = data.get("models", {}).get("definitions", [])
    # Prepare everything before creating files, so malformed input does not leave
    # a half-generated destination. This is not an in-place regeneration engine.
    documents = {"README.md": generate_readme(project, pages, endpoints, data.get("summary", {}), date)}
    for i, page in enumerate(pages, 1):
        documents[f"pages/{i:02d}-{slugify(page_name(page['path']))}.md"] = generate_page(page, date)
    for i, endpoint in enumerate(endpoints, 1):
        documents[f"endpoints/{i:02d}-{slugify(endpoint.get('method', 'unknown') + '-' + endpoint['path'])}.md"] = generate_endpoint(endpoint, date)
    documents["appendix/api-inventory.md"] = api_inventory(apis)
    documents["appendix/enum-dictionary.md"] = enum_inventory(enums)
    documents["appendix/model-dictionary.md"] = model_inventory(models)
    documents["appendix/page-relationships.md"] = "# Page Relationships\n\n[TBC] Build from navigation calls, links, redirects, route parameters, and shared-state refresh behavior.\n"
    limits = data.get("limitations", [])
    if limits:
        documents["README.md"] += "\n## Extraction Limitations\n\n" + "\n".join(f"- {item}" for item in limits) + "\n"

    output.mkdir(parents=True, exist_ok=True)
    # Recheck after creation, and use exclusive writes: concurrent files are never
    # overwritten. An I/O failure can leave new partial output; nothing is deleted.
    if any(output.iterdir()):
        raise ValueError(f"Destination is no longer empty; existing content preserved: {output}")
    for folder in ("pages", "endpoints", "appendix"):
        (output / folder).mkdir()
    for relative, content in documents.items():
        with (output / relative).open("x", encoding="utf-8") as stream:
            stream.write(content)
    print(f"PRD workspace created: {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", help="Successful JSON inventory from codebase_analyzer.py")
    parser.add_argument("-o", "--output-dir", default="prd", help="Absent or empty destination")
    parser.add_argument("-n", "--project-name")
    args = parser.parse_args()
    try:
        data = json.loads(Path(args.analysis).read_text(encoding="utf-8"))
        scaffold(data, Path(args.output_dir), args.project_name)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"prd-scaffolder: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
