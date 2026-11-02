"""Filter helpers: the numbers must change exactly as the selection says."""
import pandas as pd

from analytics import filters as ft


def _m():
    rows = []
    for y, cat, v, n in [(2020, "A", "Fake", 60), (2020, "A", "True", 20), (2020, "B", "Fake", 20),
                         (2021, "A", "Fake", 10), (2021, "B", "Distorted", 30), (2021, "B", "True", 60)]:
        rows.append({"month_start": pd.Timestamp(f"{y}-03-01"), "category_th": cat, "verdict_en": v, "n": n})
    return pd.DataFrame(rows)


def test_year_and_category_filter():
    f = ft.afnc_filtered(_m(), 2021, 2021, ["B"])
    assert f["n"].sum() == 90 and set(f["category_th"]) == {"B"}


def test_verdict_year_table_totals_and_missing_verdicts():
    t = ft.verdict_year_table(ft.afnc_filtered(_m(), 2020, 2021, ["A", "B"])).set_index("year")
    assert t.loc[2020, "afnc_verdicts"] == 100 and t.loc[2020, "afnc_distorted"] == 0
    assert t.loc[2021, "afnc_false"] == 40


def test_category_share_renormalises_over_selection():
    f = ft.afnc_filtered(_m(), 2020, 2020, ["A", "B"])
    s = ft.category_share_selected(f, ["Fake", "Distorted"]).set_index("category_th")
    assert s.loc["A", "share_pct"] == 75 and s.loc["B", "share_pct"] == 25
    only_a = ft.category_share_selected(ft.afnc_filtered(_m(), 2020, 2020, ["A"]), ["Fake"])
    assert only_a["share_pct"].iloc[0] == 100


def test_overall_false_share_and_empty():
    assert round(ft.overall_false_share(_m()), 1) == round((60 + 20 + 10 + 30) / 200 * 100, 1)
    assert pd.isna(ft.overall_false_share(_m().iloc[0:0]))


def test_slice_weeks_inclusive():
    w = pd.DataFrame({"week_start": pd.date_range("2026-01-04", periods=5, freq="7D")})
    s = ft.slice_weeks(w, "2026-01-11", "2026-01-25")
    assert len(s) == 3 and s["week_start"].min() == pd.Timestamp("2026-01-11")


def test_country_options_strips_suffix():
    f = pd.DataFrame({"country": ["Russian Federation (the)", "Thailand"], "iso3": ["RUS", "THA"], "data_year": [2024, 2024]})
    assert ft.country_options(f) == {"Russian Federation": "RUS", "Thailand": "THA"}
