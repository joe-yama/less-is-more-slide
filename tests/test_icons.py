import pytest

from slidekit.grid import GridError, icon_names, parse_grid, resolve

EXPECTED = {
    "person",
    "people",
    "arrow-right",
    "arrow-down",
    "box",
    "document",
    "gear",
    "clock",
    "check",
    "cross",
    "cloud",
    "computer",
    "magnifier",
    "chat",
}


def test_icon_names_are_exactly_the_spec_list():
    names = icon_names()
    assert len(names) == 14
    assert set(names) == EXPECTED


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_every_icon_is_a_valid_16x16_grid(name, tmp_path):
    grid = resolve(f"icon:{name}", tmp_path)
    assert (grid.width, grid.height) == (16, 16)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_every_icon_has_ink(name, tmp_path):
    grid = resolve(f"icon:{name}", tmp_path)
    assert any(ch != "." for row in grid.rows for ch in row)


def test_resolve_icon(tmp_path):
    assert resolve("icon:gear", tmp_path).width == 16


def test_resolve_relative_txt(tmp_path):
    (tmp_path / "art").mkdir()
    (tmp_path / "art" / "dot.txt").write_text("#+\n*.\n", encoding="utf-8")
    grid = resolve("art/dot.txt", tmp_path)
    assert grid == parse_grid("#+\n*.")


def test_unknown_icon_name(tmp_path):
    with pytest.raises(GridError) as exc:
        resolve("icon:nope", tmp_path)
    assert "nope" in str(exc.value)
    assert "gear" in str(exc.value)


def test_icon_name_cannot_escape_the_icon_folder(tmp_path):
    with pytest.raises(GridError):
        resolve("icon:../icons/gear", tmp_path)


def test_missing_file(tmp_path):
    with pytest.raises(GridError):
        resolve("missing.txt", tmp_path)


def test_non_txt_reference(tmp_path):
    (tmp_path / "art.png").write_text("#", encoding="utf-8")
    with pytest.raises(GridError):
        resolve("art.png", tmp_path)


def test_invalid_grid_file_reports_grid_positions(tmp_path):
    (tmp_path / "bad.txt").write_text("##\n#x\n", encoding="utf-8")
    with pytest.raises(GridError) as exc:
        resolve("bad.txt", tmp_path)
    assert [(p.line, p.col) for p in exc.value.problems] == [(2, 2)]
