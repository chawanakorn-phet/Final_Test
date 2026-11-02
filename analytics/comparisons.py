"""Analyses for the three research questions that need more than a single table:
rolling anomalies, rising/declining topics, cases-down/severity-up periods, nearest-score peers,
theme overlap (global AI harms vs Thai fact-checks) and the exploratory FOTN-vs-AIID country link.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analytics import metrics as mx


# ---------------------------------------------------------------------------
# Q2: anomalies against the series' own recent level
# ---------------------------------------------------------------------------


def rolling_robust_z(values: pd.Series, window: int = 13, min_periods: int = 8) -> pd.DataFrame:
    """Robust z of each point against the median/MAD of the surrounding `window` points (centred, excluding itself)."""
    v = values.astype(float)
    exp, z = [], []
    half = window // 2
    arr = v.to_numpy()
    for i in range(len(arr)):
        lo, hi = max(0, i - half), min(len(arr), i + half + 1)
        ctx = np.delete(arr[lo:hi], i - lo)
        ctx = ctx[~np.isnan(ctx)]
        if len(ctx) < min_periods or np.isnan(arr[i]):
            exp.append(np.nan)
            z.append(np.nan)
            continue
        med = np.median(ctx)
        mad = np.median(np.abs(ctx - med)) * 1.4826
        mad = max(mad, 0.05 * abs(med), 1.0)  # floor so near-constant series do not explode
        exp.append(med)
        z.append((arr[i] - med) / mad)
    return pd.DataFrame({"value": arr, "expected": exp, "z": z}, index=values.index)


def weekly_anomalies(weekly: pd.DataFrame, z_cut: float = 3.5, year_from: int = 2020) -> pd.DataFrame:
    """Anomalous weeks across the Thai series. Fake-news *counts* are a work quota, so we test false items and false share."""
    w = weekly[weekly["week_start"].dt.year >= year_from].sort_values("week_start").reset_index(drop=True)
    series = {
        "ข่าวเท็จ (เรื่อง/สัปดาห์)": ("afnc_false", w),
        "สัดส่วนข่าวเท็จ (%)": ("afnc_false_share_pct", w),
    }
    u = mx.usable_weeks(weekly).reset_index(drop=True)
    series["คดีหลอกลวง (คดี/สัปดาห์)"] = ("acsc_cases", u)
    series["ความเสียหายต่อคดี (บาท)"] = ("acsc_loss_per_case_calc", u)
    out = []
    for label, (col, df) in series.items():
        r = rolling_robust_z(df[col])
        r["week_start"] = df["week_start"].to_numpy()
        r["series"] = label
        out.append(r[r["z"].abs() > z_cut])
    res = pd.concat(out, ignore_index=True) if out else pd.DataFrame()
    return res.sort_values("z", key=lambda s: s.abs(), ascending=False).reset_index(drop=True) if len(res) else res


def category_spikes(monthly: pd.DataFrame, z_cut: float = 3.5, year_from: int = 2020) -> pd.DataFrame:
    """Months where a category's false-item count is far above its own neighbours (rolling 7 months)."""
    f = monthly[monthly["verdict_en"].isin(["Fake", "Distorted"]) & (monthly["month_start"].dt.year >= year_from)]
    g = f.groupby(["month_start", "category_th"])["n"].sum().unstack(fill_value=0).sort_index()
    rows = []
    for cat in g.columns:
        if g[cat].sum() < 60:
            continue
        r = rolling_robust_z(g[cat], window=7, min_periods=4)
        r = r[(r["z"] > z_cut) & (r["value"] >= 15)]  # ignore tiny counts
        for ts, rr in r.iterrows():
            rows.append({"month": ts, "category": cat, "count": int(rr["value"]), "expected": rr["expected"], "z": rr["z"]})
    return pd.DataFrame(rows).sort_values("z", ascending=False).reset_index(drop=True) if rows else pd.DataFrame()


def cases_down_severity_up(weekly: pd.DataFrame, span: int = 4) -> pd.DataFrame:
    """Non-overlapping blocks of `span` usable weeks where mean cases fell but loss per case rose vs the previous block."""
    u = mx.usable_weeks(weekly).reset_index(drop=True)
    rows = []
    blocks = [u.iloc[i:i + span] for i in range(0, len(u) - span + 1, span)]
    for prev, cur in zip(blocks[:-1], blocks[1:]):
        c0, c1 = prev["acsc_cases"].mean(), cur["acsc_cases"].mean()
        s0 = prev["acsc_loss_baht"].sum() / prev["acsc_cases"].sum()
        s1 = cur["acsc_loss_baht"].sum() / cur["acsc_cases"].sum()
        rows.append({"from": prev["week_start"].iloc[0], "to": cur["week_start"].iloc[-1], "cases_prev": c0, "cases": c1,
                     "lpc_prev": s0, "lpc": s1, "cases_chg_pct": (c1 - c0) / c0 * 100, "lpc_chg_pct": (s1 - s0) / s0 * 100,
                     "cases_down_lpc_up": (c1 < c0) and (s1 > s0)})
    return pd.DataFrame(rows)


