"""格子ファイルの解析と検証。"""

from dataclasses import dataclass
from pathlib import Path

from slidekit.palette import GRID_COLORS

MAX_SIZE = 64


@dataclass(frozen=True)
class Problem:
    """違反 1 件。line と col は 1 始まり。col は位置が文字に紐づかないとき None。"""

    line: int
    col: int | None
    message: str


class GridError(Exception):
    def __init__(self, problems: list[Problem]):
        self.problems = problems
        super().__init__("; ".join(_format(p) for p in problems))


def _format(p: Problem) -> str:
    where = f"{p.line} 行目" if p.col is None else f"{p.line} 行目 {p.col} 文字目"
    return f"{where}: {p.message}"


@dataclass(frozen=True)
class Grid:
    width: int
    height: int
    rows: list[str]


def parse_grid(text: str) -> Grid:
    rows = text.splitlines()
    while rows and rows[-1] == "":
        rows.pop()
    if not rows:
        raise GridError([Problem(1, None, "格子が空です")])

    allowed = " ".join(f"`{c}`" for c in GRID_COLORS)
    width = len(rows[0])
    problems: list[Problem] = []

    if width > MAX_SIZE:
        problems.append(Problem(1, None, f"幅 {width} は上限 {MAX_SIZE} ドットを超えています"))
    if len(rows) > MAX_SIZE:
        problems.append(
            Problem(1, None, f"高さ {len(rows)} は上限 {MAX_SIZE} ドットを超えています")
        )
    for i, row in enumerate(rows, start=1):
        if len(row) != width:
            problems.append(Problem(i, None, f"行の長さ {len(row)} が 1 行目の {width} と違います"))
        for j, ch in enumerate(row, start=1):
            if ch not in GRID_COLORS:
                problems.append(
                    Problem(i, j, f"使えない文字 `{ch}` です。使える文字は {allowed} です")
                )
    if problems:
        raise GridError(problems)
    return Grid(width=width, height=len(rows), rows=rows)


ICON_DIR = Path(__file__).resolve().parents[2] / "icons"
ICON_PREFIX = "icon:"


def icon_names() -> list[str]:
    return sorted(p.stem for p in ICON_DIR.glob("*.txt"))


def resolve(ref: str, base_dir: Path) -> Grid:
    """`icon:<名前>` か、base_dir からの相対パスの `.txt` を読んで格子にする。"""
    if ref.startswith(ICON_PREFIX):
        name = ref[len(ICON_PREFIX) :]
        names = icon_names()
        if name not in names:
            listed = "、".join(names)
            raise GridError(
                [Problem(1, None, f"アイコン `{name}` はありません。あるのは {listed}")]
            )
        path = ICON_DIR / f"{name}.txt"
    else:
        path = Path(base_dir) / ref
        if path.suffix != ".txt":
            raise GridError([Problem(1, None, f"格子ファイルは `.txt` だけです: {ref}")])
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise GridError([Problem(1, None, f"格子ファイルを読めません: {ref} ({e})")]) from e
    return parse_grid(text)
