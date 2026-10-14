"""一言の補足の解析と拒否。delta spec「一言レイアウト」「添え訳の書式」、design D4。"""

from pathlib import Path

import pytest

from slidekit import fit
from slidekit.fit import STATEMENT_BOX_H, gloss_pt, line_count, text_height_in
from slidekit.manuscript import ManuscriptError, Run, Statement, parse

PREFIX = "# 題\n---\n"
BODY = 11.53


def deck(text: str):
    return parse(text, Path(".")).slides


def problems(text: str) -> list[tuple[int, str]]:
    with pytest.raises(ManuscriptError) as e:
        parse(text, Path("."))
    return [(p.line, p.message) for p in e.value.problems]


def bad_lines(text: str) -> list[int]:
    return [line for line, _ in problems(text)]


def zen(pt: float, width: float, lines: int) -> str:
    n = 1 if lines == 1 else int(width * 72 / pt * (lines - 1)) + 1
    text = "あ" * n
    assert line_count(text, pt, width) == lines
    return text


def plain(t) -> str:
    return "".join(r.text for r in t)


def test_constants():
    assert fit.PT_STATEMENT_NOTE == 24
    assert fit.STATEMENT_NOTE_GAP_PT == 12
    assert STATEMENT_BOX_H == 6.3


# --- 解析 ---


def test_statement_without_notes_has_empty_notes():
    s = deck(PREFIX + "一言\n")[1]
    assert isinstance(s, Statement)
    assert s.notes == []
    assert s.note_glosses == []


def test_one_note_with_emphasis():
    s = deck(PREFIX + "結論\n費用は **3 案** で最小。\n")[1]
    assert isinstance(s, Statement)
    assert plain(s.text) == "結論"
    assert len(s.notes) == 1
    assert s.notes[0] == (Run("費用は "), Run("3 案", emphasis=True), Run(" で最小。"))
    assert s.note_glosses == [None]


def test_two_notes():
    s = deck(PREFIX + "結論\n理由 1\n理由 2\n")[1]
    assert [plain(n) for n in s.notes] == ["理由 1", "理由 2"]
    assert s.note_glosses == [None, None]


def test_note_break_becomes_newline():
    s = deck(PREFIX + "結論\n理由<br>その 2\n")[1]
    assert plain(s.notes[0]) == "理由\nその 2"


def test_note_glosses_go_to_note_glosses():
    s = deck(PREFIX + "結論\n^ Conclusion\n理由 1\n理由 2\n^ Reason 2\n")[1]
    assert s.gloss == "Conclusion"
    assert s.note_glosses == [None, "Reason 2"]


# --- 拒否 ---


def test_third_note_is_rejected_at_its_line():
    got = problems(PREFIX + "結論\n補足 1\n補足 2\n補足 3\n")
    assert [ln for ln, _ in got] == [6]
    assert "補足は 2 行まで" in got[0][1]


def test_note_with_three_lines_at_24pt_is_rejected():
    got = problems(PREFIX + "結論\n" + zen(24, BODY, 3) + "\n")
    assert [ln for ln, _ in got] == [4]
    assert "24pt" in got[0][1]


def test_note_with_two_lines_at_24pt_is_accepted():
    assert isinstance(deck(PREFIX + "結論\n" + zen(24, BODY, 2) + "\n")[1], Statement)


def test_note_gloss_with_three_lines_at_14pt_is_rejected():
    got = problems(PREFIX + "結論\n補足\n^ " + zen(14, BODY, 3) + "\n")
    assert [ln for ln, _ in got] == [5]
    assert "14pt" in got[0][1]


def test_note_gloss_with_two_lines_at_14pt_is_accepted():
    s = deck(PREFIX + "結論\n補足\n^ " + zen(14, BODY, 2) + "\n")[1]
    assert isinstance(s, Statement)


@pytest.mark.parametrize("line", ["- 項目", "| a | b |", "![図](x.png)", "## 見出し"])
def test_note_that_is_not_a_sentence_is_rejected(line):
    assert bad_lines(PREFIX + f"結論\n{line}\n") == [4]


def test_stack_taller_than_the_box_is_rejected_at_the_first_paragraph_over():
    three = zen(40, BODY, 3)
    two24 = zen(24, BODY, 2)
    g24 = zen(24, BODY, 2)
    g14 = zen(14, BODY, 2)
    text = PREFIX + f"{three}\n^ {g24}\n{two24}\n^ {g14}\n{two24}\n^ {g14}\n"
    # 一言 2.5 + 添え訳 1.0 + 補足 1(0.167+1.0) + 添え訳 0.583 = 5.25。2 つ目の補足で 6.3 を超える
    first = 2.5 + text_height_in(2, gloss_pt(40))
    assert first + 12 / 72 + text_height_in(2, 24) + text_height_in(2, 14) < STATEMENT_BOX_H
    assert first + 2 * (12 / 72 + text_height_in(2, 24)) + text_height_in(2, 14) > STATEMENT_BOX_H
    got = problems(text)
    # 行: 3 一言、4 添え訳、5 補足 1、6 添え訳、7 補足 2、8 添え訳
    assert [ln for ln, _ in got] == [7]
    assert "6.3" in got[0][1]
