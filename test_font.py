from font import get_font


def test_get_font() -> None:
    a = get_font(16, "normal", "roman")
    b = get_font(16, "normal", "roman")
    c = get_font(20, "normal", "roman")
    d = get_font(16, "bold", "roman")
    assert a is b
    assert a is not c
    assert a is not d
