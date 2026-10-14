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


def test_gloss_color_is_not_a_grid_color():
    assert palette.GLOSS == "767676"
    assert palette.GLOSS not in palette.GRID_COLORS.values()


def test_frame_color_is_not_a_grid_color():
    assert palette.FRAME == "BDBDBD"
    assert palette.FRAME not in palette.GRID_COLORS.values()
