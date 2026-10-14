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


# --- 矢印の経路 ---


def cx(b) -> float:
    return b.x + b.w / 2


def cy(b) -> float:
    return b.y + b.h / 2


def top_of_all(d) -> float:
    return min([b.y for b in d.boxes] + [f.y for f in d.frames])


def bottom_of_all(d) -> float:
    return max([b.y + b.h for b in d.boxes] + [f.y + f.h for f in d.frames])


def test_same_row_arrow_is_horizontal_between_facing_edges():
    d = lay("| A | B |\nA -> B\n")
    a, b = box(d, "A"), box(d, "B")
    (p, q) = d.arrows[0].points
    assert close(p[0], a.x + a.w) and close(q[0], b.x)
    assert close(p[1], cy(a)) and close(q[1], cy(a))


def test_same_column_arrow_is_vertical_between_bottom_and_top_edges():
    d = lay("| A |\n| B |\nA -> B\n")
    a, b = box(d, "A"), box(d, "B")
    (p, q) = d.arrows[0].points
    assert close(p[0], cx(a)) and close(q[0], cx(b))
    assert close(p[1], a.y + a.h) and close(q[1], b.y)


def test_different_row_and_column_arrow_is_a_diagonal_between_side_edges():
    d = lay("| A | |\n| | C |\nA -> C\n")
    a, c = box(d, "A"), box(d, "C")
    (p, q) = d.arrows[0].points
    assert close(p[0], a.x + a.w) and close(p[1], cy(a))
    assert close(q[0], c.x) and close(q[1], cy(c))
    assert q[1] > p[1] + EPS


def test_arrows_fanning_out_from_one_box_start_at_the_same_point():
    text = "| | B1 |\n| A | B2 |\n| | B3 |\nA -> B1\nA -> B2\nA -> B3\n"
    d = lay(text)
    a = box(d, "A")
    starts = {(round(p.points[0][0], 6), round(p.points[0][1], 6)) for p in d.arrows}
    assert starts == {(round(a.x + a.w, 6), round(cy(a), 6))}
    ys = [p.points[-1][1] for p in d.arrows]
    assert close(ys[1], cy(a)) and ys[0] < ys[1] < ys[2]


def test_arrow_flags_are_carried_over():
    d = lay("| A | B |\nA -> B (強調, 破線)\n")
    assert d.arrows[0].emphasis and d.arrows[0].dashed


def test_over_route_is_four_points_with_the_horizontal_part_above_everything():
    d = lay("| A | B |\n[社内] A\nA -> B (上回り)\n")
    a, b = box(d, "A"), box(d, "B")
    pts = d.arrows[0].points
    assert len(pts) == 4
    assert close(pts[0][0], cx(a)) and close(pts[0][1], a.y)
    assert close(pts[1][0], cx(a)) and close(pts[2][0], cx(b))
    assert close(pts[1][1], pts[2][1])
    assert pts[1][1] < top_of_all(d) - EPS
    assert close(pts[3][0], cx(b)) and close(pts[3][1], b.y)


def test_two_over_routes_use_separate_lanes_both_above_everything():
    d = lay("| A | B | C | D |\nA -> B (上回り)\nC -> D (上回り)\n")
    y1, y2 = d.arrows[0].points[1][1], d.arrows[1].points[1][1]
    assert abs(y1 - y2) > 0.05
    assert max(y1, y2) < top_of_all(d) - EPS


def test_under_route_goes_below_everything():
    d = lay("| A | B |\n[社内] A\nA -> B (下回り)\n")
    a, b = box(d, "A"), box(d, "B")
    pts = d.arrows[0].points
    assert len(pts) == 4
    assert close(pts[0][1], a.y + a.h) and close(pts[3][1], b.y + b.h)
    assert pts[1][1] > bottom_of_all(d) + EPS
    assert close(pts[1][1], pts[2][1])


def test_straight_arrow_across_a_box_is_rejected_with_a_hint():
    got = problems("| A | B | C |\nA -> C\n")
    assert [line for line, _ in got] == [2]
    assert "B" in got[0][1]
    assert "上回り" in got[0][1] or "下回り" in got[0][1]


def test_diagonal_arrow_across_a_box_is_rejected():
    got = problems("| A | | |\n| | B | |\n| | | C |\nA -> C\n")
    assert [line for line, _ in got] == [4]


def test_round_route_between_boxes_of_the_same_column_is_rejected():
    got = problems("| A |\n| B |\nA -> B (上回り)\n")
    assert [line for line, _ in got] == [3]


def test_second_round_route_from_the_same_edge_is_rejected():
    got = problems("| A | B | C |\nA -> B (上回り)\nA -> C (上回り)\n")
    assert [line for line, _ in got] == [3]


def test_round_route_through_another_box_is_rejected():
    got = problems("| X | |\n| A | B |\nA -> B (上回り)\n")
    assert [line for line, _ in got] == [3]
    assert "X" in got[0][1]


