"""原稿の解析と全規則の検証。違反は最初の 1 件で止めず、すべて集めてから例外にする。"""

import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from slidekit.fit import (
    BODY_BOX_H,
    BULLET_GAP_PT,
    COLUMN_BULLET_GAP_PT,
    MAX_GLOSS_LINES,
    PT_BULLET,
    PT_CAPTION,
    PT_CELL,
    PT_CELL_SMALL,
    PT_COLUMN_BULLET,
    PT_COLUMN_TEXT,
    PT_COVER_LINE,
    PT_COVER_TITLE,
    PT_FLOW_NOTE,
    PT_HEADING,
    PT_STATEMENT,
    PT_STATEMENT_NOTE,
    STATEMENT_BOX_H,
    STATEMENT_NOTE_GAP_PT,
    break_line_count,
    gloss_pt,
    table_row_height_in,
    text_height_in,
)
from slidekit.flow import FlowError, FlowProblem, FlowSpec, parse_flow
from slidekit.grid import Grid, GridError, Problem, resolve
from slidekit.inline import Run, Text, inline_problems, is_emoji
from slidekit.inline import runs as _runs
from slidekit.layout import NOTE_GAP, Diagram, layout_flow

__all__ = ["Run", "Text"]  # inline.py へ移した。ここからも読める


@dataclass(frozen=True)
class Cover:
    title: str
    lines: list[Text]
    title_gloss: str | None = None
    line_glosses: list[str | None] = field(default_factory=list)


@dataclass(frozen=True)
class Section:
    title: str
    title_gloss: str | None = None


@dataclass(frozen=True)
class Statement:
    text: Text
    gloss: str | None = None
    notes: list[Text] = field(default_factory=list)
    note_glosses: list[str | None] = field(default_factory=list)


@dataclass(frozen=True)
class Bullets:
    heading: str
    items: list[Text]
    heading_gloss: str | None = None
    item_glosses: list[str | None] = field(default_factory=list)


@dataclass(frozen=True)
class Figure:
    heading: str
    alt: str
    ref: str
    grid: Grid
    caption: Text | None
    heading_gloss: str | None = None
    caption_gloss: str | None = None


@dataclass(frozen=True)
class DiagramFigure:
    heading: str
    alt: str
    ref: str
    diagram: Diagram
    note: Text | None
    heading_gloss: str | None = None


@dataclass(frozen=True)
class Table:
    heading: str
    header: list[Text]
    rows: list[list[Text]]
    heading_gloss: str | None = None
    header_glosses: list[str | None] = field(default_factory=list)
    row_glosses: list[list[str | None]] = field(default_factory=list)
    pt: int = PT_CELL


@dataclass(frozen=True)
class BulletsBlock:
    items: list[Text]
    item_glosses: list[str | None] = field(default_factory=list)


@dataclass(frozen=True)
class ImageBlock:
    alt: str
    ref: str
    grid: Grid


@dataclass(frozen=True)
class DiagramBlock:
    alt: str
    ref: str
    diagram: Diagram


@dataclass(frozen=True)
class TextBlock:
    text: Text
    gloss: str | None = None


Block = BulletsBlock | ImageBlock | DiagramBlock | TextBlock


@dataclass(frozen=True)
class TwoColumn:
    heading: str
    left: Block
    right: Block
    heading_gloss: str | None = None


Slide = Cover | Section | Statement | Bullets | Figure | DiagramFigure | Table | TwoColumn


@dataclass(frozen=True)
class Deck:
    slides: list[Slide]

    @property
    def title(self) -> str:
        return self.slides[0].title  # type: ignore[union-attr]


class ManuscriptError(Exception):
    def __init__(self, problems: list[Problem]):
        self.problems = problems
        super().__init__("; ".join(f"{p.line} 行目: {p.message}" for p in problems))


@dataclass(frozen=True)
class _Line:
    no: int
    raw: str

    @property
    def s(self) -> str:
        return self.raw.strip()


_GLOSS_MARK = "^"
_EMPHASIS = re.compile(r"\*\*(.+?)\*\*")
_BULLET = re.compile(r"^- (.*)$")
_IMAGE = re.compile(r"^!\[([^\]]*)\]\(([^)]*)\)$")
_TABLE_SEPARATOR_CELL = re.compile(r"^:?-+:?$")
_COLUMN_BREAK = "|||"
_NESTED_BULLET = re.compile(r"^\s+- ")
_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
_PAIRED_STAR = re.compile(r"\*[^*]+\*")
_HEADING3 = re.compile(r"^#{3,6}(\s|$)")
_NUMBERED = re.compile(r"^\d+\.(\s|$)")
_HTML = re.compile(r"^<[A-Za-z!/]")
_BR_TAG = re.compile(r"<\s*/?\s*br\b[^>]*>", re.IGNORECASE)  # `<br/>` や `<BR>` も含めて見つける
_BR_AROUND = re.compile(r"\s*<br>\s*")
_BR_EDGE_OR_DOUBLE = re.compile(r"^\s*<br>|<br>\s*$|<br>\s*<br>")

