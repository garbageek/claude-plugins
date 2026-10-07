from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys

from .bundle import write_markdown_bundle
from .finalize import finalize_wiki
from .validate import fix_wiki, validate_wiki


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="local-wiki", description="Local Markdown wiki and optional static HTML tools")
    commands = parser.add_subparsers(dest="command", required=True)
    finalize = commands.add_parser("finalize", help="Update generated indexes and .wiki-meta.json (writes source wiki)")
    finalize.add_argument("wiki_dir")
    finalize.add_argument("--repo", help="Optional repository for revision metadata")
    validate = commands.add_parser("validate", help="Read-only structure and inline local-link validation")
    validate.add_argument("wiki_dir")
    validate.add_argument("--auto-fix", action="store_true", help="Explicitly repair common headings/links in place")
    bundle = commands.add_parser("build-markdown", help="Create one linked Markdown bundle; refuses existing output")
    bundle.add_argument("wiki_dir")
    bundle.add_argument("--out", required=True)
    bundle.add_argument("--title", default="Local Wiki")
    site = commands.add_parser("build-site", help="Create HTML; only previously marked generated output can be replaced")
    site.add_argument("wiki_dir")
    site.add_argument("--out", required=True)
    serve = commands.add_parser("serve", help="Serve generated HTML locally until interrupted")
    serve.add_argument("site_dir")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        if args.command == "finalize":
            meta = finalize_wiki(args.wiki_dir, repo=args.repo)
            print(f"Finalized {meta['pageCount']} pages")
        elif args.command == "validate":
            if args.auto_fix:
                for path, change in fix_wiki(args.wiki_dir):
                    print(f"FIX {path}: {change}")
            result = validate_wiki(args.wiki_dir)
            for warning in result.warnings:
                print(f"WARN {warning}")
            for error in result.errors:
                print(f"FAIL {error}")
            if not result.ok:
                return 1
            print("OK structure and inline local-link targets; anchors, reference links, and source claims still need review")
        elif args.command == "build-markdown":
            stats = write_markdown_bundle(args.wiki_dir, args.out, title=args.title)
            for warning in stats["warnings"]:
                print(f"WARN {warning}")
            print(f"Built {stats['pages']} pages into {args.out}")
        elif args.command == "build-site":
            try:
                from .site import build_site
            except ModuleNotFoundError as exc:
                raise ValueError("HTML rendering requires the packages in skill-local scripts/requirements.txt") from exc
            stats = build_site(args.wiki_dir, args.out)
            print(f"Built {stats['pages']} pages at {args.out}")
        elif args.command == "serve":
            root = Path(args.site_dir).expanduser().resolve()
            if not root.is_dir():
                raise ValueError(f"Site directory does not exist: {root}")
            handler = partial(SimpleHTTPRequestHandler, directory=str(root))
            with ThreadingHTTPServer((args.host, args.port), handler) as server:
                print(f"Serving {root} at http://{args.host}:{server.server_port}/", flush=True)
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    pass
    except (OSError, ValueError) as exc:
        print(f"local-wiki: {exc}", file=sys.stderr)
        return 2
    return 0
