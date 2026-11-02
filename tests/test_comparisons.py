"""Tests for the comparison analyses (synthetic data with known answers)."""
import numpy as np
import pandas as pd

from analytics import comparisons as cp


def test_rolling_robust_z_flags_planted_spike_only():
    rng = np.random.default_rng(0)
    v = pd.Series(50 + rng.normal(0, 2, 60))
    v.iloc[30] = 90
    r = cp.rolling_robust_z(v)
    assert r["z"].abs().idxmax() == 30 and r.loc[30, "z"] > 3.5
    assert (r["z"].drop(30).dropna().abs() < 3.5).all()


def test_rolling_robust_z_follows_level_shift():
    v = pd.Series(np.r_[np.full(30, 100.0), np.full(30, 40.0)] + np.tile([0, 1, -1], 20))
    r = cp.rolling_robust_z(v)
    assert (r["z"].dropna().abs() < 3.5).all()  # a new level is not an anomaly once the window has moved on


def _weekly(cases, lpc):
    n = len(cases)
    ws = pd.date_range("2026-01-04", periods=n, freq="7D")
    c = np.asarray(cases, float)
    return pd.DataFrame({"week_start": ws, "week_end": ws + pd.Timedelta(days=6), "acsc_usable": True, "acsc_reported": True,
                         "acsc_suspect": False, "acsc_cases": c, "acsc_loss_baht": c * np.asarray(lpc, float)})


def test_cases_down_severity_up_detects_block():
    w = _weekly([100] * 4 + [80] * 4 + [60] * 4, [10] * 4 + [12] * 4 + [8] * 4)
    r = cp.cases_down_severity_up(w, span=4)
    assert list(r["cases_down_lpc_up"]) == [True, False]


def test_cases_loss_relation_elasticity():
    cases = np.linspace(5000, 8000, 30)
    w = _weekly(cases, np.full(30, 50_000.0))           # loss proportional to cases -> elasticity 1
    r = cp.cases_loss_relation(w)
    assert abs(r["elasticity"] - 1) < 1e-6 and r["r"] > 0.99


def test_rising_topics_share_change():
    counts = pd.DataFrame({"year": [2020, 2020, 2022, 2022], "topic": ["a", "b", "a", "b"], "n": [10, 90, 50, 50]})
    r = cp.rising_topics(counts, pd.Series({2020: 100, 2022: 100}), "topic", 2020, 2022, min_count=1).set_index("topic")
    assert r.loc["a", "change_pp"] == 40 and r.loc["b", "change_pp"] == -40


def test_overlap_status_labels():
    assert cp.overlap_status(18, 12, 1400) == "ซ้อนทับ"
    assert cp.overlap_status(41, 0.3, 28) == "เฝ้าระวัง"
    assert cp.overlap_status(1.3, 4.0, 433) == "เด่นในไทย"
    assert cp.overlap_status(0.5, 0.5, 10) == "น้อยทั้งสองฝั่ง"


def test_country_link_spearman_and_not_free_list():
    df = pd.DataFrame({"country": list("ABCDEFG"), "iso3": list("abcdefg"), "mentions": [50, 40, 30, 20, 10, 8, 6],
                       "total_score": [10, 20, 30, 40, 50, 60, 70], "status_code": [3, 3, 2, 2, 1, 1, 1]})
    r = cp.country_link(df, min_mentions=5)
    assert abs(r["rho"] + 1) < 1e-9 and list(r["not_free"]["country"]) == ["A", "B"]