_EPS = 1e-9
MAX_BULLETS = 5
MAX_COVER_LINES = 3
MAX_STATEMENT_NOTES = 2
MIN_COLUMNS, MAX_COLUMNS = 2, 4
MAX_TABLE_ROWS = 6
MAX_BLOCK_BULLETS = 4

# design.md「寸法と文字の大きさ」。枠の幅（インチ）。
BODY_WIDTH = 11.53
INDENT = 0.4
FIGURE_CAPTION_WIDTH = 5.2
COLUMN_WIDTH = 5.5


def _grid_message(ref: str, p: Problem) -> str:
    """格子の違反を、原稿の行の報告に載せる文にする。位置は格子ファイルの中のもの。"""
    # アイコン名の誤りとファイルを読めない場合は、格子の中の位置を持たない。
    if ref.startswith("icon:") or p.message.startswith("格子ファイル"):
        return p.message
    where = f"{p.line} 行目" if p.col is None else f"{p.line} 行目 {p.col} 文字目"
    return f"格子ファイル {ref} の {where}: {p.message}"


def _flow_message(ref: str, p: FlowProblem) -> str:
    """構成図ファイルの違反を、原稿の行の報告に載せる文にする。"""
    if p.line is None:
        return f"構成図ファイル {ref}: {p.message}"
    return f"構成図ファイル {ref} の {p.line} 行目: {p.message}"


def _is_h1(ln: "_Line") -> bool:
    return ln.s == "#" or ln.s.startswith("# ")


def _is_flow(ref: str) -> bool:
    return ref.endswith(".flow")


@dataclass(frozen=True)
class _RowHeight:
    no: int  # 表の行の原稿の行番号
    gloss_no: int | None  # その行の添え訳の行番号
    full: float  # 添え訳を含む高さ（インチ）
    plain: float  # 添え訳を含まない高さ


