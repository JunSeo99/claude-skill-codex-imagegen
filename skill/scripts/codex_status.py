#!/usr/bin/env python3
"""Report whether the local Codex CLI is ready for this skill. Makes no model calls."""

from __future__ import annotations

import json
import re
import shutil
import subprocess

MINIMUM_VERSION = (0, 164, 0)
RELAY_MODEL = "gpt-6-luna"


def run(*args: str) -> str:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"error: {error}"
    return (completed.stdout + completed.stderr).strip()


def main() -> None:
    codex = shutil.which("codex")
    if codex is None:
        print("FAIL codex: not on PATH (npm install -g @openai/codex, then codex login)")
        raise SystemExit(1)
    ok = True

    version_text = run(codex, "--version")
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_text)
    version = tuple(int(part) for part in match.groups()) if match else None
    version_ok = version is not None and version >= MINIMUM_VERSION
    ok &= version_ok
    minimum = ".".join(map(str, MINIMUM_VERSION))
    print(f"{'OK  ' if version_ok else 'FAIL'} version: {version_text or 'unknown'} (minimum {minimum})")

    login = run(codex, "login", "status")
    login_ok = login.lower().startswith("logged in")
    ok &= login_ok
    print(f"{'OK  ' if login_ok else 'FAIL'} login: {login.splitlines()[0] if login else 'unknown'}")

    try:
        models = {m.get("slug") for m in json.loads(run(codex, "debug", "models")).get("models", [])}
    except (json.JSONDecodeError, AttributeError):
        models = set()
    relay_ok = RELAY_MODEL in models
    note = "available" if relay_ok else "not listed; pass --model with a light model from `codex debug models`"
    print(f"{'OK  ' if relay_ok else 'WARN'} relay {RELAY_MODEL}: {note}")

    print("Ready: yes" if ok else "Ready: no")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
