"""行の中の書式（強調・絵文字・使えない記法）。原稿と構成図ファイルが同じ規則を使う。"""

import re
from dataclasses import dataclass

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


def is_emoji(ch: str) -> bool:
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

_EMPHASIS = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)  # 改行（`\n`）をまたぐ強調も 1 つ
_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
_PAIRED_STAR = re.compile(r"\*[^*]+\*")


def runs(text: str) -> Text:
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


def inline_problems(s: str) -> list[str]:
    """行の中の使えない記法の理由。見つけた順ではなく、決まった順に返す。"""
    out: list[str] = []
    if "`" in s:
        out.append("インラインコード（`` ` ``）は使えません")
    if _LINK.search(s):
        out.append("リンクは使えません")
    if re.search(r"__.+?__", s):
        out.append("`__強調__` は使えません。強調は `**語句**` だけです")
    if re.search(r"~~.+?~~", s):
        out.append("`~~取り消し~~` は使えません")
    rest = _EMPHASIS.sub("", s)
    if "**" in rest:
        out.append("強調の `**` が閉じていません")
    if _PAIRED_STAR.search(rest.replace("**", "")):
        out.append("`*強調*` は使えません。強調は `**語句**` だけです")
    return out
