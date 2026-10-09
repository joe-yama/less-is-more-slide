"""原稿の解析と全規則の検証。違反は最初の 1 件で止めず、すべて集めてから例外にする。"""

import re
from dataclasses import dataclass
from pathlib import Path

from slidekit.grid import Grid, GridError, Problem, resolve

# Unicode 15.1 の emoji-data.txt の Extended_Pictographic の範囲（両端を含む）。
_EXTENDED_PICTOGRAPHIC = (
    (0x00A9, 0x00A9), (0x00AE, 0x00AE), (0x203C, 0x203C), (0x2049, 0x2049),
    (0x2122, 0x2122), (0x2139, 0x2139), (0x2194, 0x2199), (0x21A9, 0x21AA),
    (0x231A, 0x231B), (0x2328, 0x2328), (0x2388, 0x2388), (0x23CF, 0x23CF),
    (0x23E9, 0x23F3), (0x23F8, 0x23FA), (0x24C2, 0x24C2), (0x25AA, 0x25AB),
    (0x25B6, 0x25B6), (0x25C0, 0x25C0), (0x25FB, 0x25FE), (0x2600, 0x2605),
    (0x2607, 0x2612), (0x2614, 0x2685), (0x2690, 0x2705), (0x2708, 0x2712),
    (0x2714, 0x2714), (0x2716, 0x2716), (0x271D, 0x271D), (0x2721, 0x2721),
    (0x2728, 0x2728), (0x2733, 0x2734), (0x2744, 0x2744), (0x2747, 0x2747),
    (0x274C, 0x274C), (0x274E, 0x274E), (0x2753, 0x2755), (0x2757, 0x2757),
    (0x2763, 0x2767), (0x2795, 0x2797), (0x27A1, 0x27A1), (0x27B0, 0x27B0),
    (0x27BF, 0x27BF), (0x2934, 0x2935), (0x2B05, 0x2B07), (0x2B1B, 0x2B1C),
    (0x2B50, 0x2B50), (0x2B55, 0x2B55), (0x3030, 0x3030), (0x303D, 0x303D),
    (0x3297, 0x3297), (0x3299, 0x3299), (0x1F000, 0x1F0FF), (0x1F10D, 0x1F10F),
    (0x1F12F, 0x1F12F), (0x1F16C, 0x1F171), (0x1F17E, 0x1F17F), (0x1F18E, 0x1F18E),
    (0x1F191, 0x1F19A), (0x1F1AD, 0x1F1E5), (0x1F201, 0x1F20F), (0x1F21A, 0x1F21A),
    (0x1F22F, 0x1F22F), (0x1F232, 0x1F23A), (0x1F23C, 0x1F23F), (0x1F249, 0x1F3FA),
    (0x1F400, 0x1F53D), (0x1F546, 0x1F64F), (0x1F680, 0x1F6FF), (0x1F774, 0x1F77F),
    (0x1F7D5, 0x1F7FF), (0x1F80C, 0x1F80F), (0x1F848, 0x1F84F), (0x1F85A, 0x1F85F),
    (0x1F888, 0x1F88F), (0x1F8AE, 0x1F8FF), (0x1F90C, 0x1F93A), (0x1F93C, 0x1F945),
    (0x1F947, 0x1FAFF), (0x1FC00, 0x1FFFD),
)  # fmt: skip
_VARIATION_SELECTOR_16 = 0xFE0F


def _is_emoji(ch: str) -> bool:
    cp = ord(ch)
    if cp == _VARIATION_SELECTOR_16:
        return True
    return any(lo <= cp <= hi for lo, hi in _EXTENDED_PICTOGRAPHIC)


@dataclass(frozen=True)
class Run:
    """文字の連なり 1 つ。emphasis は強調色（太字ではない）。"""

    text: str
    emphasis: bool = False


Text = tuple[Run, ...]


@dataclass(frozen=True)
class Cover:
    title: str
    lines: list[Text]


@dataclass(frozen=True)
class Statement:
    text: Text


@dataclass(frozen=True)
class Bullets:
    heading: str
    items: list[Text]


@dataclass(frozen=True)
class Figure:
    heading: str
    alt: str
    ref: str
    grid: Grid
    caption: Text | None


@dataclass(frozen=True)
class Table:
    heading: str
    header: list[Text]
    rows: list[list[Text]]


@dataclass(frozen=True)
class BulletsBlock:
    items: list[Text]


@dataclass(frozen=True)
class ImageBlock:
    alt: str
    ref: str
    grid: Grid


@dataclass(frozen=True)
class TextBlock:
    text: Text


Block = BulletsBlock | ImageBlock | TextBlock


@dataclass(frozen=True)
class TwoColumn:
    heading: str
    left: Block
    right: Block


Slide = Cover | Statement | Bullets | Figure | Table | TwoColumn


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

MAX_BULLETS = 5
MAX_COVER_LINES = 3
MIN_COLUMNS, MAX_COLUMNS = 2, 4
MAX_TABLE_ROWS = 6
MAX_BLOCK_BULLETS = 4


