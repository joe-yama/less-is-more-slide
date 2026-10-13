"""添え訳（`^ ` の行）の解析と拒否。delta spec「添え訳の書式」「添え訳の拒否」。"""

from pathlib import Path

import pytest

from slidekit.fit import line_count
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


# --- 行数の上限と高さの判定 ---

BODY = 11.53
INDENT = 0.4
COLUMN = 5.5
CAPTION = 5.2


def zen(pt: float, width: float, lines: int) -> str:
    """全角文字だけで、ちょうど lines 行になる文字列（fit.line_count で数える）。"""
    n = 1 if lines == 1 else int(width * 72 / pt * (lines - 1)) + 1
    text = "あ" * n
    assert line_count(text, pt, width) == lines
    return text


def test_bullet_gloss_over_two_lines():
    gloss = zen(14, BODY - INDENT, 3)
    got = problems(PREFIX + f"## H\n- a\n^ {gloss}\n")
    assert [line for line, _ in got] == [5]
    assert "上限は 2 行" in got[0][1]


def test_bullet_gloss_two_lines_ok():
    deck(PREFIX + f"## H\n- a\n^ {zen(14, BODY - INDENT, 2)}\n")


def test_heading_gloss_limit_is_one_line():
    assert bad_lines(PREFIX + f"## H\n^ {zen(18, BODY, 2)}\n- a\n") == [4]
    deck(PREFIX + f"## H\n^ {zen(18, BODY, 1)}\n- a\n")


def test_cover_line_gloss_limit_is_one_line():
    assert bad_lines(f"# T\nSub\n^ {zen(12, BODY, 2)}\n") == [3]
    deck(f"# T\nSub\n^ {zen(12, BODY, 1)}\n")


def test_other_gloss_limits_are_two_lines():
    over = {
        "cover title": (f"# T\n^ {zen(24, BODY, 3)}\n", 2),
        "statement": (PREFIX + f"S\n^ {zen(24, BODY, 3)}\n", 4),
        "caption": (PREFIX + f"## H\n![x](icon:gear)\nC\n^ {zen(12, CAPTION, 3)}\n", 6),
        "column text": (PREFIX + f"## H\nA\n|||\nB\n^ {zen(13, COLUMN, 3)}\n", 7),
        "column bullet": (PREFIX + f"## H\n- a\n^ {zen(13, COLUMN - INDENT, 3)}\n|||\nB\n", 5),
        "table cell": (
            PREFIX
            + f"## H\n| a | b |\n|---|---|\n| 1 | 2 |\n^ | {zen(11, BODY / 2 - 0.2, 3)} | |\n",
            7,
        ),
    }
    for name, (text, line) in over.items():
        assert bad_lines(text) == [line], name


def test_bullets_total_height_includes_gloss():
    item = zen(24, BODY - INDENT, 2)
    gloss = zen(14, BODY - INDENT, 2)
    plain = PREFIX + "## H\n" + "".join(f"- {item}\n" for _ in range(3))
    deck(plain)  # 添え訳がなければ通る
    lines = ["## H"]
    for _ in range(3):
        lines += [f"- {item}", f"^ {gloss}"]
    got = problems(PREFIX + "\n".join(lines) + "\n")
    # 3 行目から ## H、4・5 が 1 つ目、6・7 が 2 つ目、8・9 が 3 つ目
    assert [line for line, _ in got] == [9]
    assert "枠の高さ" in got[0][1]


def test_two_column_bullets_height():
    item = zen(22, COLUMN - INDENT, 2)
    gloss = zen(13, COLUMN - INDENT, 2)
    plain = PREFIX + "## H\n" + "".join(f"- {item}\n" for _ in range(4)) + "|||\nB\n"
    deck(plain)
    lines = ["## H"]
    for _ in range(4):
        lines += [f"- {item}", f"^ {gloss}"]
    got = problems(PREFIX + "\n".join(lines) + "\n|||\nB\n")
    # 3 行目から ## H、4・5、6・7、8・9、10・11。4 つ目の項目は 10 行目
    assert [line for line, _ in got] == [10]