class _Parser:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.problems: list[Problem] = []
        # 現在のスライドの添え訳。結びつけた対象の原稿の行番号 → 添え訳の行。
        self._glosses: dict[int, _Line] = {}
        self._used_glosses: set[int] = set()
        # `<br>` を書ける行（一言とその補足、表の行）の原稿の行番号。
        self._br_allowed: set[int] = set()
        # 構成図ファイルの解析結果（参照 → 構成図、または報告する文）。同じ参照は 1 度だけ読む。
        self._flows: dict[str, FlowSpec | list[str]] = {}

    def add(self, line: int, message: str) -> None:
        p = Problem(line, None, message)
        if p not in self.problems:
            self.problems.append(p)

    def fit(
        self, no: int, text: str | Text, label: str, pt: float, width: float, max_lines: int
    ) -> int:
        """枠に収まらない文字を拒否する（強調の記号は幅に数えない）。行数を返す。"""
        plain = text if isinstance(text, str) else "".join(r.text for r in text)
        n = break_line_count(plain, pt, width)
        if n > max_lines:
            self.add(
                no,
                f"{label}が長すぎます（{pt:g}pt の枠で {n} 行、上限は {max_lines} 行）。短くしてください",
            )
        return n

    # --- 全体 ---

    def run(self, text: str) -> Deck:
        text = text.removeprefix("﻿")
        raw_lines = text.replace("\r\n", "\n").split("\n")
        for i, raw in enumerate(raw_lines, start=1):
            self._check_emoji(i, raw)

        # スライドに分ける。start はそのスライドを始める `---` の行（先頭は 1）。
        groups: list[tuple[int, list[_Line]]] = [(1, [])]
        for i, raw in enumerate(raw_lines, start=1):
            if raw.rstrip() == "---":
                groups.append((i, []))
            elif raw.strip():
                groups[-1][1].append(_Line(i, raw.rstrip()))

        slides: list[Slide] = []
        for index, (start, lines) in enumerate(groups):
            if not lines:
                if index == 0:
                    self.add(1, "表紙にはタイトル（`# タイトル`）が必要です")
                else:
                    self.add(
                        start, "空のスライドです。内容を書くか、区切りの `---` を消してください"
                    )
                continue
            lines = self._split_glosses(lines)
            slide = self._cover(lines) if index == 0 else self._slide(lines)
            if slide is not None:
                slides.append(slide)
                for target_no, gloss in self._glosses.items():
                    if target_no not in self._used_glosses:
                        self.add(gloss.no, "この行には添え訳をつけられません")
        for _, group in groups:
            self._check_br_places(group)
        return Deck(slides)

    # --- 行ごとの規則 ---

    def _check_br_places(self, lines: list[_Line]) -> None:
        """`<br>` を書ける行以外の `<br>` と、`<br>` 以外の書き方の `br` のタグを拒否する。"""
        for ln in lines:
            tags = _BR_TAG.findall(ln.raw)
            if not tags:
                continue
            if ln.no not in self._br_allowed:
                self.add(ln.no, "`<br>` は一言・補足・表のセルにだけ書けます")
            elif any(t != "<br>" for t in tags):
                self.add(ln.no, "改行は `<br>` と書きます（`<br/>` や `<BR>` は使えません）")

    def _text(self, no: int, s: str) -> Text:
        """`<br>` を書ける文を、`<br>` を `\\n` にした `Text` にする。前後と連続の `<br>` は拒否する。"""
        return _runs(self._breaks(no, s))

    def _breaks(self, no: int, s: str) -> str:
        if _BR_EDGE_OR_DOUBLE.search(s):
            self.add(no, "`<br>` の前後に文字が要ります（先頭・末尾・連続の `<br>` は書けません）")
        return _BR_AROUND.sub("\n", s)

    def _check_emoji(self, no: int, raw: str) -> None:
        seen: set[str] = set()
        for ch in raw:
            if is_emoji(ch) and ch not in seen:
                seen.add(ch)
                self.add(no, f"絵文字 `{ch}`（U+{ord(ch):04X}）は使えません")

    def _check_lines(self, lines: list[_Line]) -> bool:
        """未対応の書式と強調の規則を見る。レイアウトの判定を止めるべき違反があれば True。"""
        tainted = False
        emphasis_seen = 0
        for ln in lines:
            s = ln.s
            is_heading = s.startswith(("# ", "## "))
            if s.startswith("```"):
                self.add(ln.no, "コードブロックは使えません")
                tainted = True
            elif _HEADING3.match(s):
                self.add(ln.no, "`###` 以下の見出しは使えません。見出しは `## ` だけです")
                tainted = True
            elif s.startswith(">"):
                self.add(ln.no, "引用 `>` は使えません")
                tainted = True
            elif _NUMBERED.match(s):
                self.add(ln.no, "番号付きリストは使えません。`- ` の箇条書きを使ってください")
                tainted = True
            elif _HTML.match(s) and not _BR_TAG.match(s):
                self.add(ln.no, "HTML は使えません")
                tainted = True
            image = _IMAGE.match(s)
            if image:
                # 画像の行は参照の検証で見る（リンクとは別物）。構成図の強調はその行で数える。
                if _is_flow(image.group(2).strip()):
                    flow = self._flow(image.group(2).strip())
                    if isinstance(flow, FlowSpec) and flow.emphasis_lines:
                        emphasis_seen += 1
                        if emphasis_seen == 2:
                            self.add(ln.no, "強調は 1 枚のスライドに 1 か所までです")
                continue
            for reason in inline_problems(s):
                if reason.startswith("インラインコード") and s.startswith("```"):
                    continue  # コードブロックとして報告済み
                self.add(ln.no, reason)
            spans = list(_EMPHASIS.finditer(s))
            if spans and is_heading:
                self.add(ln.no, "見出しの中に強調は書けません")
            elif spans:
                for _ in spans:
                    emphasis_seen += 1
                    if emphasis_seen == 2:
                        self.add(ln.no, "強調は 1 枚のスライドに 1 か所までです")
        return tainted

    # --- 添え訳 ---

    def _split_glosses(self, lines: list[_Line]) -> list[_Line]:
        """`^` の行を取り除き、すぐ前の行に結びつける。取り除いた後の行を返す。"""
        self._glosses = {}
        self._used_glosses = set()
        kept: list[_Line] = []
        prev: _Line | None = None
        for ln in lines:
            if not ln.s.startswith(_GLOSS_MARK):
                kept.append(ln)
                prev = ln
                continue
            valid = self._check_gloss(ln)
            if prev is None or prev.no != ln.no - 1:
                self.add(ln.no, "添え訳をつける対象がありません。対象の行のすぐ次に書いてください")
            elif prev.s.startswith(_GLOSS_MARK):
                self.add(ln.no, "添え訳は 1 つの行に 1 つだけです（添え訳が続いています）")
            elif valid:
                self._glosses[prev.no] = ln
            prev = ln
        return kept

    def _check_gloss(self, ln: _Line) -> bool:
        """添え訳の書式と、本文と同じインラインの規則を見る。"""
        s = ln.s
        body = s[1:]
        if not body.strip():
            self.add(ln.no, "添え訳が空です。`^ ` の後に訳を書いてください")
            return False
        if not body[0].isspace():
            self.add(ln.no, "`^` の次には空白が要ります（`^ 訳`）")
            return False
        ok = True
        if "`" in s:
            self.add(ln.no, "インラインコード（`` ` ``）は使えません")
            ok = False
        if _LINK.search(s):
            self.add(ln.no, "リンクは使えません")
            ok = False
        if re.search(r"__.+?__", s):
            self.add(ln.no, "`__強調__` は使えません。強調は `**語句**` だけです")
            ok = False
        if re.search(r"~~.+?~~", s):
            self.add(ln.no, "`~~取り消し~~` は使えません")
            ok = False
        if "**" in s:
            self.add(ln.no, "添え訳の中に強調は書けません")
            ok = False
        if _PAIRED_STAR.search(s.replace("**", "")):
            self.add(ln.no, "`*強調*` は使えません。強調は `**語句**` だけです")
            ok = False
        return ok

    def _gloss(
        self, target: _Line, pt: float, width: float, max_lines: int = MAX_GLOSS_LINES
    ) -> tuple[str | None, int]:
        """対象の行についた添え訳の文字と、その行数。なければ (None, 0)。

        pt は対象の本文の大きさ。添え訳の枠は同じ幅で、大きさは gloss_pt(pt)。"""
        gloss = self._glosses.get(target.no)
        if gloss is None:
            return None, 0
        self._used_glosses.add(target.no)
        text = gloss.s[1:].strip()
        return text, self.fit(gloss.no, text, "添え訳", gloss_pt(pt), width, max_lines)

    def _cell_glosses(self, target: _Line, n: int) -> list[str | None]:
        """表の行についた添え訳の行を、セルごとの添え訳にする（大きさによらない検査）。なければ n 個の None。"""
        none: list[str | None] = [None] * n
        gloss = self._glosses.get(target.no)
        if gloss is None:
            return none
        self._used_glosses.add(target.no)
        cells = self._cells(gloss.s[1:].strip())
        if len(cells) != n:
            self.add(gloss.no, f"添え訳の列数 {len(cells)} が表の {n} と違います")
            return none
        if not any(cells):
            self.add(gloss.no, "添え訳のセルがすべて空です。書かないか、訳を書いてください")
            return none
        return [c or None for c in cells]

    def _check_stack(
        self, label: str, paragraphs: list[tuple[int, float]], box_h: float = BODY_BOX_H
    ) -> None:
        """段落（原稿の行, 間隔を含む高さ）を上から積み、下端が最初に枠を超えた段落の行を報告する。"""
        used = 0.0
        for no, h in paragraphs:
            used += h
            if used > box_h + _EPS:
                self.add(
                    no,
                    f"{label}が枠の高さに収まりません（この項目の下端が {used:.2f}in、"
                    f"枠は {box_h}in）。項目を短くするか、減らしてください",
                )
                return

    def _reject_gloss(self, target: _Line, what: str) -> None:
        """添え訳をつけられない行についた添え訳を拒否する。"""
        gloss = self._glosses.get(target.no)
        if gloss is not None:
            self._used_glosses.add(target.no)
            self.add(gloss.no, f"{what}の行に添え訳はつけられません")

    # --- 表紙 ---

    def _cover(self, lines: list[_Line]) -> Cover | None:
        self._check_lines(lines)
        first = lines[0]
        if not first.s.startswith("# "):
            self.add(first.no, "表紙にはタイトル（`# タイトル`）が必要です")
            return None
        title = first.s[2:].strip()
        self.fit(first.no, title, "表紙のタイトル", PT_COVER_TITLE, BODY_WIDTH, 2)
        if not title:
            self.add(first.no, "表紙のタイトルが空です")
        rest = lines[1:]
        out: list[Text] = []
        glosses: list[str | None] = []
        for i, ln in enumerate(rest):
            s = ln.s
            if s.startswith("# "):
                self.add(ln.no, "`# ` の見出しは表紙のタイトルの 1 行だけです")
            elif _IMAGE.match(s):
                self.add(
                    ln.no, "表紙に画像は置けません。表紙に書けるのはタイトルと、その後の文だけです"
                )
            elif s.startswith(("## ", "|")) or _BULLET.match(ln.raw):
                self.add(ln.no, "表紙に書けるのはタイトルと、その後の文だけです")
            elif i >= MAX_COVER_LINES:
                if i == MAX_COVER_LINES:
                    self.add(ln.no, f"表紙の文は {MAX_COVER_LINES} 行までです")
            else:
                out.append(_runs(s))
                glosses.append(self._gloss(ln, PT_COVER_LINE, BODY_WIDTH, 1)[0])
                self.fit(ln.no, out[-1], "表紙の文", PT_COVER_LINE, BODY_WIDTH, 1)
        return Cover(title, out, self._gloss(first, PT_COVER_TITLE, BODY_WIDTH)[0], glosses)

    # --- 表紙以外 ---

    def _slide(self, lines: list[_Line]) -> Slide | None:
        tainted = self._check_lines(lines)
        h1 = [ln for ln in lines if _is_h1(ln)]
        if h1:
            if len(lines) == 1:
                return self._section(lines[0])
            for ln in h1:
                self.add(ln.no, "中扉は `# タイトル` の 1 行だけです。見出しは `## ` です")
            return None
        body_lines = lines
        if tainted:
            return None

        first = body_lines[0]
        if not first.s.startswith("## "):
            return self._statement(body_lines)

        heading = first.s[3:].strip()
        if not heading:
            self.add(first.no, "見出しが空です")
        self.fit(first.no, heading, "見出し", PT_HEADING, BODY_WIDTH, 1)
        body = body_lines[1:]
        if not body:
            self.add(first.no, "見出しだけのスライドです。本文を足してください")
            return None
        heading_gloss = self._gloss(first, PT_HEADING, BODY_WIDTH, 1)[0]
        result = self._with_heading(heading, body)
        if result is not None and heading_gloss is not None:
            result = replace(result, heading_gloss=heading_gloss)
        return result

    def _section(self, ln: _Line) -> Section:
        title = ln.s[1:].strip()
        self.fit(ln.no, title, "中扉のタイトル", PT_COVER_TITLE, BODY_WIDTH, 2)
        if not title:
            self.add(ln.no, "中扉のタイトルが空です")
        return Section(title, self._gloss(ln, PT_COVER_TITLE, BODY_WIDTH)[0])

    def _statement(self, lines: list[_Line]) -> Statement | None:
        first = lines[0]
        self._br_allowed.update(ln.no for ln in lines[:3])
        if len(lines) > 1 + MAX_STATEMENT_NOTES:
            self.add(
                lines[1 + MAX_STATEMENT_NOTES].no,
                f"一言の補足は {MAX_STATEMENT_NOTES} 行までです。"
                "もっと書くなら `## 見出し` を付けて箇条書きにしてください",
            )
            return None
        ok = True
        for ln in lines:
            if _BULLET.match(ln.raw) or ln.s.startswith(("|", "![", "## ")):
                self.add(ln.no, "見出しのないスライドの行は文だけ（一言と、その補足）です")
                ok = False
        if not ok:
            return None
        text = self._text(first.no, first.s)
        n = self.fit(first.no, text, "一言", PT_STATEMENT, BODY_WIDTH, 3)
        gloss, g = self._gloss(first, PT_STATEMENT, BODY_WIDTH)
        paragraphs: list[tuple[int, float]] = [(first.no, text_height_in(n, PT_STATEMENT))]
        if gloss is not None:
            paragraphs.append(
                (self._glosses[first.no].no, text_height_in(g, gloss_pt(PT_STATEMENT)))
            )
        notes: list[Text] = []
        note_glosses: list[str | None] = []
        for ln in lines[1:]:
            note = self._text(ln.no, ln.s)
            notes.append(note)
            n = self.fit(ln.no, note, "一言の補足", PT_STATEMENT_NOTE, BODY_WIDTH, 2)
            paragraphs.append(
                (ln.no, STATEMENT_NOTE_GAP_PT / 72 + text_height_in(n, PT_STATEMENT_NOTE))
            )
            note_gloss, g = self._gloss(ln, PT_STATEMENT_NOTE, BODY_WIDTH)
            note_glosses.append(note_gloss)
            if note_gloss is not None:
                paragraphs.append(
                    (self._glosses[ln.no].no, text_height_in(g, gloss_pt(PT_STATEMENT_NOTE)))
                )
        self._check_stack("一言と補足", paragraphs, STATEMENT_BOX_H)
        return Statement(text, gloss, notes, note_glosses)

    def _with_heading(self, heading: str, body: list[_Line]) -> Slide | None:
        if all(_BULLET.match(ln.raw) for ln in body):
            return self._bullets(heading, body)
        for ln in body:
            if _NESTED_BULLET.match(ln.raw):
                self.add(ln.no, "入れ子の箇条書きは使えません")
                return None
        if any(ln.s == _COLUMN_BREAK for ln in body):
            return self._two_columns(heading, body)
        if _IMAGE.match(body[0].s):
            return self._figure(heading, body)
        if body[0].s.startswith("|"):
            return self._table(heading, body)
        if len(body) == 1:
            self.add(
                body[0].no,
                "見出しと文だけのスライドは作れません。"
                "文だけの一言か、`- ` で始まる箇条書きにしてください",
            )
        else:
            stray = next(ln for ln in body if not _BULLET.match(ln.raw))
            self.add(
                stray.no,
                "どのレイアウトにも当たりません。"
                "箇条書きと文は混ぜられません（箇条書きは全行を `- ` で始めます）",
            )
        return None

    def _bullets(self, heading: str, body: list[_Line]) -> Bullets | None:
        if len(body) > MAX_BULLETS:
            self.add(
                body[MAX_BULLETS].no,
                f"箇条書きは {MAX_BULLETS} 項目までです（{MAX_BULLETS + 1} 項目目）",
            )
            return None
        items: list[Text] = []
        glosses: list[str | None] = []
        # 項目と添え訳の段落を上から積む。項目の間の余白を足して、枠の高さと比べる。
        paragraphs: list[tuple[int, float]] = []
        for i, ln in enumerate(body):
            m = _BULLET.match(ln.raw)
            assert m is not None
            if not m.group(1).strip():
                self.add(ln.no, "箇条書きの項目が空です")
            items.append(_runs(m.group(1).strip()))
            n = self.fit(ln.no, items[-1], "箇条書きの項目", PT_BULLET, BODY_WIDTH - INDENT, 2)
            paragraphs.append(
                (ln.no, text_height_in(n, PT_BULLET) + (BULLET_GAP_PT / 72 if i else 0))
            )
            gloss, g = self._gloss(ln, PT_BULLET, BODY_WIDTH - INDENT)
            glosses.append(gloss)
            if gloss is not None:
                paragraphs.append((self._glosses[ln.no].no, text_height_in(g, gloss_pt(PT_BULLET))))
        self._check_stack("箇条書き", paragraphs)
        return Bullets(heading, items, item_glosses=glosses)

    # --- 図 ---

    def _flow(self, ref: str) -> FlowSpec | list[str]:
        """構成図ファイルを読んで解析する。失敗は報告する文の一覧。"""
        if ref not in self._flows:
            try:
                text = (self.base_dir / ref).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                self._flows[ref] = [f"構成図ファイル {ref} を読めません ({e})"]
            else:
                try:
                    self._flows[ref] = parse_flow(text)
                except FlowError as e:
                    self._flows[ref] = [_flow_message(ref, p) for p in e.problems]
        return self._flows[ref]

    def _diagram(self, ln: _Line, ref: str, max_w: float, max_h: float) -> Diagram | None:
        flow = self._flow(ref)
        if isinstance(flow, FlowSpec):
            try:
                return layout_flow(flow, max_w, max_h)
            except FlowError as e:
                messages = [_flow_message(ref, p) for p in e.problems]
        else:
            messages = flow
        for m in messages:
            self.add(ln.no, m)
        return None

    def _image(
        self, ln: _Line, max_w: float = BODY_WIDTH, max_h: float = BODY_BOX_H
    ) -> tuple[str, str, Grid | Diagram] | None:
        """画像の行を検証して (説明, 参照, 格子か構成図) にする。違反は原稿の行番号で報告する。"""
        m = _IMAGE.match(ln.s)
        assert m is not None
        alt, ref = m.group(1).strip(), m.group(2).strip()
        ok = True
        if not alt:
            self.add(ln.no, "画像の説明が空です。`![説明](参照)` の説明は代替テキストになります")
            ok = False
        if _is_flow(ref):
            diagram = self._diagram(ln, ref, max_w, max_h)
            return (alt, ref, diagram) if ok and diagram is not None else None
        try:
            grid = resolve(ref, self.base_dir)
        except GridError as e:
            for p in e.problems:
                self.add(ln.no, _grid_message(ref, p))
            return None
        return (alt, ref, grid) if ok else None

    def _figure(self, heading: str, body: list[_Line]) -> Figure | DiagramFigure | None:
        m = _IMAGE.match(body[0].s)
        assert m is not None
        flow = _is_flow(m.group(2).strip())
        self._reject_gloss(body[0], "画像")
        caption: Text | None = None
        caption_gloss: str | None = None
        max_h = BODY_BOX_H
        valid = True
        if len(body) >= 2:
            cap = body[1]
            if _IMAGE.match(cap.s) or _BULLET.match(cap.raw) or cap.s.startswith("|"):
                self.add(cap.no, "図は画像 1 つと、任意の 1 行の説明文だけです")
                valid = False
            elif flow:
                caption = _runs(cap.s)
                self._reject_gloss(cap, "注記")
                n = self.fit(cap.no, caption, "構成図の注記", PT_FLOW_NOTE, BODY_WIDTH, 3)
                max_h = BODY_BOX_H - text_height_in(n, PT_FLOW_NOTE) - NOTE_GAP
            else:
                caption = _runs(cap.s)
                caption_gloss = self._gloss(cap, PT_CAPTION, FIGURE_CAPTION_WIDTH)[0]
                self.fit(cap.no, caption, "図の説明文", PT_CAPTION, FIGURE_CAPTION_WIDTH, 3)
        if len(body) > 2:
            self.add(body[2].no, "図の説明文は 1 行までです")
            valid = False
        image = self._image(body[0], BODY_WIDTH, max_h)
        if image is None or not valid:
            return None
        alt, ref, picture = image
        if isinstance(picture, Diagram):
            return DiagramFigure(heading, alt, ref, picture, caption)
        return Figure(heading, alt, ref, picture, caption, caption_gloss=caption_gloss)

    # --- 表 ---

    @staticmethod
    def _cells(s: str) -> list[str]:
        s = s.strip()
        s = s.removeprefix("|").removesuffix("|")
        return [c.strip() for c in s.split("|")]

    def _row_height(
        self, ln: _Line, cell_lines: list[int], gloss_lines: list[int], pt: float
    ) -> "_RowHeight":
        """表の 1 行の高さ。セルごとに本文と添え訳を積み、一番高いセルで決まる。"""
        gloss_no = self._glosses[ln.no].no if ln.no in self._glosses else None
        gp = gloss_pt(pt)
        pad = gloss_lines + [0] * (len(cell_lines) - len(gloss_lines))
        full = max(
            (table_row_height_in(n, pt, g, gp) for n, g in zip(cell_lines, pad, strict=False)),
            default=table_row_height_in(1, pt),
        )
        plain = max(
            (table_row_height_in(n, pt) for n in cell_lines),
            default=table_row_height_in(1, pt),
        )
        return _RowHeight(ln.no, gloss_no, full, plain)

    def _check_table_height(self, heights: "list[_RowHeight]") -> None:
        """行を上から積み、下端が最初に枠を超えた行を報告する。添え訳を除いても超えるなら表の行、
        添え訳を足して初めて超えるなら添え訳の行（その行に添え訳がなければ直前の添え訳）。"""
        used = plain_used = 0.0
        last_gloss: int | None = None
        for row in heights:
            used += row.full
            plain_used += row.plain
            if row.gloss_no is not None:
                last_gloss = row.gloss_no
            if used <= BODY_BOX_H + _EPS:
                continue
            if plain_used > BODY_BOX_H + _EPS or last_gloss is None:
                no, bottom = row.no, plain_used
            else:
                no, bottom = last_gloss, used
            self.add(
                no,
                f"表が枠の高さに収まりません（この行の下端が {bottom:.2f}in、"
                f"枠は {BODY_BOX_H}in）。セルを短くするか、行を減らしてください",
            )
            return

    def _table_pass(
        self,
        pt: int,
        rows: list[tuple[_Line, list[str], list[str | None]]],
        cell_width: float,
    ) -> list[Problem]:
        """表のセルの大きさ pt で、セルの行数・添え訳の行数・高さを判定する。違反は足さずに返す。"""
        saved, self.problems = self.problems, []
        try:
            heights: list[_RowHeight] = []
            for ln, cells, glosses in rows:
                cell_lines = [self.fit(ln.no, c, "表のセル", pt, cell_width, 2) for c in cells]
                gloss_lines = [
                    self.fit(
                        self._glosses[ln.no].no,
                        g,
                        "添え訳",
                        gloss_pt(pt),
                        cell_width,
                        MAX_GLOSS_LINES,
                    )
                    if g
                    else 0
                    for g in glosses
                ]
                heights.append(self._row_height(ln, cell_lines, gloss_lines, pt))
            self._check_table_height(heights)
            return self.problems
        finally:
            self.problems = saved

    def _table_size(
        self,
        rows: list[tuple[_Line, list[str], list[str | None]]],
        cell_width: float,
    ) -> int:
        """18pt で違反がなければ 18pt、あれば 16pt で判定し直す。16pt でも違反があれば 16pt の違反を足す。"""
        if not self._table_pass(PT_CELL, rows, cell_width):
            return PT_CELL
        found = self._table_pass(PT_CELL_SMALL, rows, cell_width)
        for p in found:
            self.add(p.line, p.message)
        return PT_CELL_SMALL

    def _table(self, heading: str, body: list[_Line]) -> Table | None:
        head = body[0]
        self._br_allowed.update(ln.no for ln in body if ln.s.startswith("|"))
        for ln in body:
            if not ln.s.startswith("|"):
                self.add(ln.no, "表の行は `|` で始めます。表と他の内容は混ぜられません")
                return None
        header = [self._breaks(head.no, c) for c in self._cells(head.s)]
        n = len(header)
        cell_width = BODY_WIDTH / n - 0.2
        # 大きさごとの判定に渡す、行（原稿の行、セルの文字、セルの添え訳）。見出し行が先頭。
        sized: list[tuple[_Line, list[str], list[str | None]]] = [
            (head, header, self._cell_glosses(head, n))
        ]
        ok = True
        if not MIN_COLUMNS <= n <= MAX_COLUMNS:
            self.add(head.no, f"表の列は {MIN_COLUMNS}〜{MAX_COLUMNS} 列です（{n} 列あります）")
            ok = False
        if len(body) < 2:
            self.add(head.no, "表には見出し行の次に区切り行（`|---|---|`）が要ります")
            self._table_size(sized, cell_width)
            return None
        sep = body[1]
        self._reject_gloss(sep, "表の区切り")
        sep_cells = self._cells(sep.s)
        if not all(_TABLE_SEPARATOR_CELL.match(c) for c in sep_cells):
            self.add(sep.no, "表の見出し行の次は区切り行（`|---|---|`）にしてください")
            self._table_size(sized, cell_width)
            return None
        if len(sep_cells) != n:
            self.add(sep.no, f"区切り行の列数 {len(sep_cells)} が見出し行の {n} と違います")
            ok = False
        data = body[2:]
        if not data:
            self.add(head.no, "表には本文の行が 1 行以上要ります")
            self._table_size(sized, cell_width)
            return None
        if len(data) > MAX_TABLE_ROWS:
            self.add(
                data[MAX_TABLE_ROWS].no,
                f"表の本文は {MAX_TABLE_ROWS} 行までです（{MAX_TABLE_ROWS + 1} 行目）",
            )
            ok = False
        rows: list[list[Text]] = []
        row_glosses: list[list[str | None]] = []
        for ln in data:
            glosses = self._cell_glosses(ln, n)
            row_glosses.append(glosses)
            cells = [self._breaks(ln.no, c) for c in self._cells(ln.s)]
            if len(cells) != n:
                self.add(ln.no, f"行の列数 {len(cells)} が見出し行の {n} と違います")
                ok = False
            rows.append([_runs(c) for c in cells])
            sized.append((ln, cells, glosses))
        pt = self._table_size(sized, cell_width)
        if not ok:
            return None
        return Table(
            heading,
            [_runs(c) for c in header],
            rows,
            header_glosses=sized[0][2],
            row_glosses=row_glosses,
            pt=pt,
        )

    # --- 左右 2 列 ---

    def _two_columns(self, heading: str, body: list[_Line]) -> TwoColumn | None:
        breaks = [i for i, ln in enumerate(body) if ln.s == _COLUMN_BREAK]
        ok = True
        if len(breaks) > 1:
            self.add(body[breaks[1]].no, "`|||` は 1 つだけです")
            ok = False
        brk = body[breaks[0]]
        left_lines = body[: breaks[0]]
        right_end = breaks[1] if len(breaks) > 1 else len(body)
        right_lines = body[breaks[0] + 1 : right_end]
        self._reject_gloss(brk, "`|||`")
        left = self._block(left_lines, brk, "左")
        right = self._block(right_lines, brk, "右")
        if not ok or left is None or right is None:
            return None
        return TwoColumn(heading, left, right)

    def _block(self, lines: list[_Line], brk: _Line, side: str) -> Block | None:
        if not lines:
            self.add(brk.no, f"{side}の塊が空です。`|||` の{side}に内容を書いてください")
            return None
        for ln in lines:
            if _NESTED_BULLET.match(ln.raw):
                self.add(ln.no, "入れ子の箇条書きは使えません")
                return None
        what = "各塊は、箇条書き（1〜4 個）、画像の行 1 つ、1 行の文のどれか 1 つだけです"
        if all(_BULLET.match(ln.raw) for ln in lines):
            if len(lines) > MAX_BLOCK_BULLETS:
                self.add(
                    lines[MAX_BLOCK_BULLETS].no,
                    f"{side}の塊の箇条書きは {MAX_BLOCK_BULLETS} 個までです",
                )
                return None
            items: list[Text] = []
            glosses: list[str | None] = []
            paragraphs: list[tuple[int, float]] = []
            for i, ln in enumerate(lines):
                m = _BULLET.match(ln.raw)
                assert m is not None
                if not m.group(1).strip():
                    self.add(ln.no, "箇条書きの項目が空です")
                items.append(_runs(m.group(1).strip()))
                n = self.fit(
                    ln.no,
                    items[-1],
                    "2 列の箇条書きの項目",
                    PT_COLUMN_BULLET,
                    COLUMN_WIDTH - INDENT,
                    2,
                )
                paragraphs.append(
                    (
                        ln.no,
                        text_height_in(n, PT_COLUMN_BULLET)
                        + (COLUMN_BULLET_GAP_PT / 72 if i else 0),
                    )
                )
                gloss, g = self._gloss(ln, PT_COLUMN_BULLET, COLUMN_WIDTH - INDENT)
                glosses.append(gloss)
                if gloss is not None:
                    paragraphs.append(
                        (self._glosses[ln.no].no, text_height_in(g, gloss_pt(PT_COLUMN_BULLET)))
                    )
            self._check_stack(f"{side}の塊の箇条書き", paragraphs)
            return BulletsBlock(items, glosses)
        stray = next((ln for ln in lines if _BULLET.match(ln.raw)), None)
        if len(lines) > 1:
            extra = lines[1] if stray is None or stray is lines[0] else stray
            self.add(extra.no, what)
            return None
        only = lines[0]
        if _IMAGE.match(only.s):
            self._reject_gloss(only, "画像")
            image = self._image(only, COLUMN_WIDTH, BODY_BOX_H)
            if image is None:
                return None
            alt, ref, picture = image
            if isinstance(picture, Diagram):
                return DiagramBlock(alt, ref, picture)
            return ImageBlock(alt, ref, picture)
        if only.s.startswith("|"):
            self.add(only.no, what)
            return None
        text = _runs(only.s)
        self.fit(only.no, text, "2 列の文", PT_COLUMN_TEXT, COLUMN_WIDTH, 3)
        return TextBlock(text, self._gloss(only, PT_COLUMN_TEXT, COLUMN_WIDTH)[0])


def parse(text: str, base_dir: Path) -> Deck:
    parser = _Parser(Path(base_dir))
    deck = parser.run(text)
    if parser.problems:
        raise ManuscriptError(sorted(parser.problems, key=lambda p: p.line))
    return deck
