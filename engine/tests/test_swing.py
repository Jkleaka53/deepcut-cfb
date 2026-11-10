import pandas as pd

from cfbm.swing import swing_block
from cfbm.swing_data import KEYS


def feat(proven=True, importance=0.5, vol=1.3, side_mean=0.0, side_sd=0.1):
    return {"coef": importance, "lo": 0.1 if proven else -0.1, "hi": 0.9, "proven": proven, "importance": importance,
            "volatility": vol, "mean": 0.0, "sd": 1.0, "sideMean": side_mean, "sideSd": side_sd}


MODEL = {"features": {k: feat(proven=k in ("pass_ppa", "sd_sr", "pd_sr", "explosive"),
                              importance={"sd_sr": 0.8, "pass_ppa": 0.35, "pd_sr": 0.33, "explosive": 0.25}.get(k, 0.1))
                      for k in KEYS}}


def pre(**teams):
    """teams: name -> (games, {key: (off, def_allowed)}) ; unspecified keys 0/0."""
    rows = {}
    for t, (g, vals) in teams.items():
        row = {"games": g}
        for k in KEYS:
            o, d = vals.get(k, (0.0, 0.0))
            row[f"off_{k}"], row[f"def_{k}"] = o, d
        rows[t] = row
    filler = {f"T{i}": {"games": 5, **{f"{s}_{k}": (i - 10) / 100 for k in KEYS for s in ("off", "def")}} for i in range(20)}
    return pd.DataFrame.from_dict({**filler, **rows}, orient="index")


def test_drivers_ranked_by_score_and_only_proven():
    p = pre(Oregon=(8, {"pass_ppa": (0.30, -0.10), "sd_sr": (0.10, -0.05)}),
            Michigan=(8, {"pass_ppa": (0.0, 0.25), "sd_sr": (0.0, 0.10), "rush_sr": (0.9, 0.9)}))
    out = swing_block(MODEL, "Oregon", "Michigan", p, neutral=False)
    keys = [(d["key"], d["offense"]) for d in out["drivers"]]
    assert all(k in ("pass_ppa", "sd_sr", "pd_sr", "explosive") for k, _ in keys)
    scores = [d["score"] for d in out["drivers"]]
    assert scores == sorted(scores, reverse=True) and len(out["drivers"]) <= 5
    top = out["drivers"][0]
    assert top["label"] and top["cue"] and top["favors"] in ("Oregon", "Michigan")
    assert top["offRank"] >= 1 and top["of"] == 22


def test_gap_floor_and_even_note():
    p = pre(Oregon=(8, {}), Michigan=(8, {}))
    out = swing_block(MODEL, "Oregon", "Michigan", p, neutral=False)
    assert out["drivers"] == []
    assert out["note"] == "No big swing factors: these teams match up evenly on the stats the model trusts."


def test_early_season_side_skipped_with_note():
    p = pre(Oregon=(2, {"pass_ppa": (0.5, 0.0)}), Michigan=(8, {"pass_ppa": (0.5, 0.3)}))
    out = swing_block(MODEL, "Oregon", "Michigan", p, neutral=False)
    assert out["drivers"] == []
    assert out["note"] == "Too early in the season: Oregon has fewer than 3 games against FBS teams."
    assert out["overallEdge"] is None


def test_overall_edge_favors_the_better_team():
    p = pre(Oregon=(8, {k: (0.4, -0.3) for k in KEYS}), Michigan=(8, {k: (-0.3, 0.4) for k in KEYS}))
    e = swing_block(MODEL, "Oregon", "Michigan", p, neutral=False)["overallEdge"]
    assert e["team"] == "Oregon" and e["edge"] in ("slight", "clear")


def test_key_rows_map_passing_parents():
    p = pre(Oregon=(8, {"pass_ppa": (0.4, 0.0), "pd_sr": (0.4, 0.0)}), Michigan=(8, {"pass_ppa": (0.0, 0.4), "pd_sr": (0.0, 0.4)}))
    out = swing_block(MODEL, "Oregon", "Michigan", p, neutral=False)
    assert set(out["keyRows"]["Oregon"]) <= {"epa_per_db", "pd_epa", "success_rate"}
    assert "epa_per_db" in out["keyRows"]["Oregon"]


def test_even_matchups_are_not_drivers_and_favors_matches_ranks():
    import copy
    # A baseline far below every team makes z positive (offense-favoring) for every unit pair.
    shifted = copy.deepcopy(MODEL)
    for f in shifted["features"].values():
        f["sideMean"] = -0.5
    p = pre(Oregon=(8, {"pass_ppa": (-0.05, 0.0), "sd_sr": (0.0, 0.0)}),
            Michigan=(8, {"pass_ppa": (0.0, -0.09), "sd_sr": (0.0, 0.0)}))
    drivers = swing_block(shifted, "Oregon", "Michigan", p, neutral=False)["drivers"]
    assert drivers, "baseline shift should still leave real gaps"
    for d in drivers:
        better = d["offense"] if d["offRank"] < d["defRank"] else d["defense"]
        assert d["edge"] != "even" and d["favors"] == better


def test_missing_stat_for_a_team_skips_that_factor():
    p = pre(Oregon=(8, {"pass_ppa": (0.4, 0.0)}), Michigan=(8, {"pass_ppa": (0.0, 0.4)}))
    p.loc["Oregon", "off_sd_sr"] = float("nan")
    out = swing_block(MODEL, "Oregon", "Michigan", p, neutral=False)
    assert not any(d["key"] == "sd_sr" and d["offense"] == "Oregon" for d in out["drivers"])


def test_key_rows_map_run_parents():
    import copy
    p = pre(Oregon=(8, {"stuff": (-0.2, 0.0), "line_yards": (4.0, 2.0)}),
            Michigan=(8, {"stuff": (0.0, -0.2), "line_yards": (2.0, 4.0)}))
    model = copy.deepcopy(MODEL)
    for k in ("stuff", "line_yards"):
        model["features"][k].update(proven=True, importance=0.9)
    out = swing_block(model, "Oregon", "Michigan", p, neutral=False)
    keys = {d["key"] for d in out["drivers"] if d["offense"] == "Oregon"}
    want = {"stuff": "stuff_rate", "line_yards": "line_yards"}
    assert keys & set(want), "fixture should yield a run driver for Oregon"
    for k in keys & set(want):
        assert want[k] in out["keyRows"]["Oregon"]
