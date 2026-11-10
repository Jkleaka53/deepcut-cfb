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


def test_bar_on_keeps_team_hue():
    import colorsys

    from cfbm.colors import bar_on, contrast
    for primary in ("#00274c", "#007030", "#002855", "#841617"):
        out = bar_on("#13171c", primary)
        assert contrast(out, "#13171c") >= 3
        h0 = colorsys.rgb_to_hls(*(int(primary[i:i + 2], 16) / 255 for i in (1, 3, 5)))[0]
        h1 = colorsys.rgb_to_hls(*(int(out[i:i + 2], 16) / 255 for i in (1, 3, 5)))[0]
        assert abs(h0 - h1) < 0.03
    assert bar_on("#13171c", "#ffcb05") == "#ffcb05"
    assert bar_on("#13171c", None) == "#8e9aab"
