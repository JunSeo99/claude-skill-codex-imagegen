#!/usr/bin/env python3
"""Verify that a non-interlaced 8-bit PNG contains real transparent pixels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys
from typing import Optional
import zlib


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PNG_BYTES = 100 * 1024 * 1024
MAX_PIXELS = 10_000_000


def fail(message: str) -> None:
    print(f"verify_png_alpha.py: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify RGBA/gray-alpha PNG transparency without third-party packages."
    )
    parser.add_argument("image", help="PNG file to inspect")
    parser.add_argument(
        "--require-transparent-corners",
        action="store_true",
        help="also require all four corner pixels to have alpha 0",
    )
    return parser.parse_args()


def read_png(path: Path) -> tuple[int, int, int, bytes]:
    if path.is_symlink():
        fail("image must not be a symbolic link")
    if not path.is_file():
        fail(f"image does not exist or is not a regular file: {path}")
    if path.stat().st_size > MAX_PNG_BYTES:
        fail(f"image exceeds {MAX_PNG_BYTES} bytes")

    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        fail("file does not have a PNG signature")

    offset = len(PNG_SIGNATURE)
    ihdr: Optional[tuple[int, int, int]] = None
    compressed = bytearray()
    saw_iend = False

    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_start = offset + 8
        chunk_end = chunk_start + length
        crc_end = chunk_end + 4
        if crc_end > len(data):
            fail("PNG chunk extends beyond the file")
        chunk_data = data[chunk_start:chunk_end]
        expected_crc = struct.unpack(">I", data[chunk_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            fail(f"invalid CRC for {chunk_type.decode('ascii', errors='replace')} chunk")

        if chunk_type == b"IHDR":
            if ihdr is not None or length != 13:
                fail("invalid IHDR chunk")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if width == 0 or height == 0:
                fail("PNG dimensions must be positive")
            if width * height > MAX_PIXELS:
                fail(f"PNG exceeds {MAX_PIXELS} pixels")
            if bit_depth != 8 or color_type not in {4, 6}:
                fail("PNG must be 8-bit gray-alpha or RGBA")
            if compression != 0 or filtering != 0 or interlace != 0:
                fail("PNG must use standard compression/filtering and be non-interlaced")
            ihdr = (width, height, color_type)
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            saw_iend = True
            break
        offset = crc_end

    if ihdr is None or not compressed or not saw_iend:
        fail("PNG is missing IHDR, IDAT, or IEND data")
    width, height, color_type = ihdr
    return width, height, color_type, bytes(compressed)


def paeth(left: int, above: int, upper_left: int) -> int:
    prediction = left + above - upper_left
    left_distance = abs(prediction - left)
    above_distance = abs(prediction - above)
    upper_left_distance = abs(prediction - upper_left)
    if left_distance <= above_distance and left_distance <= upper_left_distance:
        return left
    if above_distance <= upper_left_distance:
        return above
    return upper_left


def decode_scanlines(
    compressed: bytes, width: int, height: int, channels: int
) -> list[bytearray]:
    stride = width * channels
    expected_size = height * (stride + 1)
    try:
        decompressor = zlib.decompressobj()
        raw = decompressor.decompress(compressed, expected_size + 1)
        if not decompressor.eof or decompressor.unconsumed_tail or decompressor.unused_data:
            fail("decompressed PNG data exceeds the expected size")
        raw += decompressor.flush()
    except zlib.error as error:
        fail(f"could not decompress PNG pixels: {error}")

    if len(raw) != expected_size:
        fail(f"unexpected decompressed size: got {len(raw)}, expected {expected_size}")

    rows: list[bytearray] = []
    offset = 0
    previous = bytearray(stride)
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        source = raw[offset : offset + stride]
        offset += stride
        row = bytearray(stride)
        for index, value in enumerate(source):
            left = row[index - channels] if index >= channels else 0
            above = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                predictor = paeth(left, above, upper_left)
            else:
                fail(f"unsupported PNG filter type: {filter_type}")
            row[index] = (value + predictor) & 0xFF
        rows.append(row)
        previous = row
    return rows


def inspect_alpha(path: Path, require_transparent_corners: bool) -> dict[str, object]:
    width, height, color_type, compressed = read_png(path)
    channels = 2 if color_type == 4 else 4
    alpha_offset = channels - 1
    rows = decode_scanlines(compressed, width, height, channels)
    minimum = 255
    maximum = 0
    transparent_pixels = 0
    partial_pixels = 0
    opaque_pixels = 0
    for row in rows:
        for index in range(alpha_offset, len(row), channels):
            alpha = row[index]
            minimum = min(minimum, alpha)
            maximum = max(maximum, alpha)
            if alpha == 0:
                transparent_pixels += 1
            elif alpha == 255:
                opaque_pixels += 1
            else:
                partial_pixels += 1
    if minimum != 0:
        fail(f"no fully transparent pixels found; minimum alpha is {minimum}")
    if maximum != 255:
        fail(f"no fully opaque pixels found; maximum alpha is {maximum}")

    corner_alpha = [
        rows[0][alpha_offset],
        rows[0][(width - 1) * channels + alpha_offset],
        rows[height - 1][alpha_offset],
        rows[height - 1][(width - 1) * channels + alpha_offset],
    ]
    if require_transparent_corners and corner_alpha != [0, 0, 0, 0]:
        fail(f"corners are not fully transparent: {corner_alpha}")

    return {
        "path": str(path),
        "width": width,
        "height": height,
        "color_type": "gray-alpha" if color_type == 4 else "rgba",
        "alpha_min": minimum,
        "alpha_max": maximum,
        "transparent_pixels": transparent_pixels,
        "partial_pixels": partial_pixels,
        "opaque_pixels": opaque_pixels,
        "corner_alpha": corner_alpha,
    }


def main() -> None:
    args = parse_args()
    path = Path(args.image).expanduser()
    metrics = inspect_alpha(path, args.require_transparent_corners)
    print(json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    main()
