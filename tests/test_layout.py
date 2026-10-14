import pytest

from slidekit.flow import FlowError, parse_flow
from slidekit.layout import (
    BOX_MIN_H,
    BOX_MIN_W,
    COL_GAP,
    FRAME_PAD,
    layout_flow,
)

EPS = 1e-6
MAX_W = 11.53
MAX_H = 4.9


def lay(text: str, max_w: float = MAX_W, max_h: float = MAX_H):
    return layout_flow(parse_flow(text), max_w, max_h)


def problems(text: str) -> list[tuple[int | None, str]]:
    with pytest.raises(FlowError) as e:
        lay(text)
    return [(p.line, p.message) for p in e.value.problems]


def box(d, name):
    return next(b for b in d.boxes if b.name == name)


def frame(d, label):
    return next(f for f in d.frames if f.label == label)


def close(a: float, b: float) -> bool:
    return abs(a - b) < EPS


# --- 箱の大きさ ---


def test_boxes_in_one_column_share_the_width_and_fit_the_longest_name():
    d = lay("| 店舗 |\n| あいうえおかきくけこ |\n")
    a, b = box(d, "店舗"), box(d, "あいうえおかきくけこ")
    assert close(a.w, b.w)
    assert close(b.w, 10 * 16 / 72 + 2 * 0.12)  # 全角 10 文字の名前が 1 行で入る


def test_short_names_use_the_minimum_size():
    d = lay("| 甲 |\n")
    assert close(box(d, "甲").w, BOX_MIN_W)
    assert close(box(d, "甲").h, BOX_MIN_H)


def test_box_height_grows_with_its_lines_and_is_shared_in_the_row():
    text = "| 甲 | 乙 |\n- 甲: 一\n- 甲: 二\n- 甲: 三\n- 甲: 四\n"
    d = lay(text)
    expected = (16 + 4 * 12) * 1.5 / 72 + 2 * 0.08
    assert close(box(d, "甲").h, expected)
    assert close(box(d, "乙").h, expected)


def test_spanning_box_covers_both_rows_from_top_to_bottom():
    d = lay("| 保存先 | 集計 a |\n| 保存先 | 集計 b |\n")
    s, a, b = box(d, "保存先"), box(d, "集計 a"), box(d, "集計 b")
    assert close(s.y, a.y)
    assert close(s.y + s.h, b.y + b.h)


def test_tall_spanning_box_stretches_the_rows_it_spans():
    lines = "".join(f"- 保存先: 行{i}\n" for i in range(4))
    d = lay("| 保存先 | 甲 |\n| 保存先 | 乙 |\n" + lines)
    s = box(d, "保存先")
    assert s.h >= (16 + 4 * 12) * 1.5 / 72 + 2 * 0.08 - EPS
    assert close(box(d, "甲").h, box(d, "乙").h)


def test_line_wider_than_the_box_maximum_is_rejected_with_line_and_box_name():
    text = "| 甲 |\n- 甲: " + "あ" * 18 + "\n"
    got = problems(text)
    assert [line for line, _ in got] == [2]
    assert "甲" in got[0][1]


def test_name_wider_than_the_box_maximum_is_rejected_at_the_placement_line():
    name = "あ" * 14  # 16pt で 3.11 インチ
    got = problems(f"| {name} |\n")
    assert [line for line, _ in got] == [1]


# --- 範囲の枠 ---

NESTED = "| 受付 | 保存先 | 集計 |\n[社内] 受付, 保存先, 集計\n[部門] 受付, 保存先\n"


def test_nested_frame_lies_inside_the_outer_frame_without_touching():
    d = lay(NESTED)
    outer, inner = frame(d, "社内"), frame(d, "部門")
    assert inner.x - outer.x >= FRAME_PAD - EPS
    assert inner.y - outer.y >= FRAME_PAD - EPS
    assert (outer.y + outer.h) - (inner.y + inner.h) >= FRAME_PAD - EPS
    # 共通の左上の箱から、内側の枠は FRAME_PAD、外側の枠は 2 段分離れる
    a = box(d, "受付")
    assert close(a.x - inner.x, FRAME_PAD)
    assert close(a.x - outer.x, 2 * FRAME_PAD)


def test_frame_label_sits_in_the_top_left_corner():
    d = lay("| 甲 |\n[社内] 甲\n")
    f = frame(d, "社内")
    assert close(f.label_x, f.x + 0.1)
    assert close(f.label_y, f.y + 0.05)


def test_two_side_by_side_frames_leave_col_gap_plus_two_pads_between_boxes():
    text = "| a | b | c | d | e |\n[送る側] a, b, c\n[受ける側] d, e\n"
    d = lay(text)
    c, dd = box(d, "c"), box(d, "d")
    assert close(dd.x - (c.x + c.w), COL_GAP + 2 * FRAME_PAD)
    left, right = frame(d, "送る側"), frame(d, "受ける側")
    assert close(right.x - (left.x + left.w), COL_GAP)


def test_frame_rect_excludes_the_label_band_from_box_rows():
    d = lay("| 甲 |\n[社内] 甲\n")
    f, b = frame(d, "社内"), box(d, "甲")
    assert close(b.y - f.y, FRAME_PAD + 0.3)


def test_non_member_box_inside_a_frame_is_rejected_with_frame_line_and_name():
    text = "| 社内 a | 取引先 a | 社内 b |\n[社内] 社内 a, 社内 b\n"
    got = problems(text)
    assert [line for line, _ in got] == [2]
    assert "取引先 a" in got[0][1]


def test_partially_overlapping_frames_are_rejected_at_the_second_frame():
    text = "| 甲 | 乙 | 丙 |\n[A] 甲, 乙\n[B] 乙, 丙\n"
    assert [line for line, _ in problems(text)] == [3]


def test_frame_label_wider_than_the_frame_is_rejected():
    text = "| 甲 |\n[" + "あ" * 12 + "] 甲\n"  # 12pt で 2.0 > 1.2 - 0.2 + 2*0.15
    assert [line for line, _ in problems(text)] == [2]
