"""添え訳（`^ ` の行）の解析と拒否。delta spec「添え訳の書式」「添え訳の拒否」。"""

from pathlib import Path

import pytest

from slidekit.manuscript import (
    Bullets,
    BulletsBlock,
    Cover,
    Figure,
    ManuscriptError,
    Statement,
    Table,
    TextBlock,
    TwoColumn,
    parse,
)


def deck(text: str):
    return parse(text, Path(".")).slides


def problems(text: str) -> list[tuple[int, str]]:
    with pytest.raises(ManuscriptError) as e:
        parse(text, Path("."))
    return [(p.line, p.message) for p in e.value.problems]


def bad_lines(text: str) -> list[int]:
    return [line for line, _ in problems(text)]


# --- 解析（添え訳が各フィールドに入る） ---


def test_cover_title_and_lines():
    cover = deck("# Title\n^ 題\nFirst\n^ 一\nSecond\n")[0]
    assert isinstance(cover, Cover)
    assert cover.title == "Title"
    assert cover.title_gloss == "題"
    assert cover.line_glosses == ["一", None]
    assert len(cover.lines) == 2


def test_cover_without_gloss_has_none():
    cover = deck("# Title\nFirst\n")[0]
    assert cover.title_gloss is None
    assert cover.line_glosses == [None]


def test_statement():
    s = deck("# T\n---\nHello\n^ こんにちは\n")[1]
    assert isinstance(s, Statement)
    assert s.gloss == "こんにちは"


def test_bullets_heading_and_items_keep_item_count():
    s = deck("# T\n---\n## Results\n^ 結果\n- Sales grew 30%\n^ 売上は 3 割伸びた\n- Plain\n")[1]
    assert isinstance(s, Bullets)
    assert s.heading == "Results"
    assert s.heading_gloss == "結果"
    assert len(s.items) == 2
    assert s.item_glosses == ["売上は 3 割伸びた", None]


def test_figure_heading_and_caption():
    s = deck("# T\n---\n## Fig\n^ 図\n![x](icon:gear)\nCaption\n^ 説明\n")[1]
    assert isinstance(s, Figure)
    assert s.heading_gloss == "図"
    assert s.caption_gloss == "説明"


def test_figure_without_caption_gloss():
    s = deck("# T\n---\n## Fig\n![x](icon:gear)\nCaption\n")[1]
    assert s.heading_gloss is None
    assert s.caption_gloss is None


def test_two_columns_items_and_text():
    s = deck("# T\n---\n## H\n^ 見出し\n- a\n^ あ\n- b\n|||\nText\n^ 文\n")[1]
    assert isinstance(s, TwoColumn)
    assert s.heading_gloss == "見出し"
    assert isinstance(s.left, BulletsBlock)
    assert s.left.item_glosses == ["あ", None]
    assert isinstance(s.right, TextBlock)
    assert s.right.gloss == "文"


def test_gloss_does_not_change_layout_decision():
    # 添え訳だけが間に入っても、全行が箇条書きなら箇条書き
    s = deck("# T\n---\n## H\n- a\n^ あ\n- b\n^ び\n")[1]
    assert isinstance(s, Bullets)
    assert len(s.items) == 2


# --- 拒否と行番号 ---

PREFIX = "# T\n---\n"  # 以降は 3 行目から


def test_gloss_at_slide_start():
    assert bad_lines(PREFIX + "^ 訳\nHello\n") == [3]


def test_gloss_after_blank_line():
    assert bad_lines(PREFIX + "## H\n- a\n\n^ 訳\n- b\n") == [6]


def test_gloss_after_figure_image():
    assert bad_lines(PREFIX + "## H\n![x](icon:gear)\n^ 訳\n") == [5]


def test_gloss_after_two_column_image():
    text = PREFIX + "## H\n![x](icon:gear)\n^ 訳\n|||\nText\n"
    assert bad_lines(text) == [5]


def test_gloss_after_column_break():
    text = PREFIX + "## H\nText\n|||\n^ 訳\nMore\n"
    assert bad_lines(text) == [6]


