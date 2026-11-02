"""Analytical layer: decomposition, change-point, outlier, lag and mix-shift tests.

All functions are pure (DataFrames in, small result objects out) so they can be unit-tested.
No scipy: the few tests we need are implemented with numpy/math. Where a p-value would be
misleading (autocorrelated weekly series, tiny n) we report effect sizes and say so.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from analytics import metrics as mx


# ---------------------------------------------------------------------------
# 1. Why did weekly scam loss fall?  loss = cases x loss-per-case (exact decomposition)
# ---------------------------------------------------------------------------


@dataclass
class Decomposition:
    peak_start: pd.Timestamp
    peak_end: pd.Timestamp
    trough_start: pd.Timestamp
    trough_end: pd.Timestamp
    loss_peak: float          # mean weekly loss, baht
    loss_trough: float
    cases_effect: float       # baht/week contributed by change in cases
    severity_effect: float    # baht/week contributed by change in loss per case
    cases_peak: float
    cases_trough: float
    lpc_peak: float
    lpc_trough: float

    @property
    def delta(self) -> float:
        return self.loss_trough - self.loss_peak

    @property
    def severity_share(self) -> float:
        return self.severity_effect / self.delta * 100 if self.delta else float("nan")


def decompose_loss(weekly: pd.DataFrame, window: int = 8) -> Decomposition | None:
    """Compare the highest and lowest `window`-week rolling mean of weekly loss (usable weeks).

    mean loss = mean cases x (sum loss / sum cases). dL = dC * S1 + C2 * dS holds exactly.
    """
    u = mx.usable_weeks(weekly).reset_index(drop=True)
    if len(u) < window * 2:
        return None
    roll = u["acsc_loss_baht"].rolling(window).mean()
    i_peak, i_trough = int(roll.idxmax()), int(roll.idxmin())
    p = u.iloc[i_peak - window + 1: i_peak + 1]
    q = u.iloc[i_trough - window + 1: i_trough + 1]
    c1, c2 = p["acsc_cases"].mean(), q["acsc_cases"].mean()
    s1 = p["acsc_loss_baht"].sum() / p["acsc_cases"].sum()
    s2 = q["acsc_loss_baht"].sum() / q["acsc_cases"].sum()
    return Decomposition(
        p["week_start"].iloc[0], p["week_end"].iloc[-1], q["week_start"].iloc[0], q["week_end"].iloc[-1],
        p["acsc_loss_baht"].mean(), q["acsc_loss_baht"].mean(), (c2 - c1) * s1, c2 * (s2 - s1), c1, c2, s1, s2)


# ---------------------------------------------------------------------------
# 2. Single change-point (binary split minimising within-segment squared error)
# ---------------------------------------------------------------------------


@dataclass
class ChangePoint:
    index: int
    date: pd.Timestamp
    mean_before: float
    mean_after: float
    pct_change: float
    variance_explained: float   # share of total SSE removed by the split (0-1)
    p_permutation: float        # indicative only: ignores autocorrelation


def _best_split(y: np.ndarray, min_seg: int) -> tuple[int, float]:
    n, best_k, best_sse = len(y), -1, np.inf
    for k in range(min_seg, n - min_seg + 1):
        a, b = y[:k], y[k:]
        sse = ((a - a.mean()) ** 2).sum() + ((b - b.mean()) ** 2).sum()
        if sse < best_sse:
            best_k, best_sse = k, sse
    return best_k, best_sse


def change_point(values: pd.Series, dates: pd.Series, min_seg: int = 6, n_perm: int = 1000, seed: int = 0) -> ChangePoint | None:
    y = values.to_numpy(dtype=float)
    if len(y) < 2 * min_seg + 1:
        return None
    k, sse = _best_split(y, min_seg)
    total = ((y - y.mean()) ** 2).sum()
    rng = np.random.default_rng(seed)
    better = sum(_best_split(rng.permutation(y), min_seg)[1] <= sse for _ in range(n_perm))
    a, b = y[:k].mean(), y[k:].mean()
    return ChangePoint(k, pd.Timestamp(dates.iloc[k]), a, b, (b - a) / a * 100, 1 - sse / total, (better + 1) / (n_perm + 1))


# ---------------------------------------------------------------------------
# 3. Outliers: robust z-score (median / MAD) -- why a week is excluded
# ---------------------------------------------------------------------------


def robust_z(weekly: pd.DataFrame, col: str = "acsc_cases") -> pd.DataFrame:
    r = weekly[weekly["acsc_reported"]].copy()
    med = r[col].median()
    mad = (r[col] - med).abs().median() * 1.4826
    r["robust_z"] = (r[col] - med) / mad if mad else np.nan
    r["median"] = med
    r["flagged"] = r["robust_z"].abs() > 3.5
    return r[["week_start", col, "median", "robust_z", "flagged", "acsc_suspect"]]


# ---------------------------------------------------------------------------
# 4. Do fake-news share and scam numbers move together? (detrended, lagged)
# ---------------------------------------------------------------------------


def _full_weekly(weekly: pd.DataFrame, col: str, use_usable: bool) -> pd.Series:
    u = mx.usable_weeks(weekly) if use_usable else weekly
    start, end = u["week_start"].min(), u["week_start"].max()
    s = weekly.set_index("week_start")[col]
    if use_usable:
        s = s.where(weekly.set_index("week_start")["acsc_usable"])
    return s.loc[start:end]


def lagged_correlation(weekly: pd.DataFrame, target: str = "acsc_cases", driver: str = "afnc_false_share_pct",
                       max_lag: int = 4) -> pd.DataFrame:
    """corr(d target_t, d driver_{t-lag}) on week-over-week changes; both series on a gap-free calendar.

    Positive lag = the driver (fake-news share) leads the target (scam numbers).
    Differencing removes the shared downward drift that would otherwise fake a correlation.
    """
    y = _full_weekly(weekly, target, True).diff()
    x = _full_weekly(weekly, driver, False).reindex(y.index).diff()
    rows = []
    for lag in range(-max_lag, max_lag + 1):
        pair = pd.concat([y, x.shift(lag)], axis=1).dropna()
        n = len(pair)
        r = float(pair.iloc[:, 0].corr(pair.iloc[:, 1])) if n > 3 else float("nan")
        rows.append({"lag": lag, "r": r, "n": n, "ci95": 1.96 / math.sqrt(n) if n > 3 else float("nan")})
    out = pd.DataFrame(rows)
    out["significant"] = out["r"].abs() > out["ci95"]
    return out


def detrended_correlation(weekly: pd.DataFrame, target: str = "acsc_cases", driver: str = "afnc_false_share_pct") -> dict:
    """Pearson r of the raw levels vs of the residuals after removing a linear time trend from each."""
    u = mx.usable_weeks(weekly).dropna(subset=[target, driver])
    t = np.arange(len(u), dtype=float)

    def resid(v: np.ndarray) -> np.ndarray:
        return v - np.polyval(np.polyfit(t, v, 1), t)

    y, x = u[target].to_numpy(float), u[driver].to_numpy(float)
    return {"n": len(u), "raw": float(np.corrcoef(x, y)[0, 1]), "detrended": float(np.corrcoef(resid(x), resid(y))[0, 1]),
            "ci95": 1.96 / math.sqrt(len(u))}


# ---------------------------------------------------------------------------
# 5. Category mix shift of false news
# ---------------------------------------------------------------------------


@dataclass
class MixShift:
    table: pd.DataFrame        # years x categories (counts)
    residuals: pd.DataFrame    # standardised Pearson residuals
    chi2: float
    dof: int
    cramers_v: float


def mix_shift(monthly: pd.DataFrame, year_from: int = 2020, year_to: int = 2025) -> MixShift:
    f = monthly[monthly["verdict_en"].isin(["Fake", "Distorted"])].copy()
    f["year"] = f["month_start"].dt.year
    f = f[(f["year"] >= year_from) & (f["year"] <= year_to)]
    tab = f.pivot_table(index="year", columns="category_th", values="n", aggfunc="sum", fill_value=0)
    tab = tab.loc[:, tab.sum() > 0]
    obs = tab.to_numpy(float)
    exp = obs.sum(1, keepdims=True) * obs.sum(0, keepdims=True) / obs.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum((obs - exp) ** 2 / exp)
        res = (obs - exp) / np.sqrt(exp * (1 - obs.sum(1, keepdims=True) / obs.sum()) * (1 - obs.sum(0, keepdims=True) / obs.sum()))
    dof = (obs.shape[0] - 1) * (obs.shape[1] - 1)
    v = math.sqrt(chi2 / (obs.sum() * (min(obs.shape) - 1))) if min(obs.shape) > 1 else float("nan")
    return MixShift(tab, pd.DataFrame(res, index=tab.index, columns=tab.columns), float(chi2), dof, v)


def two_proportion_z(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float]:
    """z and two-sided p for H0: p1 == p2."""
    p1, p2, p = x1 / n1, x2 / n2, (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se if se else float("nan")
    return z, math.erfc(abs(z) / math.sqrt(2))


def false_share_trend(yearly: pd.DataFrame, y0: int = 2020, y1: int = 2025) -> dict:
    a, b = yearly[yearly["year"] == y0].iloc[0], yearly[yearly["year"] == y1].iloc[0]
    z, p = two_proportion_z(int(a["afnc_false"]), int(a["afnc_verdicts"]), int(b["afnc_false"]), int(b["afnc_verdicts"]))
    return {"y0": y0, "y1": y1, "share0": a["afnc_false"] / a["afnc_verdicts"] * 100, "share1": b["afnc_false"] / b["afnc_verdicts"] * 100,
            "z": z, "p": p}


# ---------------------------------------------------------------------------
# 6. AIID growth, Freedom on the Net peers
# ---------------------------------------------------------------------------


def cagr(first: float, last: float, years: int) -> float:
    return ((last / first) ** (1 / years) - 1) * 100 if first > 0 and years > 0 else float("nan")


def aiid_growth_rates(yearly: pd.DataFrame, y0: int = 2022, y1: int = 2025) -> dict:
    a, b = yearly[yearly["year"] == y0].iloc[0], yearly[yearly["year"] == y1].iloc[0]
    out = {"y0": y0, "y1": y1}
    for col in ("incidents", "deepfake", "scam"):
        out[col + "_x"] = b[col] / a[col] if a[col] else float("nan")
        out[col + "_cagr"] = cagr(a[col], b[col], y1 - y0)
    out["deepfake0"], out["scam0"] = int(a["deepfake"]), int(a["scam"])
    out["deepfake_share0"], out["deepfake_share1"] = a["deepfake"] / a["incidents"] * 100, b["deepfake"] / b["incidents"] * 100
    out["scam_share0"], out["scam_share1"] = a["scam"] / a["incidents"] * 100, b["scam"] / b["incidents"] * 100
    return out


def asean_standing(fotn: pd.DataFrame, year: int, iso3: str = "THA", asean: dict | None = None) -> dict:
    from config import ASEAN
    peers = fotn[(fotn["data_year"] == year) & fotn["iso3"].isin(asean or ASEAN)].sort_values("total_score", ascending=False)
    me = peers[peers["iso3"] == iso3].iloc[0]
    others = peers[peers["iso3"] != iso3]
    return {
        "rank": int((peers["total_score"] > me["total_score"]).sum() + 1), "n": len(peers),
        "score": int(me["total_score"]), "median_others": float(others["total_score"].median()),
        "gap_to_median": float(me["total_score"] - others["total_score"].median()),
        "weakest_component": min(("สิทธิผู้ใช้", me["pct_rights"]), ("การจำกัดเนื้อหา", me["pct_content"]), ("อุปสรรคการเข้าถึง", me["pct_access"]), key=lambda t: t[1]),
        "table": peers[["country", "total_score", "pct_access", "pct_content", "pct_rights"]],
    }
