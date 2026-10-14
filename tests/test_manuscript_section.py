"""中扉の解析と拒否。delta spec「中扉レイアウト」「原稿の区切りと表紙」「添え訳の書式」、design D5。"""

from pathlib import Path

import pytest

from slidekit.fit import line_count
from slidekit.manuscript import Cover, ManuscriptError, Section, Statement, parse

PREFIX = "# 題\n---\n本編\n---\n"
BODY = 11.53


def deck(text: str):
    return parse(text, Path(".")).slides


def problems(text: str) -> list[tuple[int, str]]:
    with pytest.raises(ManuscriptError) as e:
        parse(text, Path("."))
    return [(p.line, p.message) for p in e.value.problems]


def zen(pt: float, width: float, lines: int) -> str:
    n = 1 if lines == 1 else int(width * 72 / pt * (lines - 1)) + 1
    text = "あ" * n
    assert line_count(text, pt, width) == lines
    return text


# --- 解析 ---


def test_h1_only_slide_after_the_cover_is_a_section():
    slides = deck(PREFIX + "# 補足資料\n")
    assert isinstance(slides[0], Cover)
    assert slides[2] == Section("補足資料")
    assert slides[2].title_gloss is None


def test_section_gloss_goes_to_title_gloss():
    s = deck(PREFIX + "# 補足資料\n^ Appendix\n")[2]
    assert s == Section("補足資料", "Appendix")


def test_slide_after_a_section_is_parsed():
    slides = deck(PREFIX + "# 補足資料\n---\n続き\n")
    assert isinstance(slides[2], Section)
    assert isinstance(slides[3], Statement)


def test_section_title_with_two_lines_at_40pt_is_accepted():
    assert isinstance(deck(PREFIX + "# " + zen(40, BODY, 2) + "\n")[2], Section)


def test_cover_is_unchanged():
    assert isinstance(deck("# 題\n副題\n")[0], Cover)


# --- 拒否 ---


@pytest.mark.parametrize("other", ["- 項目", "## 見出し", "文", "| a | b |"])
def test_h1_mixed_with_another_line_is_rejected_at_the_h1_line(other):
    got = problems("# 題\n---\n# 補足資料\n" + other + "\n")
    assert got[0][0] == 3
    assert "中扉は `# タイトル` の 1 行だけです" in got[0][1]
    assert "見出しは `## `" in got[0][1]
    assert [ln for ln, _ in got] == [3]


def test_h1_after_another_line_is_rejected_at_the_h1_line():
    got = problems("# 題\n---\n文\n# 補足資料\n")
    assert [ln for ln, _ in got] == [4]


def test_two_h1_lines_are_rejected():
    got = problems("# 題\n---\n# 一\n# 二\n")
    assert [ln for ln, _ in got] == [3, 4]


def test_empty_title_is_rejected():
    got = problems("# 題\n---\n# \n")
    assert [ln for ln, _ in got] == [3]
    assert "空" in got[0][1]


def test_title_with_three_lines_at_40pt_is_rejected():
    got = problems("# 題\n---\n# " + zen(40, BODY, 3) + "\n")
    assert [ln for ln, _ in got] == [3]
    assert "40pt" in got[0][1]


def test_section_gloss_with_three_lines_is_rejected():
    got = problems("# 題\n---\n# 補足資料\n^ " + zen(24, BODY, 3) + "\n")
    assert [ln for ln, _ in got] == [4]
