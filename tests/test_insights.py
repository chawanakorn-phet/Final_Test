"""Tests for the analytical layer, using synthetic series with a known answer."""
import numpy as np
import pandas as pd

from analytics import insights as ix


def _weekly(cases, loss=None, driver=None):
    n = len(cases)
    ws = pd.date_range("2026-01-04", periods=n, freq="7D")
    cases = np.asarray(cases, float)
    loss = np.asarray(loss if loss is not None else cases * 50_000, float)
    return pd.DataFrame({
        "week_start": ws, "week_end": ws + pd.Timedelta(days=6), "acsc_reported": True, "acsc_usable": True, "acsc_suspect": False,
        "acsc_cases": cases, "acsc_loss_baht": loss,
        "afnc_false_share_pct": driver if driver is not None else np.full(n, 70.0),
    })


def test_loss_decomposition_is_exact():
    cases = np.r_[np.full(10, 7000), np.full(10, 5000)]
    lpc = np.r_[np.full(10, 60_000), np.full(10, 30_000)]
    d = ix.decompose_loss(_weekly(cases, cases * lpc), window=8)
    assert abs(d.cases_effect + d.severity_effect - d.delta) < 1          # identity holds
    assert abs(d.cases_effect - (-2000 * 60_000)) < 1                     # dC * S1
    assert abs(d.severity_effect - (5000 * -30_000)) < 1                  # C2 * dS
    assert round(d.severity_share) == 56


def test_change_point_finds_planted_break():
    rng = np.random.default_rng(1)
    y = np.r_[rng.normal(100, 3, 25), rng.normal(60, 3, 25)]
    w = _weekly(y)
    cp = ix.change_point(w["acsc_cases"], w["week_start"], n_perm=200)
    assert abs(cp.index - 25) <= 1
    assert cp.pct_change < -35 and cp.variance_explained > 0.9 and cp.p_permutation < 0.02


def test_change_point_none_when_too_short():
    w = _weekly(np.arange(5))
    assert ix.change_point(w["acsc_cases"], w["week_start"]) is None


def test_robust_z_flags_only_the_outlier():
    w = _weekly(np.r_[np.full(20, 6000) + np.arange(20) * 10, 79_000])
    z = ix.robust_z(w)
    assert list(z.loc[z["flagged"], "acsc_cases"]) == [79_000]


def test_lagged_correlation_recovers_planted_lag():
    rng = np.random.default_rng(3)
    n = 80
    driver = np.cumsum(rng.normal(0, 1, n))                  # random walk
    target = np.r_[np.zeros(2), driver[:-2]] * 100 + rng.normal(0, 5, n)   # target follows driver 2 weeks later
    out = ix.lagged_correlation(_weekly(target, driver=driver), max_lag=4).set_index("lag")
    assert out["r"].idxmax() == 2 and out.loc[2, "significant"]


def test_detrended_correlation_removes_shared_drift():
    n = 60
    t = np.arange(n)
    rng = np.random.default_rng(5)
    w = _weekly(10_000 - 50 * t + rng.normal(0, 30, n), driver=80 - 0.2 * t + rng.normal(0, 0.5, n))
    r = ix.detrended_correlation(w)
    assert r["raw"] > 0.9 and abs(r["detrended"]) < 0.3


def test_mix_shift_independent_vs_shifted():
    def build(rows):
        recs = [{"month_start": pd.Timestamp(f"{y}-01-01"), "category_th": c, "verdict_en": "Fake", "n": n} for y, c, n in rows]
        return pd.DataFrame(recs)
    same = build([(2020, "A", 50), (2020, "B", 50), (2021, "A", 100), (2021, "B", 100)])
    shifted = build([(2020, "A", 90), (2020, "B", 10), (2021, "A", 10), (2021, "B", 90)])
    assert ix.mix_shift(same, 2020, 2021).cramers_v < 1e-9
    assert ix.mix_shift(shifted, 2020, 2021).cramers_v > 0.7


def test_two_proportion_and_cagr():
    z, p = ix.two_proportion_z(50, 100, 50, 100)
    assert z == 0 and p == 1
    z, p = ix.two_proportion_z(80, 100, 50, 100)
    assert z < -4 and p < 1e-4
    assert round(ix.cagr(100, 400, 2), 1) == 100.0
