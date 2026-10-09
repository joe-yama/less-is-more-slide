from slidekit import palette


def test_four_colors():
    assert palette.PAPER == "FFFFFF"
    assert palette.INK == "1A1A1A"
    assert palette.GRAY == "6B6B6B"
    assert palette.ACCENT == "B23A2E"


def test_grid_colors_map_four_characters():
    assert palette.GRID_COLORS == {
        ".": None,
        "#": "1A1A1A",
        "+": "6B6B6B",
        "*": "B23A2E",
    }
    assert palette.GRID_COLORS["#"] == palette.INK
    assert palette.GRID_COLORS["+"] == palette.GRAY
    assert palette.GRID_COLORS["*"] == palette.ACCENT
