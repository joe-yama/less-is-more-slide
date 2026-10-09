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
