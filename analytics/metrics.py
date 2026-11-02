"""KPI and summary calculations. Pure functions over the processed tables."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def pct_change(new: float, old: float) -> float | None:
    if old is None or pd.isna(old) or old == 0 or pd.isna(new):
        return None
    return (new - old) / old * 100


def usable_weeks(weekly: pd.DataFrame) -> pd.DataFrame:
    """Weeks with an ACSC briefing that is not flagged suspect."""
    return weekly[weekly["acsc_usable"]].sort_values("week_start")


@dataclass
class LatestWeek:
    week_start: pd.Timestamp
    week_end: pd.Timestamp
    cases: float
    loss_baht: float
    loss_per_case: float
    rounded: bool
    cases_vs_base: float | None
    loss_vs_base: float | None
    lpc_vs_base: float | None
    base_weeks: int


def latest_week(weekly: pd.DataFrame, base_weeks: int = 4) -> LatestWeek | None:
    """Latest usable briefing, compared with the mean of the `base_weeks` usable weeks before it."""
    u = usable_weeks(weekly)
    if u.empty:
        return None
    last, prior = u.iloc[-1], u.iloc[-1 - base_weeks:-1]
    lpc = last["acsc_loss_baht"] / last["acsc_cases"]
    prior_lpc = prior["acsc_loss_baht"].sum() / prior["acsc_cases"].sum() if len(prior) else np.nan
    return LatestWeek(
        week_start=last["week_start"], week_end=last["week_end"], cases=last["acsc_cases"],
        loss_baht=last["acsc_loss_baht"], loss_per_case=lpc, rounded=bool(last["acsc_rounded"]),
        cases_vs_base=pct_change(last["acsc_cases"], prior["acsc_cases"].mean()) if len(prior) else None,
        loss_vs_base=pct_change(last["acsc_loss_baht"], prior["acsc_loss_baht"].mean()) if len(prior) else None,
        lpc_vs_base=pct_change(lpc, prior_lpc), base_weeks=len(prior))


def false_share(df: pd.DataFrame) -> float:
    """(fake + distorted) / all verdicts, from summed counts (not a mean of weekly percentages)."""
    total = df["afnc_verdicts"].sum()
    return float(df["afnc_false"].sum() / total * 100) if total else float("nan")


def recent_false_share(weekly: pd.DataFrame, n_weeks: int = 4) -> tuple[float, float]:
    """False share over the last n complete weeks vs the same span one year earlier."""
    w = weekly.sort_values("week_start")
    last = w["week_start"].max()
    recent = w[w["week_start"] > last - pd.Timedelta(weeks=n_weeks)]
    prev_end = last - pd.Timedelta(weeks=52)
    prev = w[(w["week_start"] > prev_end - pd.Timedelta(weeks=n_weeks)) & (w["week_start"] <= prev_end)]
    return false_share(recent), false_share(prev) if len(prev) else float("nan")


def afnc_yearly(weekly: pd.DataFrame, min_year: int = 2020) -> pd.DataFrame:
    g = weekly[weekly["year"] >= min_year].groupby("year")[["afnc_verdicts", "afnc_fake", "afnc_distorted", "afnc_true", "afnc_false"]].sum()
    g["false_share_pct"] = g["afnc_false"] / g["afnc_verdicts"] * 100
    return g.reset_index()


def monthly_scam(weekly: pd.DataFrame) -> pd.DataFrame:
    """Average per usable week, by month of week_start."""
    u = usable_weeks(weekly).copy()
    u["month"] = u["week_start"].dt.to_period("M").dt.to_timestamp()
    g = u.groupby("month").agg(cases=("acsc_cases", "mean"), loss=("acsc_loss_baht", "mean"),
                               cases_sum=("acsc_cases", "sum"), loss_sum=("acsc_loss_baht", "sum"),
                               weeks=("acsc_cases", "size")).reset_index()
    g["loss_per_case"] = g["loss_sum"] / g["cases_sum"]
    return g


def cases_loss_stats(weekly: pd.DataFrame) -> dict:
    u = usable_weeks(weekly)
    return {
        "weeks": len(u), "cases_mean": u["acsc_cases"].mean(), "loss_mean": u["acsc_loss_baht"].mean(),
        "lpc_overall": u["acsc_loss_baht"].sum() / u["acsc_cases"].sum(),
    }


def correlation_note(weekly: pd.DataFrame) -> dict:
    """Pearson r between ACSC measures and the weekly AFNC false share (usable weeks only)."""
    u = usable_weeks(weekly).dropna(subset=["afnc_false_share_pct"])
    out = {"n": len(u)}
    for col, key in (("acsc_cases", "cases"), ("acsc_loss_baht", "loss")):
        out[key] = float(u[col].corr(u["afnc_false_share_pct"])) if len(u) > 2 else float("nan")
    out["cases_vs_loss"] = float(u["acsc_cases"].corr(u["acsc_loss_baht"])) if len(u) > 2 else float("nan")
    return out


def category_share(monthly: pd.DataFrame, year_from: int = 2020) -> pd.DataFrame:
    """Yearly share (%) of false items (fake + distorted) by category."""
    f = monthly[monthly["verdict_en"].isin(["Fake", "Distorted"]) & (monthly["month_start"].dt.year >= year_from)].copy()
    f["year"] = f["month_start"].dt.year
    g = f.groupby(["year", "category_th"])["n"].sum().reset_index()
    g["share_pct"] = g["n"] / g.groupby("year")["n"].transform("sum") * 100
    return g


def top_agencies(agencies: pd.DataFrame, year_from: int, year_to: int, n: int = 10) -> pd.DataFrame:
    a = agencies[(agencies["year"] >= year_from) & (agencies["year"] <= year_to)]
    return a.groupby("checked_by_agency")["n"].sum().nlargest(n).reset_index()


def top_tags(tags: pd.DataFrame, year_from: int, year_to: int, n: int = 15) -> pd.DataFrame:
    t = tags[(tags["year"] >= year_from) & (tags["year"] <= year_to)]
    return t.groupby("tag")[["n", "n_false"]].sum().nlargest(n, "n").reset_index()


# ----- Freedom on the Net ---------------------------------------------------


def thailand_fotn(fotn: pd.DataFrame) -> pd.DataFrame:
    return fotn[fotn["iso3"] == "THA"].sort_values("data_year")


def fotn_rank(fotn: pd.DataFrame, iso3: str, year: int) -> tuple[int, int]:
    """Rank (1 = most free; ties share the best rank) and number of countries in that year."""
    y = fotn[fotn["data_year"] == year]
    score = y.loc[y["iso3"] == iso3, "total_score"].iloc[0]
    return int((y["total_score"] > score).sum() + 1), len(y)


def fotn_change(fotn: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    p = fotn.pivot(index="country", columns="data_year", values="total_score")
    c = (p[y1] - p[y0]).dropna().rename("change").reset_index()
    return c.merge(p[[y0, y1]].reset_index(), on="country").rename(columns={y0: "score_start", y1: "score_end"}).sort_values("change")


# ----- AIID -----------------------------------------------------------------


def aiid_summary(yearly: pd.DataFrame, risk: pd.DataFrame, latest_year: int) -> dict:
    total = int(yearly["incidents"].sum())
    classified = int(risk.loc[risk["risk_domain"] != "ยังไม่จัดหมวด", "n"].sum())
    full = yearly[yearly["year"] < latest_year]
    peak = full.loc[full["incidents"].idxmax()]
    return {
        "total": total, "deepfake": int(yearly["deepfake"].sum()), "scam": int(yearly["scam"].sum()),
        "classified_pct": classified / total * 100, "peak_year": int(peak["year"]), "peak_n": int(peak["incidents"]),
    }
