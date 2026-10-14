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
PT_CELL_SMALL = 16  # 18pt で入らない表を 1 段だけ小さくする（design.md D6）
PT_COLUMN_BULLET = 22
PT_COLUMN_TEXT = 22
PT_PAGE_NUMBER = 12

# 一言の補足（design.md D4）。
PT_STATEMENT_NOTE = 24
STATEMENT_NOTE_GAP_PT = 12  # 一言と補足の間、補足どうしの間

# 構成図（design.md D3）。
PT_BOX_NAME = 16
PT_BOX_LINE = 12
PT_FLOW_LABEL = 12  # 矢印のラベル、枠のラベル、× の文
PT_CROSS = 32
PT_FLOW_NOTE = 16

# 添え訳（design.md「合意事項」）。大きさは本文の 60% を整数の pt に丸める。
GLOSS_RATIO = 0.6
MAX_GLOSS_LINES = 2  # 添え訳の行数の上限


def gloss_pt(pt: float) -> int:
    """本文の大きさ（pt）から添え訳の大きさ（pt）。四捨五入した整数。"""
    return math.floor(pt * GLOSS_RATIO + 0.5)


# 枠の高さ（インチ）と行の高さ。メイリオの行の高さは 1.5em（design.md「2026-10-09 枠の高さも判定する」）。
# render が枠を描くのにも、manuscript が収まるかの判定にも、ここを使う。
LINE_HEIGHT_FACTOR = 1.5
BODY_BOX_H = 4.9  # 箇条書き・2 列の本文・表の下端までの高さ（見出しの下 1.8in から）
BULLET_GAP_PT = 12  # 箇条書きの項目の間
COLUMN_BULLET_GAP_PT = 10  # 2 列の箇条書きの項目の間
STATEMENT_BOX_H = 6.3  # 一言の枠の高さ（7.5 - 2 * 見出しの上端 0.6）
TABLE_ROW_H = 0.6  # 表の行の最低の高さ
CELL_MARGIN_V = 0.05  # 表のセルの上下の余白（それぞれ）


def text_width_em(text: str) -> float:
    """全角（W・F）は 1.0em、それ以外は 0.6em として合計する。"""
    return sum(FULL_EM if unicodedata.east_asian_width(ch) in "WF" else HALF_EM for ch in text)


def line_count(text: str, font_pt: float, box_width_in: float) -> int:
    """合計幅 ÷ 枠の幅（em）の切り上げ。和文はどこでも折り返せるものとする。"""
    box_em = box_width_in * 72 / font_pt
    return math.ceil(text_width_em(text) / box_em - _EPS)


def break_line_count(text: str, font_pt: float, box_width_in: float) -> int:
    """改行（`\\n`）で分けた部分ごとの `line_count` の合計。改行のない文は `line_count` と同じ。"""
    return sum(line_count(part, font_pt, box_width_in) for part in text.split("\n"))


def text_height_in(lines: int, font_pt: float) -> float:
    """行数 × 文字の大きさ × 行の高さの係数 ÷ 72 インチ。"""
    return lines * font_pt * LINE_HEIGHT_FACTOR / 72


def table_row_height_in(
    lines: int, font_pt: float, gloss_lines: int = 0, gloss_font_pt: float = 0
) -> float:
    """表のセル 1 つが決める行の高さ。最低の高さより内容が高ければ、行が伸びる。

    gloss_lines が 0 でなければ、本文の段落の下に添え訳の段落が積まれる。"""
    content = text_height_in(lines, font_pt)
    if gloss_lines:
        content += text_height_in(gloss_lines, gloss_font_pt)
    return max(TABLE_ROW_H, content + 2 * CELL_MARGIN_V)
