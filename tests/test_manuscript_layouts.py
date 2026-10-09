from pathlib import Path

import pytest

from slidekit.grid import Grid
from slidekit.manuscript import (
    BulletsBlock,
    Figure,
    ImageBlock,
    ManuscriptError,
    Table,
    TextBlock,
    TwoColumn,
    parse,
)

FIXTURES = Path(__file__).parent / "fixtures"


def parse_ok(body: str):
    return parse("# 題\n---\n" + body, FIXTURES).slides[1]


def problems_of(body: str):
    with pytest.raises(ManuscriptError) as e:
        parse("# 題\n---\n" + body, FIXTURES)
    return e.value.problems


def lines_of(body: str) -> list[int]:
    # 本文は 3 行目から始まる
    return [p.line for p in problems_of(body)]


def plain(t) -> str:
    return "".join(r.text for r in t)


# --- 図 ---


def test_figure_with_icon_and_caption():
    s = parse_ok("## 構成\n![歯車](icon:gear)\n毎晩 2 時に動く。\n")
    assert isinstance(s, Figure)
    assert s.heading == "構成"
    assert s.alt == "歯車"
    assert isinstance(s.grid, Grid) and (s.grid.width, s.grid.height) == (16, 16)
    assert plain(s.caption) == "毎晩 2 時に動く。"


def test_figure_without_caption():
    s = parse_ok("## 構成\n![歯車](icon:gear)\n")
    assert isinstance(s, Figure) and s.caption is None


def test_figure_with_grid_file_relative_to_base_dir():
    s = parse_ok("## ロボット\n![ロボット](robot.txt)\n")
    assert isinstance(s, Figure)
    assert (s.grid.width, s.grid.height) == (8, 8)


def test_figure_rejects_non_pixel_art():
    assert lines_of("## 写真\n![写真](photo.png)\n") == [4]


def test_figure_rejects_empty_alt():
    assert lines_of("## 構成\n![](icon:gear)\n") == [4]


def test_figure_rejects_unknown_icon_and_names_it():
    problems = problems_of("## 構成\n![x](icon:unicorn)\n")
    assert [p.line for p in problems] == [4]
    assert "unicorn" in problems[0].message


def test_figure_rejects_missing_grid_file():
    assert lines_of("## 構成\n![x](nothing.txt)\n") == [4]


def test_figure_grid_violation_reports_manuscript_line_and_grid_position():
    problems = problems_of("## ロボット\n![ロボット](bad_char.txt)\n")
    assert [p.line for p in problems] == [4]
    m = problems[0].message
    assert "bad_char.txt" in m
    assert "3 行目" in m and "5 文字目" in m


def test_figure_rejects_two_images_and_long_caption_block():
    assert lines_of("## 構成\n![a](icon:gear)\n![b](icon:box)\n") == [5]
    assert lines_of("## 構成\n![a](icon:gear)\n一行目\n二行目\n") == [6]


def test_figure_requires_heading():
    assert lines_of("![a](icon:gear)\n") == [3]


# --- 表 ---

TABLE = "## 比較\n| 名前 | 値 | 備考 |\n|---|---|---|\n| a | 1 | x |\n| b | 2 | y |\n| c | 3 | z |\n| d | 4 | w |\n"


def test_table_three_columns_four_body_rows():
    s = parse_ok(TABLE)
    assert isinstance(s, Table)
    assert s.heading == "比較"
    assert [plain(c) for c in s.header] == ["名前", "値", "備考"]
    assert len(s.rows) == 4
    assert [plain(c) for c in s.rows[3]] == ["d", "4", "w"]


def test_table_boundaries_are_accepted():
    parse_ok("## t\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    rows = "".join(f"| {i} | x | y | z |\n" for i in range(6))
    parse_ok("## t\n| a | b | c | d |\n|---|---|---|---|\n" + rows)


def test_table_with_five_columns_is_rejected():
    assert lines_of("## t\n| a | b | c | d | e |\n|-|-|-|-|-|\n| 1 | 2 | 3 | 4 | 5 |\n") == [4]


def test_table_with_one_column_is_rejected():
    assert lines_of("## t\n| a |\n|---|\n| 1 |\n") == [4]


def test_table_with_seven_body_rows_is_rejected_at_the_seventh():
    rows = "".join(f"| {i} | x |\n" for i in range(7))
    assert lines_of("## t\n| a | b |\n|---|---|\n" + rows) == [3 + 3 + 6]


def test_table_without_body_rows_is_rejected():
    assert lines_of("## t\n| a | b |\n|---|---|\n") == [4]


def test_table_with_ragged_row_is_rejected_at_that_row():
    assert lines_of("## t\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 |\n") == [7]


def test_table_without_separator_row_is_rejected():
    assert lines_of("## t\n| a | b |\n| 1 | 2 |\n") == [5]


def test_table_cell_may_hold_one_emphasis():
    s = parse_ok("## t\n| a | b |\n|---|---|\n| 1 | **2** |\n")
    assert s.rows[0][1][0].emphasis is True


# --- 左右 2 列 ---


def test_two_columns_bullets_and_image():
    s = parse_ok("## 比べる\n- 左の一\n- 左の二\n|||\n![箱](icon:box)\n")
    assert isinstance(s, TwoColumn)
    assert s.heading == "比べる"
    assert isinstance(s.left, BulletsBlock)
    assert [plain(i) for i in s.left.items] == ["左の一", "左の二"]
    assert isinstance(s.right, ImageBlock)
    assert s.right.alt == "箱"
    assert (s.right.grid.width, s.right.grid.height) == (16, 16)


def test_two_columns_sentence_and_sentence():
    s = parse_ok("## 比べる\n左の文\n|||\n右の文\n")
    assert isinstance(s.left, TextBlock) and plain(s.left.text) == "左の文"
    assert isinstance(s.right, TextBlock) and plain(s.right.text) == "右の文"


def test_two_columns_empty_right_is_rejected_at_the_separator():
    assert lines_of("## 比べる\n- a\n|||\n") == [5]


def test_two_columns_empty_left_is_rejected():
    assert lines_of("## 比べる\n|||\n- a\n") == [4]


def test_two_columns_five_bullets_in_a_block_rejected_at_fifth():
    left = "".join(f"- {i}\n" for i in range(5))
    assert lines_of(f"## 比べる\n{left}|||\n右\n") == [3 + 1 + 4]


def test_two_columns_four_bullets_are_accepted():
    left = "".join(f"- {i}\n" for i in range(4))
    parse_ok(f"## 比べる\n{left}|||\n右\n")


def test_two_columns_block_mixing_kinds_is_rejected():
    assert lines_of("## 比べる\n- a\n文\n|||\n右\n") == [5]
    assert lines_of("## 比べる\n![a](icon:box)\n文\n|||\n右\n") == [5]


def test_two_columns_two_separators_rejected():
    assert lines_of("## 比べる\n- a\n|||\n- b\n|||\n- c\n") == [7]


def test_two_columns_image_grid_violation_reports_manuscript_line():
    problems = problems_of("## 比べる\n左\n|||\n![x](bad_char.txt)\n")
    assert [p.line for p in problems] == [6]
    assert "5 文字目" in problems[0].message


def test_two_columns_nested_bullet_rejected():
    assert lines_of("## 比べる\n- a\n  - b\n|||\n右\n") == [5]
