"""Short-horizon forecasting with honest back-testing.

Five simple models are compared on a rolling-origin back-test; the one with the lowest RMSE is used. If the series is too short,
nothing is forecast. The prediction band is approximate (+/- 1.96 x back-test RMSE) and is labelled as such in the dashboard.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

MODELS = ["Naive", "Moving average", "Exponential smoothing", "Holt (damped trend)", "ARIMA(1,1,1)"]


def _predict(name: str, train: np.ndarray, h: int) -> np.ndarray:
    if name == "Naive":
        return np.repeat(train[-1], h)
    if name == "Moving average":
        return np.repeat(train[-min(4, len(train)):].mean(), h)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from statsmodels.tsa.arima.model import ARIMA
        from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
        try:
            if name == "Exponential smoothing":
                return np.asarray(SimpleExpSmoothing(train, initialization_method="estimated").fit().forecast(h))
            if name == "Holt (damped trend)":
                return np.asarray(ExponentialSmoothing(train, trend="add", damped_trend=True, initialization_method="estimated").fit().forecast(h))
            if name == "ARIMA(1,1,1)":
                return np.asarray(ARIMA(train, order=(1, 1, 1)).fit().forecast(h))
        except Exception:  # noqa: BLE001 - a model that fails to fit simply drops out of the comparison
            return np.full(h, np.nan)
    raise ValueError(name)


@dataclass
class ForecastResult:
    ok: bool
    reason: str = ""
    model: str = ""
    horizon: int = 0
    metrics: pd.DataFrame = field(default_factory=pd.DataFrame)      # model, MAE, RMSE, n_points
    backtest: pd.DataFrame = field(default_factory=pd.DataFrame)     # date, actual, predicted (best model)
    forecast: pd.DataFrame = field(default_factory=pd.DataFrame)     # date, forecast, lower, upper
    history: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))


def forecast_series(y: pd.Series, horizon: int, min_obs: int, freq: str, n_origins: int = 10) -> ForecastResult:
    """y: numeric series with a regular DatetimeIndex (gaps already handled by the caller)."""
    y = y.astype(float).dropna()
    if len(y) < min_obs:
        return ForecastResult(False, f"ไม่มีข้อมูลเพียงพอสำหรับการวิเคราะห์นี้: มี {len(y)} จุด (ต้องการอย่างน้อย {min_obs})", history=y)
    vals = y.to_numpy()
    n = len(vals)
    origins = list(range(max(min_obs // 2, n - n_origins - horizon + 1), n - horizon + 1))
    rows, preds = [], {}
    for m in MODELS:
        errs, pts = [], []
        for t in origins:
            p = _predict(m, vals[:t], horizon)
            if np.isnan(p).any():
                errs = []
                break
            e = vals[t:t + horizon] - p
            errs.extend(e.tolist())
            pts.append((t, p))
        if errs:
            rows.append({"model": m, "MAE": float(np.mean(np.abs(errs))), "RMSE": float(np.sqrt(np.mean(np.square(errs)))), "n_points": len(errs)})
            preds[m] = pts
    metrics = pd.DataFrame(rows).sort_values("RMSE").reset_index(drop=True)
    if metrics.empty:
        return ForecastResult(False, "ไม่สามารถประเมินแบบจำลองได้ (แบบจำลองทุกแบบล้มเหลว)", history=y)
    best = metrics.iloc[0]["model"]
    # back-test table of the chosen model: first step of each origin (a "1-step-ahead" view)
    bt = pd.DataFrame([{"date": y.index[t], "actual": vals[t], "predicted": p[0]} for t, p in preds[best]])
    yhat = _predict(best, vals, horizon)
    rmse = float(metrics.iloc[0]["RMSE"])
    idx = pd.date_range(y.index[-1], periods=horizon + 1, freq=freq)[1:]
    fc = pd.DataFrame({"date": idx, "forecast": yhat, "lower": np.maximum(yhat - 1.96 * rmse, 0), "upper": yhat + 1.96 * rmse})
    return ForecastResult(True, "", best, horizon, metrics, bt, fc, y)
