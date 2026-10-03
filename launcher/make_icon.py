"""Generates launcher/ahos.ico with no third-party dependencies.

Modern Windows (Vista+) accepts PNG-encoded entries inside an ICO container, so
this builds one in pure stdlib: a small PNG writer (CRC + zlib only) wrapped in
the ICONDIR/ICONDIRENTRY layout. The glyph is a dark tile with three rising
green bars — a paper-only chart, nothing that suggests live trading.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

BG = (12, 16, 28)
BAR = (74, 222, 128)
EDGE = (40, 48, 66)


def _png(width: int, height: int, pixels: list[list[tuple[int, int, int]]]) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)

    raw = b""
    for y in range(height):
        raw += b"\x00"  # filter type 0 (None)
        for x in range(width):
            r, g, b = pixels[y][x]
            raw += bytes((r, g, b))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    return png


def _bars(size: int) -> list[list[tuple[int, int, int]]]:
    grid = [[BG] * size for _ in range(size)]
    for x in range(size):
        grid[0][x] = EDGE
        grid[size - 1][x] = EDGE
        grid[x][0] = EDGE
        grid[x][size - 1] = EDGE
    # three rising bars, left to right, sitting on the bottom edge
    heights = (size // 3, size // 2, size - size // 4)
    bar_w = max(2, size // 7)
    gap = max(1, size // 8)
    x = size // 4
    for h in heights:
        for dx in range(bar_w):
            for y in range(size - 2 - h, size - 2):
                if 0 <= y < size and 0 <= x + dx < size:
                    grid[y][x + dx] = BAR
        x += bar_w + gap
    return grid


def build(out: Path, sizes: tuple[int, ...] = (32, 16)) -> Path:
    images = [(s, _png(s, s, _bars(s))) for s in sizes]
    header = struct.pack("<HHH", 0, 1, len(images))
    entries, blobs, offset = b"", b"", 6 + 16 * len(images)
    for size, png in images:
        entries += struct.pack("<BBBBHHII", size if size < 256 else 0, size if size < 256 else 0,
                               0, 0, 1, 32, len(png), offset)
        blobs += png
        offset += len(png)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(header + entries + blobs)
    return out


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "ahos.ico"
    path = build(target)
    print(f"wrote {path} ({path.stat().st_size} bytes)")
