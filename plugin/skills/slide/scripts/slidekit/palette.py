"""色の定義。色を書くのはこのファイルだけ。"""

PAPER = "FFFFFF"
INK = "1A1A1A"
GRAY = "6B6B6B"
ACCENT = "B23A2E"

# 格子の 1 文字 → 色。`.` は透明。
GRID_COLORS: dict[str, str | None] = {
    ".": None,
    "#": INK,
    "+": GRAY,
    "*": ACCENT,
}