def test_two_glosses_in_a_row_rejects_second():
    assert bad_lines(PREFIX + "## H\n- a\n^ 一\n^ 二\n") == [6]


def test_gloss_on_cover_start_and_after_blank():
    assert bad_lines("^ 訳\n# T\n") == [1]
    assert bad_lines("# T\n\n^ 訳\n") == [3]


def test_bold_in_gloss():
    got = problems(PREFIX + "## H\n- a\n^ **訳**\n")
    assert [line for line, _ in got] == [5]
    assert "添え訳の中に強調は書けません" in got[0][1]


def test_caret_only_and_no_space():
    assert bad_lines(PREFIX + "## H\n- a\n^\n") == [5]
    assert bad_lines(PREFIX + "## H\n- a\n^訳\n") == [5]


@pytest.mark.parametrize(
    "gloss",
    ["🚀 訳", "[a](b) 訳", "`code` 訳", "__訳__", "*訳*", "~~訳~~"],
)
def test_inline_rules_apply_to_gloss(gloss):
    assert bad_lines(PREFIX + f"## H\n- a\n^ {gloss}\n") == [5]


def test_body_emphasis_is_not_rejected_because_of_gloss():
    # 添え訳の `**` は添え訳の理由で拒否されるが、本文の強調 1 か所は数え違えない
    got = problems(PREFIX + "## H\n- **a**\n^ **訳**\n- b\n")
    assert [line for line, _ in got] == [5]


def test_body_emphasis_with_valid_gloss_passes():
    s = deck(PREFIX + "## H\n- **a**\n^ 訳\n- b\n")[1]
    assert s.item_glosses == ["訳", None]


# --- 表 ---
# 3 行目から: ## H / 4 見出し行 / 5 区切り行 / 6 本文 1 / 7 本文 2
TABLE = "## H\n| Item | Sales | YoY |\n|---|---|---|\n| A | 10 | 5% |\n| B | 20 | 6% |\n"


def table_text(*glosses_after: tuple[int, str]) -> str:
    """表の原稿。(何行目の次か, 添え訳の行) を後ろから差し込む。"""
    lines = (PREFIX + TABLE).splitlines()
    for after, gloss in sorted(glosses_after, reverse=True):
        lines.insert(after, gloss)
    return "\n".join(lines) + "\n"


def test_table_header_and_row_glosses_per_cell():
    text = table_text((4, "^ | 品目 | 売上 | 前年比 |"), (6, "^ | A 社 | 10 億 | 5 % |"))
    t = deck(text)[1]
    assert isinstance(t, Table)
    assert t.header_glosses == ["品目", "売上", "前年比"]
    assert t.row_glosses == [["A 社", "10 億", "5 %"], [None, None, None]]
    assert len(t.rows) == 2


def test_table_gloss_with_empty_cell_is_none():
    t = deck(table_text((6, "^ | 売上 | | 前年比 |")))[1]
    assert t.row_glosses[0] == ["売上", None, "前年比"]


def test_table_without_gloss_has_none_cells():
    t = deck(PREFIX + TABLE)[1]
    assert t.header_glosses == [None, None, None]
    assert t.row_glosses == [[None, None, None], [None, None, None]]
    assert t.heading_gloss is None


def test_table_heading_gloss():
    t = deck(PREFIX + TABLE.replace("## H\n", "## H\n^ 見出し\n"))[1]
    assert t.heading_gloss == "見出し"


def test_table_gloss_wrong_cell_count():
    assert bad_lines(table_text((6, "^ | 売上 | 前年比 |"))) == [7]
    assert bad_lines(table_text((4, "^ | a | b | c | d |"))) == [5]


def test_table_gloss_all_empty():
    assert bad_lines(table_text((6, "^ | | | |"))) == [7]


def test_table_gloss_after_separator():
    assert bad_lines(table_text((5, "^ | a | b | c |"))) == [6]


def test_table_gloss_bold_in_cell():
    got = problems(table_text((6, "^ | **a** | b | c |")))
    assert [line for line, _ in got] == [7]
    assert "添え訳の中に強調は書けません" in got[0][1]
