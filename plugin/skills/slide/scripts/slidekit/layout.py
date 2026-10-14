"""構成図の配置の計算（design.md D3〜D7）。座標はインチで、判定と描画が同じ結果を使う。"""

from dataclasses import dataclass, field

from slidekit.fit import (
    PT_BOX_LINE,
    PT_BOX_NAME,
    PT_FLOW_LABEL,
    text_height_in,
    text_width_em,
)
from slidekit.flow import BoxSpec, FlowError, FlowProblem, FlowSpec, GroupSpec
from slidekit.inline import Text

BOX_PAD_X = 0.12
BOX_PAD_Y = 0.08
BOX_MIN_W = 1.2
BOX_MAX_W = 3.0
BOX_MIN_H = 0.6
COL_GAP = 0.6
ROW_GAP = 0.35
FRAME_PAD = 0.15
FRAME_LABEL_H = 0.3
LABEL_MARGIN = 0.1
LANE_GAP = 0.3
CROSS_SIZE = 0.45
NOTE_GAP = 0.3

FRAME_LABEL_DX = 0.1
FRAME_LABEL_DY = 0.05
FRAME_LABEL_SLACK = 0.2  # 枠のラベルが入る幅は、枠の幅からこれを引いた幅
EPS = 1e-6


@dataclass
class PlacedBox:
    x: float
    y: float
    w: float
    h: float
    name: str
    lines: list[Text]


@dataclass
class PlacedFrame:
    x: float
    y: float
    w: float
    h: float
    label: str
    label_x: float
    label_y: float


@dataclass
class PlacedArrow:
    points: list[tuple[float, float]]
    emphasis: bool
    dashed: bool


@dataclass
class PlacedLabel:
    x: float
    y: float
    w: float
    h: float
    lines: list[str]
    emphasis: bool


@dataclass
class PlacedCross:
    x: float
    y: float
    w: float
    h: float


@dataclass
class Diagram:
    width: float
    height: float
    boxes: list[PlacedBox] = field(default_factory=list)
    frames: list[PlacedFrame] = field(default_factory=list)
    arrows: list[PlacedArrow] = field(default_factory=list)
    labels: list[PlacedLabel] = field(default_factory=list)
    crosses: list[PlacedCross] = field(default_factory=list)


def _width_in(text: str, pt: float) -> float:
    return text_width_em(text) * pt / 72


def _plain(line: Text) -> str:
    return "".join(r.text for r in line)


@dataclass
class _Cells:
    """枠のメンバーを囲むセルの長方形（両端を含む）。"""

    col0: int
    col1: int
    row0: int
    row1: int


def _group_cells(g: GroupSpec, by_name: dict[str, BoxSpec]) -> _Cells:
    bs = [by_name[m] for m in g.members]
    return _Cells(
        min(b.col for b in bs),
        max(b.col for b in bs),
        min(b.row_top for b in bs),
        max(b.row_bottom for b in bs),
    )


def _check_groups(spec: FlowSpec, by_name: dict[str, BoxSpec]) -> list[FlowProblem]:
    out: list[FlowProblem] = []
    cells = [_group_cells(g, by_name) for g in spec.groups]
    for g, c in zip(spec.groups, cells, strict=True):
        members = set(g.members)
        for b in spec.boxes:
            if b.name in members:
                continue
            if c.col0 <= b.col <= c.col1 and b.row_top <= c.row1 and b.row_bottom >= c.row0:
                out.append(
                    FlowProblem(
                        g.line_no,
                        f"範囲の枠 `{g.label}` の長方形に、含めない箱 `{b.name}` が入ります",
                    )
                )
    for j, gj in enumerate(spec.groups):
        sj = set(gj.members)
        for gi in spec.groups[:j]:
            si = set(gi.members)
            if si & sj and not (si <= sj or sj <= si):
                out.append(
                    FlowProblem(
                        gj.line_no,
                        f"範囲の枠 `{gj.label}` が `{gi.label}` と一部だけ重なります。"
                        "入れ子にするか、共通の箱をなくしてください",
                    )
                )
    return out


def _edge(c: _Cells, k: int) -> int:
    return (c.col0, c.col1, c.row0, c.row1)[k]


def _depths(spec: FlowSpec, cells: list[_Cells]) -> list[tuple[int, int, int, int]]:
    """枠ごとの（左・右・上・下）の辺の入れ子の深さ（D4 の 2）。"""
    sets = [set(g.members) for g in spec.groups]
    n = len(spec.groups)

    def inside(i: int, j: int) -> bool:
        """枠 i が枠 j の内側（メンバーが j に含まれる。同じ集合は後に書いた方を外側）。"""
        if i == j:
            return False
        if sets[i] == sets[j]:
            return i < j
        return sets[i] < sets[j]

    result: list[list[int]] = [[1] * 4 for _ in range(n)]
    order = sorted(range(n), key=lambda i: len(sets[i]))
    for k in range(4):
        for j in order:  # 内側の枠（メンバーが少ない）から先に決める
            best = 0
            for i in range(n):
                if inside(i, j) and _edge(cells[i], k) == _edge(cells[j], k):
                    best = max(best, result[i][k])
            result[j][k] = 1 + best
    return [tuple(r) for r in result]  # type: ignore[misc]


