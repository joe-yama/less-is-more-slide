"""文字幅の見積もりと行数。実際の描画ではなく、安全側に寄せた見積もり。"""

import math
import unicodedata

FULL_EM = 1.0
HALF_EM = 0.6  # メイリオの半角は約 0.55em。安全側に寄せる
_EPS = 1e-9

# design.md「寸法と文字の大きさ」。文字の大きさ（pt）。render と manuscript の両方がここを使う。
PT_COVER_TITLE = 40
PT_COVER_LINE = 20
PT_HEADING = 30
PT_STATEMENT = 40
PT_BULLET = 24
PT_CAPTION = 20
PT_CELL = 18
PT_COLUMN_BULLET = 22
PT_COLUMN_TEXT = 22
PT_PAGE_NUMBER = 12


def text_width_em(text: str) -> float:
    """全角（W・F）は 1.0em、それ以外は 0.6em として合計する。"""
    return sum(FULL_EM if unicodedata.east_asian_width(ch) in "WF" else HALF_EM for ch in text)


def line_count(text: str, font_pt: float, box_width_in: float) -> int:
    """合計幅 ÷ 枠の幅（em）の切り上げ。和文はどこでも折り返せるものとする。"""
    box_em = box_width_in * 72 / font_pt
    return math.ceil(text_width_em(text) / box_em - _EPS)
