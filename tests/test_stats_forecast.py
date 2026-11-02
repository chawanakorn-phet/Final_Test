"""Statistics gates and forecasting behave as specified (synthetic data, known answers)."""
import numpy as np
import pandas as pd

from analytics import forecast as fc
from analytics import stats as st


def test_correlate_known_values_and_p():
    rng = np.random.default_rng(1)
    x = pd.Series(np.arange(40.0))
    y = x * 2 + rng.normal(0, 1, 40)
    r = st.correlate(x, y, "pearson")
    assert r["ok"] and r["r"] > 0.99 and r["p"] < 1e-10 and r["n"] == 40
    noise = st.correlate(pd.Series(rng.normal(size=60)), pd.Series(rng.normal(size=60)), "spearman")
    assert noise["ok"] and noise["p"] > 0.01


def test_correlate_refuses_small_n_and_constant():
    r = st.correlate(pd.Series([1, 2, 3, 4, 5.0]), pd.Series([2, 1, 4, 3, 5.0]), min_n=10)
    assert not r["ok"] and np.isnan(r["r"]) and "ไม่มีข้อมูลเพียงพอ" in r["reason"] and r["n"] == 5
    c = st.correlate(pd.Series(np.arange(20.0)), pd.Series(np.ones(20)))
    assert not c["ok"]


def test_correlate_drops_nan_pairs_and_counts_complete_pairs():
    x = pd.Series([1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10, 11, 12.0])
    y = pd.Series([2, 4, 6, np.nan, 10, 12, 14, 16, 18, 20, 22, 24.0])
    assert st.correlate(x, y, "pearson")["n"] == 10


def test_interpret_mentions_n_and_causation_guard():
    r = st.correlate(pd.Series(np.arange(30.0)), pd.Series(np.arange(30.0) ** 1.5))
    s = st.interpret(r)
    assert "n = 30" in s and "ไม่ใช่หลักฐานเชิงเหตุและผล" in s


def test_forecast_refuses_short_series():
    y = pd.Series(np.arange(20.0), index=pd.date_range("2026-01-04", periods=20, freq="7D"))
    r = fc.forecast_series(y, horizon=4, min_obs=40, freq="7D")
    assert not r.ok and "ไม่มีข้อมูลเพียงพอ" in r.reason and r.forecast.empty


def test_forecast_picks_trend_model_for_linear_trend():
    idx = pd.date_range("2020-01-01", periods=72, freq="MS")
    y = pd.Series(100 + 3.0 * np.arange(72) + np.random.default_rng(0).normal(0, 1, 72), index=idx)
    r = fc.forecast_series(y, horizon=3, min_obs=36, freq="MS")
    assert r.ok and r.model != "Naive"
    assert r.metrics.set_index("model").loc[r.model, "RMSE"] < r.metrics.set_index("model").loc["Naive", "RMSE"]
    assert len(r.forecast) == 3 and r.forecast["date"].iloc[0] == pd.Timestamp("2026-01-01")
    assert (r.forecast["lower"] <= r.forecast["forecast"]).all() and (r.forecast["forecast"] <= r.forecast["upper"]).all()
    assert r.forecast["forecast"].iloc[0] > y.iloc[-1] - 5  # continues the upward trend


def test_forecast_constant_series_is_flat():
    y = pd.Series(np.full(50, 49.0), index=pd.date_range("2022-01-01", periods=50, freq="MS"))
    r = fc.forecast_series(y, horizon=3, min_obs=36, freq="MS")
    assert r.ok and np.allclose(r.forecast["forecast"], 49.0, atol=1e-3)
    assert r.metrics["RMSE"].min() < 1e-6
