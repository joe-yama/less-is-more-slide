"""構成図ファイル（`.flow`）の解析。違反は最初の 1 件で止めず、すべて集めてから例外にする。"""

import re
from dataclasses import dataclass, field

from slidekit.inline import Text, inline_problems, is_emoji
from slidekit.inline import runs as inline_runs

_FORBIDDEN_IN_NAME = (",", "(", ")", ":", "[", "]", "->", "**", "<br>")
MAX_BOX_LINES = 4
MAX_LABEL_LINES = 2
ATTRIBUTES = ("強調", "破線", "上回り", "下回り")
_HTML_TAG = re.compile(r"<(?!br>)[A-Za-z!/]")


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
        by_name = {b.name: b for b in boxes}
        for no, line in others:
            if line.startswith("- "):
                self._box_line(no, line, by_name)
            elif line.startswith("["):
                self._group(no, line, by_name, spec.groups)
            else:
                self._arrow(no, line, by_name, spec.arrows)
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

    # --- 箱の中の行 ---

    def _box_line(self, no: int, line: str, boxes: dict[str, BoxSpec]) -> None:
        name, sep, text = line[2:].partition(":")
        name, text = name.strip(), text.strip()
        if not sep or not name or not text:
            self.add(no, "箱の中の行は `- 名前: 文` の形で書いてください")
            return
        box = boxes.get(name)
        if box is None:
            self.add(no, f"配置にない名前 `{name}` です")
            return
        if "<br>" in text:
            self.add(no, "箱の中の行に改行は書けません")
            return
        if _HTML_TAG.search(text):
            self.add(no, "HTML は使えません")
            return
        if len(box.lines) >= MAX_BOX_LINES:
            self.add(no, f"箱 `{name}` の中の行は {MAX_BOX_LINES} 行までです")
            return
        box.lines.append(inline_runs(text))

    # --- 範囲の枠 ---

    def _group(
        self, no: int, line: str, boxes: dict[str, BoxSpec], groups: list[GroupSpec]
    ) -> None:
        close = line.find("]")
        if close < 0:
            self.add(no, "範囲の枠は `[ラベル] 名前, 名前` の形で書いてください")
            return
        label = line[1:close].strip()
        rest = line[close + 1 :].strip()
        ok = True
        if not label:
            self.add(no, "範囲の枠のラベルが空です")
            ok = False
        elif "**" in label or "<" in label:
            self.add(no, "範囲の枠のラベルに `**` や HTML は書けません")
            ok = False
        members = [m.strip() for m in rest.split(",")] if rest else []
        if not members or not all(members):
            self.add(no, "範囲の枠には、囲む箱の名前を `,` で区切って書いてください")
            return
        for m in members:
            if m not in boxes:
                self.add(no, f"配置にない名前 `{m}` です")
                ok = False
        if ok and any(g.label == label for g in groups):
            self.add(no, f"同じラベル `{label}` の枠がすでにあります")
            ok = False
        if ok:
            groups.append(GroupSpec(label, members, no))

    # --- 矢印 ---

    def _arrow(
        self, no: int, line: str, boxes: dict[str, BoxSpec], arrows: list[ArrowSpec]
    ) -> None:
        src, _, rest = line.partition(" -> ")
        src = src.strip()
        head, colon, label_text = rest.partition(":")
        head, label_text = head.strip(), label_text.strip()
        attrs: list[str] = []
        m = re.fullmatch(r"(.*?)\s*\(([^)]*)\)", head)
        if m:
            head = m.group(1).strip()
            attrs = [a.strip() for a in m.group(2).split(",")]
        dst = head
        ok = True
        for name in (src, dst):
            if name not in boxes:
                self.add(no, f"配置にない名前 `{name}` です")
                ok = False
        if ok and src == dst:
            self.add(no, "始点と終点が同じ矢印は書けません")
            ok = False
        if ok and any(a.src == src and a.dst == dst for a in arrows):
            self.add(no, f"`{src}` から `{dst}` への矢印はすでにあります")
            ok = False
        for a in attrs:
            if a not in ATTRIBUTES:
                self.add(
                    no,
                    f"知らない属性 `{a}` です。使える属性は {'、'.join(ATTRIBUTES)} です",
                )
                ok = False
        if "上回り" in attrs and "下回り" in attrs:
            self.add(no, "`上回り` と `下回り` は同時に使えません")
            ok = False
        emphasis = "強調" in attrs
        label: list[str] | None = None
        cross = False
        if colon:
            label, cross, label_ok = self._label(no, label_text, emphasis)
            ok = ok and label_ok
        if not ok:
            return
        route = "over" if "上回り" in attrs else "under" if "下回り" in attrs else "straight"
        arrows.append(ArrowSpec(src, dst, emphasis, "破線" in attrs, route, label, cross, no))

    def _label(self, no: int, text: str, emphasis: bool) -> tuple[list[str] | None, bool, bool]:
        """ラベルの行・× の有無・正しいか。"""
        cross = text.startswith("× ")
        if cross:
            text = text[2:].strip()
            if not emphasis:
                self.add(no, "`× ` のラベルは `強調` の矢印にだけ書けます")
                return None, cross, False
        if "**" in text:
            self.add(no, "矢印のラベルに強調は書けません")
            return None, cross, False
        if _HTML_TAG.search(text):
            self.add(no, "HTML は使えません（改行は `<br>` だけです）")
            return None, cross, False
        lines = [part.strip() for part in text.split("<br>")]
        if not all(lines):
            self.add(no, "矢印のラベルが空です")
            return None, cross, False
        if len(lines) > MAX_LABEL_LINES:
            self.add(no, f"矢印のラベルは {MAX_LABEL_LINES} 行までです")
            return None, cross, False
        return lines, cross, True


def _order(p: FlowProblem) -> int:
    return 0 if p.line is None else p.line


def parse_flow(text: str) -> FlowSpec:
    return _Parser().run(text)
