from slidekit.fit import line_count, text_width_em

BODY_WIDTH_IN = 11.53  # design.md の本文領域の幅


def test_fullwidth_is_1em_each():
    assert text_width_em("あいうえお") == 5.0
    assert text_width_em("ＡＢ") == 2.0  # 全角英字は F


def test_halfwidth_is_0_6em_each():
    assert text_width_em("abcde") == 3.0
    assert text_width_em("ｱｲ") == 1.2  # 半角カナは H


def test_mixed():
    assert abs(text_width_em("AIの話") - 3.2) < 1e-9


def test_empty_is_zero():
    assert text_width_em("") == 0.0


def test_heading_15_fullwidth_chars_fit_in_one_line():
    assert line_count("あ" * 15, 30, BODY_WIDTH_IN) == 1


def test_heading_60_fullwidth_chars_need_two_or_more_lines():
    assert line_count("あ" * 60, 30, BODY_WIDTH_IN) >= 2


def test_line_count_is_ceiling_of_width_over_box():
    # 30pt の 1em = 30/72 in。枠 10 in は 24em。
    assert line_count("あ" * 24, 30, 10) == 1
    assert line_count("あ" * 25, 30, 10) == 2
    assert line_count("あ" * 48, 30, 10) == 2
    assert line_count("あ" * 49, 30, 10) == 3


def test_gloss_size_is_60_percent_rounded():
    from slidekit import fit

    assert fit.GLOSS_RATIO == 0.6
    got = {pt: fit.gloss_pt(pt) for pt in (40, 30, 24, 22, 20, 18)}
    assert got == {40: 24, 30: 18, 24: 14, 22: 13, 20: 12, 18: 11}
    assert all(type(v) is int for v in got.values())


def test_gloss_limits():
    from slidekit import fit

    assert fit.MAX_GLOSS_LINES == 2
    assert fit.COLUMN_BULLET_GAP_PT == 10


def test_flow_diagram_sizes():
    from slidekit import fit

    assert fit.PT_BOX_NAME == 16
    assert fit.PT_BOX_LINE == 12
    assert fit.PT_FLOW_LABEL == 12
    assert fit.PT_CROSS == 32
    assert fit.PT_FLOW_NOTE == 16


# --- 改行（`\n`）で分けた部分ごとの行数 ---


def test_break_line_count_sums_the_parts():
    from slidekit.fit import break_line_count

    long = "あ" * 60
    expected = line_count(long, 30, BODY_WIDTH_IN) + line_count("い", 30, BODY_WIDTH_IN)
    assert expected >= 3
    assert break_line_count(long + "\n" + "い", 30, BODY_WIDTH_IN) == expected


def test_break_line_count_without_break_is_line_count():
    from slidekit.fit import break_line_count

    assert break_line_count("あ" * 60, 30, BODY_WIDTH_IN) == line_count(
        "あ" * 60, 30, BODY_WIDTH_IN
    )


def test_break_line_count_two_short_parts_are_two_lines():
    from slidekit.fit import break_line_count

    assert break_line_count("あ\nい", 40, BODY_WIDTH_IN) == 2
