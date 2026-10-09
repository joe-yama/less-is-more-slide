import struct
import zlib

from slidekit.grid import parse_grid
from slidekit.palette import GRID_COLORS
from slidekit.png import encode_png

ROWS = [
    "#+*.#+*.",
    "+*.#+*.#",
    "*.#+*.#+",
    ".#+*.#+*",
    "#+*.#+*.",
    "+*.#+*.#",
    "*.#+*.#+",
    ".#+*.#+*",
]
GRID_TEXT = "\n".join(ROWS)


def decode_png(data: bytes) -> tuple[int, int, list[list[tuple[int, ...]]]]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    idat = b""
    header = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        kind = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length : pos + 12 + length])
        assert crc == zlib.crc32(kind + body)
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    width, height, depth, color_type, _, _, interlace = header
    assert (depth, color_type, interlace) == (8, 6, 0)
    raw = zlib.decompress(idat)
    stride = 1 + width * 4
    assert len(raw) == stride * height
    pixels = []
    for y in range(height):
        row = raw[y * stride : (y + 1) * stride]
        assert row[0] == 0  # フィルタなし
        pixels.append([tuple(row[1 + x * 4 : 5 + x * 4]) for x in range(width)])
    return width, height, pixels


def rgba(color: str | None) -> tuple[int, ...]:
    if color is None:
        return (0, 0, 0, 0)
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16), 255)


def test_scale_10_gives_80x80_with_square_dots():
    grid = parse_grid(GRID_TEXT)
    width, height, pixels = decode_png(encode_png(grid, 10))
    assert (width, height) == (80, 80)
    for gy, row in enumerate(grid.rows):
        for gx, ch in enumerate(row):
            expected = rgba(GRID_COLORS[ch])
            for y in range(gy * 10, gy * 10 + 10):
                for x in range(gx * 10, gx * 10 + 10):
                    assert pixels[y][x] == expected


def test_only_three_colors_and_full_transparency():
    grid = parse_grid(GRID_TEXT)
    _, _, pixels = decode_png(encode_png(grid, 7))
    colors = {p for row in pixels for p in row}
    allowed = {rgba(c) for c in GRID_COLORS.values()}
    assert colors == allowed
    assert len(colors) == 4  # 3 色 + 完全な透明
    assert all(p[3] in (0, 255) for p in colors)


def test_non_square_grid():
    grid = parse_grid("#+\n*.\n..")
    width, height, _ = decode_png(encode_png(grid, 3))
    assert (width, height) == (6, 9)
