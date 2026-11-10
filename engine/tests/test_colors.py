from cfbm.colors import contrast, fill_for_white_text, text_on


def test_contrast_black_white():
    assert round(contrast("#000000", "#ffffff"), 1) == 21.0


def test_fill_keeps_dark_primary():  # Michigan navy passes behind white
    assert fill_for_white_text("#00274c", "#ffcb05") == "#00274c"


def test_fill_uses_alt_when_primary_fails():  # WVU gold fails, navy alt passes
    assert fill_for_white_text("#eaaa00", "#002855") == "#002855"


def test_fill_darkens_when_both_fail():  # Tennessee orange + white alt
    out = fill_for_white_text("#ff8200", "#ffffff")
    assert contrast(out, "#ffffff") >= 4.5


def test_text_on_dark_card_lightens_navy():
    out = text_on("#13171c", "#00274c", "#ffcb05")
    assert contrast(out, "#13171c") >= 4.5


def test_text_on_white_keeps_navy():
    assert text_on("#ffffff", "#00274c", "#ffcb05") == "#00274c"


def test_bad_hex_falls_back_to_ink():
    assert fill_for_white_text("", None) == "#0b1220"
