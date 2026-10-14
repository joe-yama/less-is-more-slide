"""構成図ファイル（`.flow`）の解析。違反は最初の 1 件で止めず、すべて集めてから例外にする。"""

from dataclasses import dataclass, field

from slidekit.inline import Text, inline_problems, is_emoji

_FORBIDDEN_IN_NAME = (",", "(", ")", ":", "[", "]", "->", "**", "<br>")


@dataclass(frozen=True)
class FlowProblem:
    line: int | None  # 構成図ファイルの行番号。行に結びつかない違反は None
    message: str


class FlowError(Exception):
    def __init__(self, problems: list[FlowProblem]):
        self.problems = problems
        super().__init__("; ".join(p.message for p in problems))


@dataclass
class BoxSpec:
    name: str
    col: int
    row_top: int
    row_bottom: int
    lines: list[Text]
    line_no: int  # 最初に現れた配置の行


@dataclass
class GroupSpec:
    label: str
    members: list[str]
    line_no: int


@dataclass
class ArrowSpec:
    src: str
    dst: str
    emphasis: bool
    dashed: bool
    route: str  # "straight" | "over" | "under"
    label: list[str] | None
    cross: bool
    line_no: int


@dataclass
class FlowSpec:
    columns: int
    boxes: list[BoxSpec]
    groups: list[GroupSpec]
    arrows: list[ArrowSpec]
    emphasis_lines: list[int] = field(default_factory=list)


def _cells(s: str) -> list[str]:
    s = s.strip()
    s = s.removeprefix("|").removesuffix("|")
    return [c.strip() for c in s.split("|")]


class _Parser:
    def __init__(self) -> None:
        self.problems: list[FlowProblem] = []

    def add(self, line: int | None, message: str) -> None:
        self.problems.append(FlowProblem(line, message))

    def run(self, text: str) -> FlowSpec:
        text = text.removeprefix("﻿")
        raw_lines = text.replace("\r\n", "\n").split("\n")
        placement: list[tuple[int, str]] = []
        others: list[tuple[int, str]] = []
        seen_other_after_placement = False
        for no, raw in enumerate(raw_lines, start=1):
            s = raw.strip()
            if not s:
                continue
            self._check_emoji(no, s)
            if s.startswith("|"):
                if seen_other_after_placement:
                    self.add(no, "配置の行は続けて書いてください")
                    continue
                placement.append((no, s))
            else:
                if placement:
                    seen_other_after_placement = True
                if s.startswith(("- ", "[")) or " -> " in s:
                    for reason in inline_problems(s):
                        self.add(no, reason)
                    others.append((no, s))
                else:
                    self.add(
                        no,
                        "読めない行です。配置の行（`|`）、箱の中の行（`- `）、"
                        "範囲の枠（`[`）、矢印（` -> `）のどれかで書いてください",
                    )
        columns, boxes = self._placement(placement)
        spec = FlowSpec(columns, boxes, [], [])
        if self.problems:
            raise FlowError(sorted(self.problems, key=_order))
        return spec

    def _check_emoji(self, no: int, s: str) -> None:
        seen: set[str] = set()
        for ch in s:
            if is_emoji(ch) and ch not in seen:
                seen.add(ch)
                self.add(no, f"絵文字 `{ch}`（U+{ord(ch):04X}）は使えません")

    def _name_problems(self, no: int, name: str) -> bool:
        """名前に使えない文字を報告する。報告したら True。"""
        bad = [t for t in _FORBIDDEN_IN_NAME if t in name]
        if bad:
            self.add(no, f"名前 `{name}` に使えない文字があります: {' '.join(bad)}")
            return True
        for reason in inline_problems(name):
            self.add(no, f"名前 `{name}`: {reason}")
            return True
        return False

    def _placement(self, rows: list[tuple[int, str]]) -> tuple[int, list[BoxSpec]]:
        if not rows:
            self.add(None, "配置の行がありません")
            return 0, []
        columns = len(_cells(rows[0][1]))
        boxes: dict[str, BoxSpec] = {}
        r = 0
        for no, s in rows:
            cells = _cells(s)
            if len(cells) != columns:
                self.add(no, f"配置の行の列の数 {len(cells)} が 1 行目の {columns} と違います")
                continue
            for c, name in enumerate(cells):
                if not name:
                    continue
                if self._name_problems(no, name):
                    continue
                box = boxes.get(name)
                if box is None:
                    boxes[name] = BoxSpec(name, c, r, r, [], no)
                elif box.col == c and box.row_bottom == r - 1:
                    box.row_bottom = r
                else:
                    self.add(
                        no,
                        f"同じ名前 `{name}` が離れたセルか別の列にあります。"
                        "同じ列の上下に続けて書くか、名前を変えてください",
                    )
            r += 1
        return columns, list(boxes.values())


def _order(p: FlowProblem) -> int:
    return 0 if p.line is None else p.line


def parse_flow(text: str) -> FlowSpec:
    return _Parser().run(text)