def test_route_through_a_frame_label_is_rejected():
    text = "| A | B |\n[社内システム] A\nA -> B (上回り)\n"
    got = problems(text)
    assert [line for line, _ in got] == [3]
    assert "社内システム" in got[0][1]


# --- ラベルと × の位置、図の大きさ ---

LM = 0.1  # LABEL_MARGIN
CROSS = 0.45  # CROSS_SIZE
LABEL_H = 12 * 1.5 / 72  # 12pt の 1 行


def label_of(d, text):
    return next(label for label in d.labels if label.lines[0] == text)


def test_horizontal_label_is_below_the_line_and_between_the_boxes():
    d = lay("| A | B |\nA -> B: 直接参照\n")
    a, b = box(d, "A"), box(d, "B")
    lb = label_of(d, "直接参照")
    assert lb.x >= a.x + a.w - EPS and lb.x + lb.w <= b.x + EPS
    assert close(lb.y, cy(a) + LM)
    assert close(lb.x + lb.w / 2, (a.x + a.w + b.x) / 2)
    assert close(lb.h, LABEL_H)


def test_gap_between_columns_widens_to_fit_a_two_inch_label():
    d = lay("| A | B |\nA -> B: " + "あ" * 12 + "\n")
    a, b = box(d, "A"), box(d, "B")
    assert b.x - (a.x + a.w) >= 2.0 + 2 * LM - EPS
    lb = d.labels[0]
    assert close(lb.w, 2.0)
    assert lb.x >= a.x + a.w - EPS and lb.x + lb.w <= b.x + EPS


def test_vertical_label_is_right_of_the_line_and_the_row_gap_widens():
    d = lay("| A |\n| B |\nA -> B: 受け渡し\n")
    a, b = box(d, "A"), box(d, "B")
    lb = d.labels[0]
    assert close(lb.x, cx(a) + LM)
    assert close(lb.y + lb.h / 2, (a.y + a.h + b.y) / 2)
    assert close(b.y - (a.y + a.h), max(0.35, LABEL_H + 2 * LM))


def test_diagonal_label_goes_below_the_line_first():
    d = lay("| A | |\n| | C |\nA -> C: 渡す\n")
    (p, q) = d.arrows[0].points
    ref = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    lb = d.labels[0]
    # 右下がり: ラベルの右上の角が基準点の LABEL_MARGIN 下
    assert close(lb.x + lb.w, ref[0]) and close(lb.y, ref[1] + LM)


def test_diagonal_label_goes_above_when_the_lower_side_is_blocked():
    text = "| A | |\n| D | C |\nA -> C: 一行目<br>二行目\nD -> C\n"
    d = lay(text)
    (p, q) = d.arrows[0].points
    ref = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    lb = d.labels[0]
    # 右下がり・上側: ラベルの左下の角が基準点の LABEL_MARGIN 上
    assert close(lb.x, ref[0]) and close(lb.y + lb.h, ref[1] - LM)


def test_diagonal_label_with_both_sides_blocked_is_rejected_at_the_arrow_line():
    text = "| A | B |\n| D | C |\nA -> C: 渡す\nD -> B\n"
    assert [line for line, _ in problems(text)] == [3]


def test_cross_sits_at_the_middle_of_the_horizontal_segment_with_its_text_outside():
    d = lay("| A | B |\nA -> B (強調, 下回り): × 直接の参照はやめる\n")
    pts = d.arrows[0].points
    mid_x, lane = (pts[1][0] + pts[2][0]) / 2, pts[1][1]
    x = d.crosses[0]
    assert close(x.x + x.w / 2, mid_x) and close(x.y + x.h / 2, lane)
    assert close(x.w, CROSS) and close(x.h, CROSS)
    t = d.labels[0]
    assert t.emphasis and t.x >= x.x + x.w - EPS
    assert t.y >= lane + LM - EPS  # 下回りの文は下側


def test_cross_text_of_an_over_route_is_above_the_lane():
    d = lay("| A | B |\nA -> B (強調, 上回り): × やめる\n")
    lane = d.arrows[0].points[1][1]
    t = d.labels[0]
    assert t.y + t.h <= lane - LM + EPS


def test_round_route_label_is_outside_the_horizontal_segment_and_centered():
    d = lay("| A | B |\nA -> B (上回り): 迂回\n")
    pts = d.arrows[0].points
    lb = d.labels[0]
    assert close(lb.y + lb.h, pts[1][1] - LM)
    assert close(lb.x + lb.w / 2, (pts[1][0] + pts[2][0]) / 2)


