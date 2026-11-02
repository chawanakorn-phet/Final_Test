"""Pure helpers behind the dashboard filters, so the filtered numbers can be unit-tested."""
from __future__ import annotations

import pandas as pd

VERDICT_EN = {"ข่าวปลอม": "Fake", "ข่าวบิดเบือน": "Distorted", "ข่าวจริง": "True"}


def slice_years(df: pd.DataFrame, col: str, lo: int, hi: int) -> pd.DataFrame:
    s = df[col].dt.year if pd.api.types.is_datetime64_any_dtype(df[col]) else df[col]
    return df[(s >= lo) & (s <= hi)]


def slice_weeks(weekly: pd.DataFrame, lo, hi) -> pd.DataFrame:
    """Weeks whose start date lies in [lo, hi] (both inclusive)."""
    return weekly[(weekly["week_start"] >= pd.Timestamp(lo)) & (weekly["week_start"] <= pd.Timestamp(hi))]


def afnc_filtered(monthly: pd.DataFrame, lo: int, hi: int, categories: list[str]) -> pd.DataFrame:
    """AFNC verdict counts (month x category x verdict) limited to the chosen years and categories."""
    m = slice_years(monthly, "month_start", lo, hi)
    return m[m["category_th"].isin(categories)]


def verdict_year_table(filtered: pd.DataFrame) -> pd.DataFrame:
    """Per year: fake / distorted / true / total, in the column names the verdict chart expects."""
    p = filtered.assign(year=filtered["month_start"].dt.year).pivot_table(index="year", columns="verdict_en", values="n", aggfunc="sum", fill_value=0)
    for v in ("Fake", "Distorted", "True"):
        if v not in p.columns:
            p[v] = 0
    out = pd.DataFrame({"year": p.index, "afnc_fake": p["Fake"].to_numpy(), "afnc_distorted": p["Distorted"].to_numpy(), "afnc_true": p["True"].to_numpy()})
    out["afnc_verdicts"] = out[["afnc_fake", "afnc_distorted", "afnc_true"]].sum(axis=1)
    out["afnc_false"] = out["afnc_fake"] + out["afnc_distorted"]
    return out.reset_index(drop=True)


def category_share_selected(filtered: pd.DataFrame, verdicts_en: list[str]) -> pd.DataFrame:
    """Yearly share (%) of the counted verdict types by category, re-normalised over the selected categories."""
    f = filtered[filtered["verdict_en"].isin(verdicts_en)].assign(year=lambda d: d["month_start"].dt.year)
    g = f.groupby(["year", "category_th"])["n"].sum().reset_index()
    if g.empty:
        return g.assign(share_pct=pd.Series(dtype=float))
    g["share_pct"] = g["n"] / g.groupby("year")["n"].transform("sum") * 100
    return g


def overall_false_share(filtered: pd.DataFrame) -> float:
    tot = filtered["n"].sum()
    return float(filtered.loc[filtered["verdict_en"].isin(["Fake", "Distorted"]), "n"].sum() / tot * 100) if tot else float("nan")


def country_options(fotn: pd.DataFrame) -> dict[str, str]:
    """Display name -> iso3 for the multiselect (parenthetical suffixes dropped)."""
    y = fotn.sort_values("data_year").drop_duplicates("iso3", keep="last")
    return {c.split(" (")[0]: i for c, i in zip(y["country"], y["iso3"])}
