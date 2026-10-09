import pytest

from slidekit.grid import Grid, GridError, Problem, parse_grid

ROWS = [
    "........",
    ".######.",
    ".#++++#.",
    ".#+**+#.",
    ".#+**+#.",
    ".#++++#.",
    ".######.",
    "........",
]
GOOD_8X8 = "\n".join(ROWS)


def test_accepts_valid_8x8():
    grid = parse_grid(GOOD_8X8)
    assert isinstance(grid, Grid)
    assert (grid.width, grid.height) == (8, 8)
    assert grid.rows == GOOD_8X8.split("\n")


def test_rejects_unknown_char_with_position_and_allowed_chars():
    rows = GOOD_8X8.split("\n")
    rows[2] = rows[2][:4] + "x" + rows[2][5:]
    with pytest.raises(GridError) as exc:
        parse_grid("\n".join(rows))
    problems = exc.value.problems
    assert len(problems) == 1
    p = problems[0]
    assert isinstance(p, Problem)
    assert (p.line, p.col) == (3, 5)
    for allowed in (".", "#", "+", "*"):
        assert allowed in p.message
    assert "x" in p.message


def test_rejects_short_second_row():
    rows = GOOD_8X8.split("\n")
    rows[1] = rows[1][:-1]
    with pytest.raises(GridError) as exc:
        parse_grid("\n".join(rows))
    assert [p.line for p in exc.value.problems] == [2]


def test_rejects_width_65():
    with pytest.raises(GridError):
        parse_grid("." * 65)


def test_accepts_width_64_and_height_64():
    assert parse_grid("#" * 64).width == 64
    assert parse_grid("\n".join(["#"] * 64)).height == 64


def test_rejects_height_65():
    with pytest.raises(GridError):
        parse_grid("\n".join(["#"] * 65))


def test_rejects_empty():
    with pytest.raises(GridError):
        parse_grid("\n\n")


def test_ignores_trailing_blank_lines():
    grid = parse_grid(GOOD_8X8 + "\n\n\n")
    assert (grid.width, grid.height) == (8, 8)
