from slidekit import inline, manuscript


def test_runs_split_emphasis():
    assert inline.runs("a**b**c") == (
        inline.Run("a"),
        inline.Run("b", emphasis=True),
        inline.Run("c"),
    )
    assert inline.runs("plain") == (inline.Run("plain"),)
    assert inline.runs("**b**") == (inline.Run("b", emphasis=True),)


def test_manuscript_reexports_run_and_text():
    assert manuscript.Run is inline.Run
    assert manuscript.Text is inline.Text


def test_is_emoji():
    assert inline.is_emoji("🚀")
    assert inline.is_emoji("️")
    assert not inline.is_emoji("あ")
    assert not inline.is_emoji("a")


def test_inline_problems_clean():
    assert inline.inline_problems("ふつうの **強調** 文") == []


def test_inline_problems_reasons():
    assert inline.inline_problems("`x`") == ["インラインコード（`` ` ``）は使えません"]
    assert inline.inline_problems("[a](b)") == ["リンクは使えません"]
    assert inline.inline_problems("__x__") == [
        "`__強調__` は使えません。強調は `**語句**` だけです"
    ]
    assert inline.inline_problems("~~x~~") == ["`~~取り消し~~` は使えません"]
    assert inline.inline_problems("*x*") == ["`*強調*` は使えません。強調は `**語句**` だけです"]
    assert inline.inline_problems("**x") == ["強調の `**` が閉じていません"]