def cases_loss_relation(weekly: pd.DataFrame) -> dict:
    """Pearson r (level) and elasticity of weekly loss with respect to cases (log-log slope), usable weeks."""
    u = mx.usable_weeks(weekly)
    x, y = np.log(u["acsc_cases"].to_numpy(float)), np.log(u["acsc_loss_baht"].to_numpy(float))
    slope = float(np.polyfit(x, y, 1)[0])
    return {"n": len(u), "r": float(u["acsc_cases"].corr(u["acsc_loss_baht"])), "elasticity": slope,
            "r_lpc_cases": float(u["acsc_cases"].corr(u["acsc_loss_baht"] / u["acsc_cases"]))}


# ---------------------------------------------------------------------------
# Q1: topics that recur and are rising / declining
# ---------------------------------------------------------------------------


def rising_topics(counts: pd.DataFrame, totals: pd.Series, label_col: str, y0: int, y1: int, min_count: int = 20) -> pd.DataFrame:
    """Share of items per year for each topic and the change (percentage points) between two years.

    counts: columns [year, <label_col>, n];  totals: items per year (index = year).
    """
    c = counts[counts["year"].isin([y0, y1])].pivot_table(index=label_col, columns="year", values="n", aggfunc="sum", fill_value=0)
    for y in (y0, y1):
        if y not in c.columns:
            c[y] = 0
    c = c[(c[y0] + c[y1]) >= min_count]
    out = pd.DataFrame({
        "topic": c.index, "n_start": c[y0].to_numpy(), "n_end": c[y1].to_numpy(),
        "share_start": c[y0].to_numpy() / totals[y0] * 100, "share_end": c[y1].to_numpy() / totals[y1] * 100})
    out["change_pp"] = out["share_end"] - out["share_start"]
    return out.sort_values("change_pp", ascending=False).reset_index(drop=True)


def eu_topic_counts(eu_keywords: pd.DataFrame) -> pd.DataFrame:
    return eu_keywords.rename(columns={"keyword": "topic", "debunks": "n"})[["year", "topic", "n"]]


# ---------------------------------------------------------------------------
# Q3: overlap of global AI harms with Thai fact-checked items; peers; country link
# ---------------------------------------------------------------------------


def theme_overlap(theme_year: pd.DataFrame) -> pd.DataFrame:
    """Per theme: share of all AIID incidents and share of all false AFNC verdicts, plus a status label."""
    g = theme_year.groupby(["source", "theme_th"]).agg(n=("n", "sum")).reset_index()
    tot = theme_year.drop_duplicates(["source", "year"]).groupby("source")["total"].sum()
    g["share_pct"] = g.apply(lambda r: r["n"] / tot[r["source"]] * 100, axis=1)
    p = g.pivot(index="theme_th", columns="source", values=["n", "share_pct"])
    p.columns = [f"{a}_{b}" for a, b in p.columns]
    p = p.reset_index().rename(columns={"theme_th": "theme"})
    return p


def overlap_status(aiid_share: float, afnc_share: float, afnc_n: int, min_share: float = 2.0, min_n: int = 30) -> str:
    """'ซ้อนทับ' when both sides show it, 'เฝ้าระวัง' when AIID shows it but AFNC data hardly does."""
    if aiid_share >= min_share and afnc_n >= min_n and afnc_share >= min_share:
        return "ซ้อนทับ"
    if aiid_share >= min_share and afnc_n < min_n:
        return "เฝ้าระวัง"
    if aiid_share < min_share and afnc_share >= min_share:
        return "เด่นในไทย"
    return "น้อยทั้งสองฝั่ง"


def nearest_peers(fotn: pd.DataFrame, year: int, iso3: str = "THA", band: int = 6) -> pd.DataFrame:
    y = fotn[fotn["data_year"] == year]
    me = y.loc[y["iso3"] == iso3, "total_score"].iloc[0]
    peers = y[(y["total_score"] - me).abs() <= band].sort_values("total_score", ascending=False).copy()
    prior = fotn[fotn["data_year"] == year - 5].set_index("iso3")["total_score"]
    peers["change_5y"] = peers["iso3"].map(lambda i: peers.loc[peers["iso3"] == i, "total_score"].iloc[0] - prior.get(i, np.nan))
    return peers[["country", "iso3", "total_score", "status", "pct_access", "pct_content", "pct_rights", "change_5y"]]


def spearman(x: pd.Series, y: pd.Series) -> float:
    return float(x.rank().corr(y.rank()))


def country_link(country: pd.DataFrame, min_mentions: int = 5) -> dict:
    """Exploratory rank correlation between FOTN score and how often a country is mentioned in AIID text."""
    d = country[country["mentions"] >= min_mentions]
    low = country[(country["status_code"] == 3) & (country["mentions"] > 0)].sort_values("mentions", ascending=False)
    return {"n": len(d), "rho": spearman(d["total_score"], d["mentions"]) if len(d) > 3 else float("nan"),
            "not_free": low[["country", "mentions", "total_score"]].reset_index(drop=True),
            "n_with_mention": int((country["mentions"] > 0).sum()), "n_countries": len(country)}
