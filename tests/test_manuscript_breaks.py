"""改行 `<br>` の解析と拒否。delta spec「改行」「未対応の書式の拒否」。"""

from pathlib import Path

import pytest

from slidekit.manuscript import ManuscriptError, Statement, Table, parse

PREFIX = "# 題\n---\n"


def deck(text: str):
    return parse(text, Path(".")).slides


def problems(text: str) -> list[tuple[int, str]]:
    with pytest.raises(ManuscriptError) as e:
        parse(text, Path("."))
    return [(p.line, p.message) for p in e.value.problems]


def bad_lines(text: str) -> list[int]:
    return [line for line, _ in problems(text)]


def plain(t) -> str:
    return "".join(r.text for r in t)


# --- 書ける場所 ---


def test_statement_break_becomes_newline():
    s = deck(PREFIX + "来期は値上げせず、<br>品目を減らす。\n")[1]
    assert isinstance(s, Statement)
    assert plain(s.text) == "来期は値上げせず、\n品目を減らす。"


def test_table_cells_break_becomes_newline_in_header_and_body():
    s = deck(
        PREFIX + "## 比べる\n| 観点<br>名 | B |\n|---|---|\n| C: 集計基盤で実行<br>（提案） | x |\n"
    )[1]
    assert isinstance(s, Table)
    assert plain(s.header[0]) == "観点\n名"
    assert plain(s.rows[0][0]) == "C: 集計基盤で実行\n（提案）"
    assert plain(s.rows[0][1]) == "x"


def test_spaces_around_break_are_dropped():
    s = deck(PREFIX + "ア <br> イ\n")[1]
    assert plain(s.text) == "ア\nイ"


# --- 書けない場所 ---


@pytest.mark.parametrize(
    "text, line",
    [
        ("# 題<br>名\n", 1),
        ("# 題\nサブ<br>タイトル\n", 2),
        (PREFIX + "## 見出し<br>です\n- a\n", 3),
        (PREFIX + "## 見出し\n- a<br>b\n", 4),
        (PREFIX + "## 見出し\n- a\n^ あ<br>い\n", 5),
        (PREFIX + "## 見出し\n![図](x.png)\n説明<br>文\n", 5),
        (PREFIX + "## 見出し\n- a<br>b\n|||\n- c\n", 4),
        (PREFIX + "## 見出し\n- a\n|||\n文<br>章\n", 6),
        (PREFIX + "## 見出し\n| a | b |\n^ | あ<br>い | |\n|---|---|\n| c | d |\n", 5),
    ],
)
def test_break_outside_allowed_places_is_rejected(text, line):
    assert line in bad_lines(text)
    assert any("`<br>` は一言・補足・表のセルにだけ" in m for ln, m in problems(text) if ln == line)


@pytest.mark.parametrize("tag", ["<br/>", "<br />", "<BR>", "<Br>"])
def test_other_br_spellings_are_rejected_even_where_br_is_allowed(tag):
    text = PREFIX + f"一言{tag}二言\n"
    assert bad_lines(text) == [3]
    assert any("改行は `<br>` と書きます" in m for _, m in problems(text))


def test_other_br_spelling_in_a_table_cell_is_rejected():
    assert bad_lines(PREFIX + "## 表\n| a | b |\n|---|---|\n| x<br/>y | z |\n") == [6]


@pytest.mark.parametrize("statement", ["<br>後", "前<br>", "前<br><br>後", "前<br> <br>後"])
def test_leading_trailing_and_double_breaks_are_rejected(statement):
    text = PREFIX + statement + "\n"
    assert bad_lines(text) == [3]
    assert any("`<br>` の前後に文字が要ります" in m for _, m in problems(text))


def test_leading_break_in_a_table_cell_is_rejected():
    text = PREFIX + "## 表\n| a | b |\n|---|---|\n| <br>x | z |\n"
    assert bad_lines(text) == [6]


# --- 行数の判定 ---


def test_cell_with_a_break_counts_two_lines_and_is_accepted():
    assert isinstance(deck(PREFIX + "## 表\n| a | b |\n|---|---|\n| あ<br>い | z |\n")[1], Table)


def test_cell_with_two_breaks_counts_three_lines_and_is_rejected():
    text = PREFIX + "## 表\n| a | b |\n|---|---|\n| あ<br>い<br>う | z |\n"
    assert bad_lines(text) == [6]


def test_statement_lines_from_breaks_are_added():
    # 40pt で 1 行ずつの 4 部分は 4 行（上限 3 行）
    text = PREFIX + "あ<br>い<br>う<br>え\n"
    assert bad_lines(text) == [3]
    assert isinstance(deck(PREFIX + "あ<br>い<br>う\n")[1], Statement)
