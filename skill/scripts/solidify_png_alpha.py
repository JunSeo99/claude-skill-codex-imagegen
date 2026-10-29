#!/usr/bin/env python3
"""Write a copy of an RGBA/gray-alpha PNG with near-opaque alpha raised to fully opaque."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys
import zlib

from verify_png_alpha import decode_scanlines, read_png


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Raise alpha >= threshold to 255 so a generated cutout's subject is solid."
    )
    parser.add_argument("image", help="source PNG (left unchanged)")
    parser.add_argument("output", help="new PNG path; must not exist")
    parser.add_argument("--threshold", type=int, default=240, help="alpha raised to 255 from this value (default: 240)")
    args = parser.parse_args()
    if not 1 <= args.threshold <= 255:
        parser.error("--threshold must be between 1 and 255")
    return args


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def solidify(source: Path, threshold: int) -> tuple[bytes, int]:
    width, height, color_type, compressed = read_png(source)
    channels = 4 if color_type == 6 else 2
    raw = bytearray()
    changed = 0
    for row in decode_scanlines(compressed, width, height, channels):
        for index in range(channels - 1, len(row), channels):
            if threshold <= row[index] < 255:
                row[index] = 255
                changed += 1
        raw += b"\x00" + row
    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    return png, changed


def main() -> None:
    args = parse_args()
    output = Path(args.output).expanduser()
    if output.exists() or output.is_symlink():
        print(f"solidify_png_alpha.py: output already exists: {output}", file=sys.stderr)
        raise SystemExit(1)
    png, changed = solidify(Path(args.image).expanduser(), args.threshold)
    output.write_bytes(png)
    print(f"{output} ({changed} pixels raised to alpha 255)")


if __name__ == "__main__":
    main()
