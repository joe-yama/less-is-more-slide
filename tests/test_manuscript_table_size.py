"""表の文字の大きさ（18pt → 16pt）の判定。delta spec「表の文字の大きさ」「添え訳の文字」、design D6。"""

from pathlib import Path

import pytest

from slidekit import fit
from slidekit.manuscript import ManuscriptError, Table, parse

PREFIX = "# 題\n---\n## 比べる\n"
COLS = 4
CELL_W = 11.53 / COLS - 0.2


def deck(text: str):
    return parse(text, Path(".")).slides


def problems(text: str) -> list[tuple[int, str]]:
    with pytest.raises(ManuscriptError) as e:
        parse(text, Path("."))
    return [(p.line, p.message) for p in e.value.problems]


def lines_at(text: str, pt: float) -> int:
    return fit.line_count(text, pt, CELL_W)


def cell(chars: int, at_18: int, at_16: int) -> str:
    """全角 chars 字。18pt と 16pt の行数を確かめて返す（fit.line_count で数える）。"""
    text = "あ" * chars
    assert (lines_at(text, 18), lines_at(text, 16)) == (at_18, at_16)
    return text


def table(*rows: list[str]) -> str:
    """見出し行（rows[0]）、区切り行、本文の行から表の原稿を作る。"""
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return PREFIX + "\n".join(out) + "\n"


def test_constant():
    assert fit.PT_CELL_SMALL == 16


def test_table_that_fits_at_18pt_stays_at_18pt():
    t = deck(table(["観点", "A", "B", "C"], ["速さ", "1", "2", "3"]))[1]
    assert isinstance(t, Table)
    assert t.pt == 18


def test_three_line_cell_at_18pt_that_is_two_lines_at_16pt_makes_a_16pt_table():
    t = deck(table(["観点", "A", "B", "C"], ["速さ", cell(22, 3, 2), "2", "3"]))[1]
    assert isinstance(t, Table)
    assert t.pt == 16


def test_table_too_tall_at_18pt_but_fitting_at_16pt_is_16pt():
    two = cell(15, 2, 2)
    rows = [[two] * COLS] * 6  # 見出し行 + 本文 5 行、どのセルも 2 行
    assert 6 * fit.table_row_height_in(2, 18) > fit.BODY_BOX_H
    assert 6 * fit.table_row_height_in(2, 16) <= fit.BODY_BOX_H
    t = deck(table(*rows))[1]
    assert isinstance(t, Table)
    assert t.pt == 16


def test_three_line_cell_at_16pt_is_rejected_with_16pt_reason_only():
    long = cell(30, 3, 3)
    got = problems(table(["観点", "A", "B", "C"], ["速さ", "1", "2", "3"], ["x", long, "2", "3"]))
    assert [ln for ln, _ in got] == [7]
    assert "16pt" in got[0][1]
    assert "3 行" in got[0][1]
    assert "18pt" not in got[0][1]


def test_gloss_of_a_16pt_table_is_judged_at_10pt():
    # 37 字: 11pt（18pt の表）では 3 行、10pt（16pt の表）では 2 行
    gloss = "あ" * 37
    assert (lines_at(gloss, 11), lines_at(gloss, 10)) == (3, 2)
    forcing = cell(22, 3, 2)
    text = table(["観点", "A", "B", "C"], ["速さ", forcing, "2", "3"])
    text += "^ | | | " + gloss + " | |\n"
    t = deck(text)[1]
    assert isinstance(t, Table)
    assert t.pt == 16
    assert t.row_glosses[0][2] == gloss


def test_gloss_with_three_lines_at_10pt_is_rejected_at_its_line():
    gloss = "あ" * 40
    assert lines_at(gloss, 10) == 3
    forcing = cell(22, 3, 2)
    text = table(["観点", "A", "B", "C"], ["速さ", forcing, "2", "3"])
    text += "^ | | | " + gloss + " | |\n"
    got = problems(text)
    assert [ln for ln, _ in got] == [7]
    assert "10pt" in got[0][1]
    assert "18pt" not in got[0][1]


def test_size_independent_violations_are_reported_once():
    # 5 列（列数の違反）で、どの大きさでも 3 行になるセルがある
    long = "あ" * 60
    text = table(["a", "b", "c", "d", "e"], [long, "1", "2", "3", "4"])
    got = problems(text)
    column_errors = [m for _, m in got if "表の列は" in m]
    assert len(column_errors) == 1
    assert sum(1 for ln, _ in got if ln == 6) == 1  # セルの行数の違反も 1 回だけ（16pt の分）
    assert all("18pt" not in m for _, m in got)


def test_row_with_wrong_column_count_is_reported_once():
    text = table(["観点", "A", "B", "C"], ["x", cell(22, 3, 2), "2"])
    got = problems(text)
    assert [m for _, m in got].count("行の列数 3 が見出し行の 4 と違います") == 1