def layout_flow(spec: FlowSpec, max_w: float, max_h: float) -> Diagram:
    by_name = {b.name: b for b in spec.boxes}
    problems = _check_groups(spec, by_name)

    # 1. 箱の幅と列の幅
    content_w: dict[str, float] = {}
    for b in spec.boxes:
        w = _width_in(b.name, PT_BOX_NAME)
        if w + 2 * BOX_PAD_X > BOX_MAX_W + EPS:
            problems.append(
                FlowProblem(
                    b.line_no,
                    f"箱 `{b.name}` の名前が、箱の幅の上限 {BOX_MAX_W} インチに入りません",
                )
            )
        for i, line in enumerate(b.lines):
            lw = _width_in(_plain(line), PT_BOX_LINE)
            if lw + 2 * BOX_PAD_X > BOX_MAX_W + EPS:
                no = b.line_nos[i] if i < len(b.line_nos) else b.line_no
                problems.append(
                    FlowProblem(
                        no,
                        f"箱 `{b.name}` の中の行が、箱の幅の上限 {BOX_MAX_W} インチに入りません",
                    )
                )
            w = max(w, lw)
        content_w[b.name] = w + 2 * BOX_PAD_X
    if problems:
        raise FlowError(sorted(problems, key=lambda p: p.line or 0))

    cols = spec.columns
    n_rows = max((b.row_bottom for b in spec.boxes), default=-1) + 1
    col_w = [0.0] * cols
    for b in spec.boxes:
        col_w[b.col] = max(col_w[b.col], content_w[b.name])
    col_w = [
        max(BOX_MIN_W, w) if any(b.col == c for b in spec.boxes) else 0.0
        for c, w in enumerate(col_w)
    ]

    # 2. 枠の余白
    cells = [_group_cells(g, by_name) for g in spec.groups]
    depths = _depths(spec, cells)
    left_m = [0.0] * cols
    right_m = [0.0] * cols
    top_m = [0.0] * n_rows
    bottom_m = [0.0] * n_rows
    for c, (dl, dr, dt, db) in zip(cells, depths, strict=True):
        left_m[c.col0] = max(left_m[c.col0], dl * FRAME_PAD)
        right_m[c.col1] = max(right_m[c.col1], dr * FRAME_PAD)
        top_m[c.row0] = max(top_m[c.row0], dt * (FRAME_PAD + FRAME_LABEL_H))
        bottom_m[c.row1] = max(bottom_m[c.row1], db * FRAME_PAD)

    # 3. 列と行の位置
    col_x = [0.0] * cols
    x = left_m[0] if cols else 0.0
    for c in range(cols):
        col_x[c] = x
        x += col_w[c]
        if c + 1 < cols:
            x += right_m[c] + COL_GAP + left_m[c + 1]
    width = x + (right_m[cols - 1] if cols else 0.0)

    gaps = [bottom_m[r] + ROW_GAP + top_m[r + 1] for r in range(n_rows - 1)]
    covered = [False] * n_rows
    for b in spec.boxes:
        for r in range(b.row_top, b.row_bottom + 1):
            covered[r] = True
    row_h = [BOX_MIN_H if covered[r] else 0.0 for r in range(n_rows)]

    def content_h(b: BoxSpec) -> float:
        return (
            text_height_in(1, PT_BOX_NAME)
            + text_height_in(len(b.lines), PT_BOX_LINE)
            + 2 * BOX_PAD_Y
        )

    for b in spec.boxes:
        if b.row_top == b.row_bottom:
            row_h[b.row_top] = max(row_h[b.row_top], content_h(b))
    for b in spec.boxes:
        if b.row_top != b.row_bottom:
            rows = range(b.row_top, b.row_bottom + 1)
            total = sum(row_h[r] for r in rows) + sum(
                gaps[r] for r in range(b.row_top, b.row_bottom)
            )
            short = content_h(b) - total
            if short > 0:
                for r in rows:
                    row_h[r] += short / len(rows)
    row_y = [0.0] * n_rows
    y = top_m[0] if n_rows else 0.0
    for r in range(n_rows):
        row_y[r] = y
        y += row_h[r]
        if r + 1 < n_rows:
            y += gaps[r]
    height = y + (bottom_m[n_rows - 1] if n_rows else 0.0)

    # 4. 箱と枠
    placed_boxes = [
        PlacedBox(
            col_x[b.col],
            row_y[b.row_top],
            col_w[b.col],
            row_y[b.row_bottom] + row_h[b.row_bottom] - row_y[b.row_top],
            b.name,
            b.lines,
        )
        for b in spec.boxes
    ]
    frames: list[PlacedFrame] = []
    for g, c, (dl, dr, dt, db) in zip(spec.groups, cells, depths, strict=True):
        fx = col_x[c.col0] - dl * FRAME_PAD
        fy = row_y[c.row0] - dt * (FRAME_PAD + FRAME_LABEL_H)
        fr = col_x[c.col1] + col_w[c.col1] + dr * FRAME_PAD
        fb = row_y[c.row1] + row_h[c.row1] + db * FRAME_PAD
        frames.append(
            PlacedFrame(fx, fy, fr - fx, fb - fy, g.label, fx + FRAME_LABEL_DX, fy + FRAME_LABEL_DY)
        )
        if _width_in(g.label, PT_FLOW_LABEL) > (fr - fx) - FRAME_LABEL_SLACK + EPS:
            problems.append(
                FlowProblem(g.line_no, f"範囲の枠のラベル `{g.label}` が枠の幅に入りません")
            )
    if problems:
        raise FlowError(sorted(problems, key=lambda p: p.line or 0))

    return Diagram(width, height, placed_boxes, frames)
