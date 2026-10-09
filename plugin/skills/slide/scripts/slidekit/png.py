"""格子 → PNG のバイト列。zlib と struct だけで RGBA、フィルタなし。"""

import struct
import zlib

from slidekit.grid import Grid
from slidekit.palette import GRID_COLORS

_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def _rgba(color: str | None) -> bytes:
    if color is None:
        return b"\x00\x00\x00\x00"
    return bytes.fromhex(color) + b"\xff"


def encode_png(grid: Grid, scale: int) -> bytes:
    """1 ドットを scale × scale の正方形にした RGBA の PNG を返す。"""
    raw = bytearray()
    for row in grid.rows:
        line = b"\x00" + b"".join(_rgba(GRID_COLORS[ch]) * scale for ch in row)
        raw += line * scale
    header = struct.pack(">IIBBBBB", grid.width * scale, grid.height * scale, 8, 6, 0, 0, 0)
    return (
        _SIGNATURE
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(bytes(raw)))
        + _chunk(b"IEND", b"")
    )
