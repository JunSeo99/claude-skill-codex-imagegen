#!/usr/bin/env python3
"""Build the distributable skill archive reproducibly."""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skill"
DESTINATION = ROOT / "dist" / "codex-imagegen.skill"
ARCHIVE_ROOT = "codex-imagegen"
FIXED_TIMESTAMP = (2026, 8, 21, 0, 0, 0)


def source_files() -> list[Path]:
    return sorted(
        path
        for path in SOURCE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )


def build_archive() -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in source_files():
            relative = path.relative_to(SOURCE).as_posix()
            info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{relative}", FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            info.external_attr = (mode & 0xFFFF) << 16
            info.create_system = 3
            bundle.writestr(info, path.read_bytes())
    return output.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if dist/codex-imagegen.skill is not the reproducible current bundle",
    )
    args = parser.parse_args()
    archive = build_archive()
    if args.check:
        if not DESTINATION.is_file() or DESTINATION.read_bytes() != archive:
            print("dist/codex-imagegen.skill is stale; run scripts/package_skill.py", file=sys.stderr)
            raise SystemExit(1)
        print("dist/codex-imagegen.skill is current")
        return
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_bytes(archive)
    print(f"wrote {DESTINATION} ({len(archive)} bytes)")


if __name__ == "__main__":
    main()
