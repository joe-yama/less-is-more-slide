"""色の定義。色を書くのはこのファイルだけ。"""

PAPER = "FFFFFF"
INK = "1A1A1A"
GRAY = "6B6B6B"
ACCENT = "B23A2E"
# 添え訳の文字の色。白とのコントラスト比 4.54:1。GRID_COLORS には入れない。
GLOSS = "767676"

# 構成図の範囲の枠の線の色。GRID_COLORS には入れない。
FRAME = "BDBDBD"

# 格子の 1 文字 → 色。`.` は透明。
GRID_COLORS: dict[str, str | None] = {
    ".": None,
    "#": INK,
    "+": GRAY,
    "*": ACCENT,
}