def _grid_message(ref: str, p: Problem) -> str:
    """格子の違反を、原稿の行の報告に載せる文にする。位置は格子ファイルの中のもの。"""
    # アイコン名の誤りとファイルを読めない場合は、格子の中の位置を持たない。
    if ref.startswith("icon:") or p.message.startswith("格子ファイル"):
        return p.message
    where = f"{p.line} 行目" if p.col is None else f"{p.line} 行目 {p.col} 文字目"
    return f"格子ファイル {ref} の {where}: {p.message}"


def _runs(text: str) -> Text:
    runs: list[Run] = []
    pos = 0
    for m in _EMPHASIS.finditer(text):
        if m.start() > pos:
            runs.append(Run(text[pos : m.start()]))
        runs.append(Run(m.group(1), emphasis=True))
        pos = m.end()
    if pos < len(text):
        runs.append(Run(text[pos:]))
    return tuple(runs)


class _Parser:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.problems: list[Problem] = []

    def add(self, line: int, message: str) -> None:
        p = Problem(line, None, message)
        if p not in self.problems:
            self.problems.append(p)

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
            slide = self._cover(lines) if index == 0 else self._slide(lines)
            if slide is not None:
                slides.append(slide)
        return Deck(slides)

    # --- 行ごとの規則 ---

    def _check_emoji(self, no: int, raw: str) -> None:
        seen: set[str] = set()
        for ch in raw:
            if _is_emoji(ch) and ch not in seen:
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
            elif _HTML.match(s):
                self.add(ln.no, "HTML は使えません")
                tainted = True
            if _IMAGE.match(s):
                continue  # 画像の行は参照の検証で見る（リンクとは別物）
            if "`" in s and not s.startswith("```"):
                self.add(ln.no, "インラインコード（`` ` ``）は使えません")
            if _LINK.search(s):
                self.add(ln.no, "リンクは使えません")
            if re.search(r"__.+?__", s):
                self.add(ln.no, "`__強調__` は使えません。強調は `**語句**` だけです")
            if re.search(r"~~.+?~~", s):
                self.add(ln.no, "`~~取り消し~~` は使えません")
            spans = list(_EMPHASIS.finditer(s))
            rest = _EMPHASIS.sub("", s)
            if "**" in rest:
                self.add(ln.no, "強調の `**` が閉じていません")
            if _PAIRED_STAR.search(rest.replace("**", "")):
                self.add(ln.no, "`*強調*` は使えません。強調は `**語句**` だけです")
            if spans and is_heading:
                self.add(ln.no, "見出しの中に強調は書けません")
            elif spans:
                for _ in spans:
                    emphasis_seen += 1
                    if emphasis_seen == 2:
                        self.add(ln.no, "強調は 1 枚のスライドに 1 か所までです")
        return tainted

    # --- 表紙 ---

    def _cover(self, lines: list[_Line]) -> Cover | None:
        self._check_lines(lines)
        first = lines[0]
        if not first.s.startswith("# "):
            self.add(first.no, "表紙にはタイトル（`# タイトル`）が必要です")
            return None
        title = first.s[2:].strip()
        if not title:
            self.add(first.no, "表紙のタイトルが空です")
        rest = lines[1:]
        out: list[Text] = []
        for i, ln in enumerate(rest):
            s = ln.s
            if s.startswith("# "):
                self.add(ln.no, "`# ` の見出しは表紙のタイトルの 1 行だけです")
            elif s.startswith(("## ", "|")) or _BULLET.match(ln.raw):
                self.add(ln.no, "表紙に書けるのはタイトルと、その後の文だけです")
            elif i >= MAX_COVER_LINES:
                if i == MAX_COVER_LINES:
                    self.add(ln.no, f"表紙の文は {MAX_COVER_LINES} 行までです")
            else:
                out.append(_runs(s))
        return Cover(title, out)

    # --- 表紙以外 ---

    def _slide(self, lines: list[_Line]) -> Slide | None:
        tainted = self._check_lines(lines)
        body_lines: list[_Line] = []
        for ln in lines:
            if ln.s.startswith("# "):
                self.add(ln.no, "`# ` の見出しは表紙のタイトルにだけ使えます。見出しは `## ` です")
            else:
                body_lines.append(ln)
        if not body_lines:
            return None
        if tainted:
            return None

        first = body_lines[0]
        if not first.s.startswith("## "):
            return self._statement(body_lines)

        heading = first.s[3:].strip()
        if not heading:
            self.add(first.no, "見出しが空です")
        body = body_lines[1:]
        if not body:
            self.add(first.no, "見出しだけのスライドです。本文を足してください")
            return None
        return self._with_heading(heading, body)

    def _statement(self, lines: list[_Line]) -> Statement | None:
        first = lines[0]
        if len(lines) > 1:
            self.add(
                first.no,
                "見出し（`## `）のないスライドは 1 行の文だけ（一言）です。"
                "複数行なら `## 見出し` を付けて箇条書きにしてください",
            )
            return None
        s = first.s
        if _BULLET.match(first.raw) or s.startswith(("|", "![", "## ")):
            self.add(first.no, "見出しのないスライドは 1 行の文だけ（一言）です")
            return None
        return Statement(_runs(s))

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
        for ln in body:
            m = _BULLET.match(ln.raw)
            assert m is not None
            if not m.group(1).strip():
                self.add(ln.no, "箇条書きの項目が空です")
            items.append(_runs(m.group(1).strip()))
        return Bullets(heading, items)

    # --- 図 ---

    def _image(self, ln: _Line) -> tuple[str, str, Grid] | None:
        """画像の行を検証して (説明, 参照, 格子) にする。違反は原稿の行番号で報告する。"""
        m = _IMAGE.match(ln.s)
        assert m is not None
        alt, ref = m.group(1).strip(), m.group(2).strip()
        ok = True
        if not alt:
            self.add(ln.no, "画像の説明が空です。`![説明](参照)` の説明は代替テキストになります")
            ok = False
        try:
            grid = resolve(ref, self.base_dir)
        except GridError as e:
            for p in e.problems:
                self.add(ln.no, _grid_message(ref, p))
            return None
        return (alt, ref, grid) if ok else None

    def _figure(self, heading: str, body: list[_Line]) -> Figure | None:
        image = self._image(body[0])
        caption: Text | None = None
        valid = True
        if len(body) >= 2:
            cap = body[1]
            if _IMAGE.match(cap.s) or _BULLET.match(cap.raw) or cap.s.startswith("|"):
                self.add(cap.no, "図は画像 1 つと、任意の 1 行の説明文だけです")
                valid = False
            else:
                caption = _runs(cap.s)
        if len(body) > 2:
            self.add(body[2].no, "図の説明文は 1 行までです")
            valid = False
        if image is None or not valid:
            return None
        alt, ref, grid = image
        return Figure(heading, alt, ref, grid, caption)

    # --- 表 ---

    @staticmethod
    def _cells(s: str) -> list[str]:
        s = s.strip()
        s = s.removeprefix("|").removesuffix("|")
        return [c.strip() for c in s.split("|")]

    def _table(self, heading: str, body: list[_Line]) -> Table | None:
        head = body[0]
        for ln in body:
            if not ln.s.startswith("|"):
                self.add(ln.no, "表の行は `|` で始めます。表と他の内容は混ぜられません")
                return None
        header = self._cells(head.s)
        n = len(header)
        ok = True
        if not MIN_COLUMNS <= n <= MAX_COLUMNS:
            self.add(head.no, f"表の列は {MIN_COLUMNS}〜{MAX_COLUMNS} 列です（{n} 列あります）")
            ok = False
        if len(body) < 2:
            self.add(head.no, "表には見出し行の次に区切り行（`|---|---|`）が要ります")
            return None
        sep = body[1]
        sep_cells = self._cells(sep.s)
        if not all(_TABLE_SEPARATOR_CELL.match(c) for c in sep_cells):
            self.add(sep.no, "表の見出し行の次は区切り行（`|---|---|`）にしてください")
            return None
        if len(sep_cells) != n:
            self.add(sep.no, f"区切り行の列数 {len(sep_cells)} が見出し行の {n} と違います")
            ok = False
        data = body[2:]
        if not data:
            self.add(head.no, "表には本文の行が 1 行以上要ります")
            return None
        if len(data) > MAX_TABLE_ROWS:
            self.add(
                data[MAX_TABLE_ROWS].no,
                f"表の本文は {MAX_TABLE_ROWS} 行までです（{MAX_TABLE_ROWS + 1} 行目）",
            )
            ok = False
        rows: list[list[Text]] = []
        for ln in data:
            cells = self._cells(ln.s)
            if len(cells) != n:
                self.add(ln.no, f"行の列数 {len(cells)} が見出し行の {n} と違います")
                ok = False
            rows.append([_runs(c) for c in cells])
        if not ok:
            return None
        return Table(heading, [_runs(c) for c in header], rows)

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
            for ln in lines:
                m = _BULLET.match(ln.raw)
                assert m is not None
                if not m.group(1).strip():
                    self.add(ln.no, "箇条書きの項目が空です")
                items.append(_runs(m.group(1).strip()))
            return BulletsBlock(items)
        stray = next((ln for ln in lines if _BULLET.match(ln.raw)), None)
        if len(lines) > 1:
            extra = lines[1] if stray is None or stray is lines[0] else stray
            self.add(extra.no, what)
            return None
        only = lines[0]
        if _IMAGE.match(only.s):
            image = self._image(only)
            if image is None:
                return None
            return ImageBlock(*image)
        if only.s.startswith("|"):
            self.add(only.no, what)
            return None
        return TextBlock(_runs(only.s))


def parse(text: str, base_dir: Path) -> Deck:
    parser = _Parser(Path(base_dir))
    deck = parser.run(text)
    if parser.problems:
        raise ManuscriptError(sorted(parser.problems, key=lambda p: p.line))
    return deck