def test_origin_is_the_top_left_of_everything():
    d = lay("| A | B |\nA -> B (強調, 上回り): × やめる\n")
    xs = [b.x for b in d.boxes] + [p[0] for a in d.arrows for p in a.points]
    ys = [b.y for b in d.boxes] + [p[1] for a in d.arrows for p in a.points]
    ys += [lb.y for lb in d.labels] + [c.y for c in d.crosses]
    assert close(min(xs), 0.0) and close(min(ys), 0.0)
    right = max(b.x + b.w for b in d.boxes)
    assert d.width >= right - EPS
    assert d.height >= max(b.y + b.h for b in d.boxes) - EPS


def test_diagram_wider_than_max_w_is_rejected_without_a_line_number():
    text = "| " + " | ".join("ABCDEFGHI") + " |\n"
    got = problems(text)
    assert [line for line, _ in got] == [None]
    assert "11.53" in got[0][1]


def test_diagram_taller_than_max_h_is_rejected_without_a_line_number():
    text = "".join(f"| {c} |\n" for c in "ABCDEFG")
    got = problems(text)
    assert [line for line, _ in got] == [None]
    assert "4.9" in got[0][1]


def test_max_w_applies_to_the_whole_diagram():
    text = "| A | B | C |\n"
    lay(text, max_w=4.81)  # 3 列 × 1.2 + 間隔 2 × 0.6 = 4.8
    with pytest.raises(FlowError):
        lay(text, max_w=4.79)


# 設計の対話の図 1〜7（design.md「7 つの図は spec の Scenario から組み立てる」）。
# 6.1 が examples/design-review/*.flow にそのまま写せる形で書く。
FIG1 = """\
| 受付 API | 保存先 | 集計基盤 | 取引先 a |
| | | | 取引先 b |
[社内] 受付 API, 保存先, 集計基盤
[部門 A] 受付 API, 保存先
受付 API -> 保存先
保存先 -> 集計基盤
集計基盤 -> 取引先 a (強調)
集計基盤 -> 取引先 b (強調): ここで社外に渡る
"""
FIG2 = """\
| | 注文 1 |
| 受付 | 注文 2 |
| | 注文 3 |
受付 -> 注文 1: 新規
受付 -> 注文 2
受付 -> 注文 3: 取消
"""
FIG3 = """\
| 保存先 | 集計 a |
| 保存先 | 集計 b |
保存先 -> 集計 a
保存先 -> 集計 b
"""
FIG4 = """\
| 店舗 | 受付 | 検証 | 取込 | 集計 |
[送る側] 店舗, 受付, 検証
[受ける側] 取込, 集計
店舗 -> 受付
受付 -> 検証
検証 -> 取込: 送信
取込 -> 集計
"""
FIG5_LEFT = """\
| 受付 | 保存先 | 集計 |
[今の形] 受付, 保存先, 集計
受付 -> 保存先
保存先 -> 集計
"""
FIG5_RIGHT = """\
| 受付 | キュー | 集計 |
[案の形] 受付, キュー, 集計
受付 -> キュー: 非同期
キュー -> 集計
"""
FIG6 = """\
| 取込 | 変換 | 外部 |
取込 -> 変換
変換 -> 外部
取込 -> 外部 (強調, 破線, 下回り): × 直接の参照はやめる
外部 -> 取込 (上回り): 結果を返す
"""
FIG7 = """\
| 受付 | 保存先 |
- 保存先: key=V1/
- 保存先: **key=V/**
- 保存先: key=V3/
- 保存先: …
受付 -> 保存先
"""


@pytest.mark.parametrize("text", [FIG1, FIG2, FIG3, FIG4, FIG6, FIG7])
def test_design_dialogue_figures_fit_the_full_width(text):
    d = lay(text, max_w=11.53, max_h=4.9)
    assert d.width <= 11.53 and d.height <= 4.9


@pytest.mark.parametrize("text", [FIG5_LEFT, FIG5_RIGHT])
def test_design_dialogue_comparison_figures_fit_a_column(text):
    d = lay(text, max_w=5.5, max_h=4.9)
    assert d.width <= 5.5 and d.height <= 4.9


def test_cross_on_a_straight_horizontal_arrow_widens_the_gap_and_fits():
    d = lay("| A | B |\nA -> B (強調): × 使わない\n")
    a, b = box(d, "A"), box(d, "B")
    x, t = d.crosses[0], d.labels[0]
    mid = (a.x + a.w + b.x) / 2
    assert close(x.x + x.w / 2, mid) and close(x.y + x.h / 2, cy(a))
    assert t.x >= x.x + x.w - EPS  # 文は × 印の右
    assert t.x + t.w <= b.x + EPS  # 終点の箱に掛からない


def test_cross_on_a_horizontal_arrow_from_a_row_spanning_box_fits():
    d = lay("| A | X |\n| A | B |\n| A | Y |\nA -> B (強調): × 使わない\n")
    b = box(d, "B")
    x, t = d.crosses[0], d.labels[0]
    assert close(x.y + x.h / 2, cy(b))
    assert t.x >= x.x + x.w - EPS and t.x + t.w <= b.x + EPS
