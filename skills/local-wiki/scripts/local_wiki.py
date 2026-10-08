#!/usr/bin/env python3
"""Installed-path entry point for local wiki helpers (Python 3.10+)."""
import sys

sys.dont_write_bytecode = True
from droid_wiki.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