def test_two_column_right_bullets_height():
    item = zen(22, COLUMN - INDENT, 2)
    gloss = zen(13, COLUMN - INDENT, 2)
    lines = ["## H", "A", "|||"]
    for _ in range(4):
        lines += [f"- {item}", f"^ {gloss}"]
    # 3 行目から ## H、A、|||、6・7、8・9、10・11、12・13。4 つ目の項目は 12 行目
    assert bad_lines(PREFIX + "\n".join(lines) + "\n") == [12]


def table_with(gloss_rows: set[int]) -> tuple[str, dict[int, int]]:
    """3 列の表。gloss_rows は添え訳をつける行（0 が見出し行、1〜5 が本文）。
    戻り値は原稿と、行 → その添え訳の原稿の行番号。"""
    gloss = "^ | " + " | ".join([zen(11, BODY / 3 - 0.2, 2)] * 3) + " |"
    lines = ["## H"]  # 3 行目
    where: dict[int, int] = {}
    for r in range(6):
        lines.append("| a | b | c |" if r == 0 else "| 1 | 2 | 3 |")
        if r in gloss_rows:
            lines.append(gloss)
            where[r] = 2 + len(lines)
        if r == 0:
            lines.append("|---|---|---|")
    return PREFIX + "\n".join(lines) + "\n", where


def test_table_height_rejects_at_gloss_that_overflows():
    text, where = table_with({0, 1, 2, 5})
    assert bad_lines(text) == [where[5]]
    ok, _ = table_with({0, 1, 2})
    deck(ok)  # 5 行目の添え訳を除けば通る


def test_table_height_rejects_table_row_when_plain_already_overflows():
    # 2 行のセルの行は 0.85in。見出し + 本文 5 行 = 5.1in で、添え訳がなくても本文 5 行目で超える。
    cell = zen(18, BODY / 3 - 0.2, 2)
    head = f"## H\n| {cell} | b | c |\n|---|---|---|\n"
    rows = [f"| {cell} | b | c |" for _ in range(5)]
    plain = PREFIX + head + "\n".join(rows) + "\n"
    # 3 行目から ## H、4 見出し、5 区切り、6〜10 が本文。本文 5 行目は 10 行目
    assert bad_lines(plain) == [10]
    # 添え訳をつけても、添え訳を除いた高さで超える行の報告は表の行のまま
    rows[0] += "\n^ | x | y | z |"
    assert bad_lines(PREFIX + head + "\n".join(rows) + "\n") == [11]


def test_limits_fit_without_height_check():
    cover = f"# {zen(40, BODY, 2)}\n^ {zen(24, BODY, 2)}\n"
    for _ in range(3):
        cover += f"{zen(20, BODY, 1)}\n^ {zen(12, BODY, 1)}\n"
    deck(cover)
    deck(PREFIX + f"{zen(40, BODY, 3)}\n^ {zen(24, BODY, 2)}\n")
    deck(PREFIX + f"## H\n![x](icon:gear)\n{zen(20, CAPTION, 3)}\n^ {zen(12, CAPTION, 2)}\n")
    deck(PREFIX + f"## H\nA\n|||\n{zen(22, COLUMN, 3)}\n^ {zen(13, COLUMN, 2)}\n")


def test_build_cli_reports_path_line_reason(tmp_path, capsys):
    import build

    src = tmp_path / "gloss.md"
    src.write_text(PREFIX + f"## H\n- a\n^ {zen(14, BODY - INDENT, 3)}\n", encoding="utf-8")
    out = tmp_path / "gloss.pptx"
    assert build.main([str(src), "-o", str(out)]) == 1
    err = capsys.readouterr().err.splitlines()
    assert len(err) == 1
    prefix = f"{src}:5: "
    assert err[0].startswith(prefix)
    assert "上限は 2 行" in err[0][len(prefix) :]
    assert not out.exists()
