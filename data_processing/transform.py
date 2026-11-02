"""Pure transformations: raw DataFrames in, tidy dashboard tables out (no I/O)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config


# ---------------------------------------------------------------------------
# ACSC / weekly panel
# ---------------------------------------------------------------------------


def group_scam_type(label) -> str | None:
    """Map one of the many spellings of a scam type to a canonical group. NaN stays NaN."""
    if pd.isna(label):
        return None
    for needle, group in config.ACSC_TYPE_RULES:
        if needle in str(label):
            return group
    return config.ACSC_TYPE_OTHER


def build_weekly(panel: pd.DataFrame) -> pd.DataFrame:
    """Weekly panel + quality flags. Weeks without an ACSC briefing keep NaN (never 0)."""
    w = panel.copy()
    w["acsc_reported"] = w["acsc_reported"].astype(bool)
    flag = w["acsc_flag"].fillna("").astype(str)
    w["acsc_suspect"] = flag.str.startswith(config.SUSPECT_FLAG_PREFIX)
    w["acsc_usable"] = w["acsc_reported"] & ~w["acsc_suspect"]
    w["acsc_rounded"] = w["acsc_loss_precision"].eq("rounded")
    # Recompute rather than trusting the published change-vs-previous-week columns.
    w["acsc_loss_per_case_calc"] = np.where(w["acsc_reported"], w["acsc_loss_baht"] / w["acsc_cases"], np.nan)
    w["top_type_group"] = w["acsc_top_type_th"].map(group_scam_type)
    w["highest_loss_group"] = w["acsc_highest_loss_type_th"].map(group_scam_type)
    # False share recomputed from counts (the published % is a per-week value)
    w["afnc_false"] = w["afnc_fake"] + w["afnc_distorted"]
    # Plot-ready copies: unusable weeks are NaN, so lines break instead of dropping to 0 / spiking
    for col in ("acsc_cases", "acsc_loss_baht", "acsc_loss_per_case_calc"):
        w[col + "_plot"] = w[col].where(w["acsc_usable"])
    return w


def acsc_type_summary(weekly: pd.DataFrame) -> pd.DataFrame:
    """How often each scam group was the top-by-cases / top-by-loss type (counts of weeks)."""
    use = weekly[weekly["acsc_usable"]]
    top = use["top_type_group"].value_counts(dropna=True).rename("weeks_top_by_cases")
    loss = use["highest_loss_group"].value_counts(dropna=True).rename("weeks_top_by_loss")
    out = pd.concat([top, loss], axis=1).fillna(0).astype(int)
    out.index.name = "scam_type"
    return out.reset_index()


# ---------------------------------------------------------------------------
# AFNC
# ---------------------------------------------------------------------------


def _category_th(en) -> str:
    return config.CATEGORY_TH.get(en, config.CATEGORY_OTHER_TH)


def afnc_verdicts(items: pd.DataFrame) -> pd.DataFrame:
    v = items[items["item_type"] == "Verdict"].copy()
    v["category_th"] = v["category_en"].map(_category_th)
    v["verdict_th"] = v["verdict_en"].map(config.VERDICT_TH)
    return v


def afnc_monthly(items: pd.DataFrame) -> pd.DataFrame:
    v = afnc_verdicts(items)
    v["month_start"] = v["date"].dt.to_period("M").dt.to_timestamp()
    out = (v.groupby(["month_start", "category_th", "verdict_en"]).size().rename("n").reset_index())
    return out


def afnc_agencies(items: pd.DataFrame) -> pd.DataFrame:
    v = afnc_verdicts(items)
    v = v.dropna(subset=["checked_by_agency"])
    out = v.groupby(["year", "checked_by_agency"]).size().rename("n").reset_index()
    return out


def normalize_tags(raw_tags) -> list[str]:
    """Split `a;b;c`, drop generic tags, map aliases to one canonical tag, de-duplicate per post."""
    if pd.isna(raw_tags):
        return []
    seen, out = set(), []
    for t in str(raw_tags).split(";"):
        t = t.strip()
        if not t or t in config.TAG_GENERIC:
            continue
        t = config.TAG_LOOKUP.get(t, t)
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def afnc_tags(items: pd.DataFrame, min_total: int = 15) -> pd.DataFrame:
    v = afnc_verdicts(items)
    exploded = v[["year", "topic_tags", "verdict_en"]].assign(tag=v["topic_tags"].map(normalize_tags)).explode("tag")
    exploded = exploded.dropna(subset=["tag"])
    exploded["is_false"] = exploded["verdict_en"].isin(["Fake", "Distorted"])
    out = exploded.groupby(["year", "tag"]).agg(n=("tag", "size"), n_false=("is_false", "sum")).reset_index()
    keep = out.groupby("tag")["n"].transform("sum") >= min_total
    return out[keep].reset_index(drop=True)


def clean_afnc_items(items: pd.DataFrame) -> pd.DataFrame:
    """Row-level cleaned AFNC posts (no article text): Thai labels, merged categories, normalised tags."""
    c = items.copy()
    c["category_th"] = c["category_en"].map(_category_th)
    c["verdict_th"] = c["verdict_en"].map(config.VERDICT_TH)
    c["is_false"] = c["verdict_en"].isin(["Fake", "Distorted"])
    c["tags_clean"] = c["topic_tags"].map(lambda s: ";".join(normalize_tags(s)))
    c["agency_missing"] = c["checked_by_agency"].isna()
    return c.drop(columns=["topic_tags", "title"])


def afnc_scam_share(clean: pd.DataFrame) -> pd.DataFrame:
    """Per year: false verdicts, how many carry a tag, how many carry a scam/impersonation tag."""
    f = clean[(clean["item_type"] == "Verdict") & clean["is_false"]].copy()
    tags = f["tags_clean"].fillna("").str.split(";")
    f["has_tag"] = tags.map(lambda t: any(x for x in t))
    f["scam_tag"] = tags.map(lambda t: bool(set(t) & config.SCAM_TAGS))
    g = f.groupby("year").agg(false_posts=("post_id", "size"), tagged=("has_tag", "sum"), scam_tagged=("scam_tag", "sum")).reset_index()
    g["scam_share_of_tagged_pct"] = g["scam_tagged"] / g["tagged"] * 100
    return g


# ---------------------------------------------------------------------------
# AIID
# ---------------------------------------------------------------------------


def aiid_flags(inc: pd.DataFrame) -> pd.DataFrame:
    d = inc.copy()
    text = (d["title"].fillna("") + " " + d["description"].fillna("") + " " + d["Implicated Systems"].fillna(""))
    d["year"] = d["date"].dt.year
    d["is_deepfake"] = text.str.contains(config.DEEPFAKE_PATTERN, case=False, regex=True)
    d["is_scam"] = (d["title"].fillna("") + " " + d["description"].fillna("")).str.contains(
        config.SCAM_PATTERN, case=False, regex=True)
    d["is_thai"] = (d["title"].fillna("") + " " + d["description"].fillna("")).str.contains(
        config.THAI_PATTERN, case=True, regex=True)
    d["is_misinfo"] = d["Risk Domain"].eq("Misinformation")
    d["classified"] = d["Risk Domain"].notna()
    return d


def aiid_yearly(flagged: pd.DataFrame) -> pd.DataFrame:
    g = flagged.groupby("year")
    out = g.agg(incidents=("Incident ID", "size"), deepfake=("is_deepfake", "sum"), scam=("is_scam", "sum"),
                misinfo=("is_misinfo", "sum"), reports=("report_count", "sum")).reset_index()
    out["year"] = out["year"].astype(int)
    return out


def aiid_risk(flagged: pd.DataFrame) -> pd.DataFrame:
    d = flagged.assign(
        risk_domain=flagged["Risk Domain"].fillna("ยังไม่จัดหมวด"),
        intent=flagged["Intent"].fillna("ยังไม่จัดหมวด"),
    )
    return d.groupby(["risk_domain", "intent"]).size().rename("n").reset_index()


def aiid_thai(flagged: pd.DataFrame) -> pd.DataFrame:
    t = flagged[flagged["is_thai"]].sort_values("date")
    out = t[["Incident ID", "date", "title", "is_deepfake", "is_scam", "report_count"]].copy()
    out["url"] = out["Incident ID"].map(lambda i: config.AIID_CITE_URL.format(id=i))
    return out.reset_index(drop=True)


def aiid_top_reported(flagged: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    t = flagged.nlargest(n, "report_count")[["Incident ID", "date", "title", "report_count"]].copy()
    t["url"] = t["Incident ID"].map(lambda i: config.AIID_CITE_URL.format(id=i))
    return t.reset_index(drop=True)


def aiid_growth(snapshots: list[tuple[pd.Timestamp, pd.DataFrame]]) -> pd.DataFrame:
    """One row per weekly export: size, new IDs vs previous export, IDs that disappeared."""
    rows, prev = [], None
    for stamp, df in snapshots:
        ids = set(df["Incident ID"])
        new = ids - prev if prev is not None else set()
        new_df = df[df["Incident ID"].isin(new)]
        rows.append({
            "snapshot": stamp, "incidents": len(ids), "new": len(new) if prev is not None else np.nan,
            "removed": len(prev - ids) if prev is not None else np.nan,
            "new_with_old_event_date": int((new_df["date"] < stamp - pd.Timedelta(days=60)).sum()) if prev is not None else np.nan,
        })
        prev = ids
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Freedom on the Net
# ---------------------------------------------------------------------------


def build_fotn(df: pd.DataFrame) -> pd.DataFrame:
    f = df.copy()
    f["pct_access"] = f["obstacles_to_access"] / 25 * 100
    f["pct_content"] = f["limits_on_content"] / 35 * 100
    f["pct_rights"] = f["violations_of_user_rights"] / 40 * 100
    f["is_asean"] = f["iso3"].isin(config.ASEAN)
    return f


# ---------------------------------------------------------------------------
# EUvsDisinfo
# ---------------------------------------------------------------------------


def eu_prepare(eu: pd.DataFrame) -> pd.DataFrame:
    d = eu.copy()
    d["debunk_dt"] = pd.to_datetime(d["debunk_date"], format="%d-%m-%Y", errors="coerce")
    return d


def eu_debunks(d: pd.DataFrame) -> pd.DataFrame:
    """One row per distinct debunk (the article-level file repeats debunk-level fields)."""
    g = d.groupby("debunk_id")
    out = g.agg(debunk_date=("debunk_dt", "first"), keywords=("keywords", "first"), articles=("article_id", "size"),
                disinformation_articles=("class", lambda s: int((s == "disinformation").sum())),
                trustworthy_articles=("class", lambda s: int((s == "trustworthy").sum()))).reset_index()
    return out.sort_values("debunk_date").reset_index(drop=True)


def eu_yearly(d: pd.DataFrame) -> pd.DataFrame:
    d = d.dropna(subset=["debunk_dt"])
    g = d.groupby(d["debunk_dt"].dt.year)
    out = pd.DataFrame({
        "debunks": g["debunk_id"].nunique(),
        "articles": g.size(),
        "disinformation_articles": g["class"].apply(lambda s: int((s == "disinformation").sum())),
        "trustworthy_articles": g["class"].apply(lambda s: int((s == "trustworthy").sum())),
    }).reset_index(names="year")
    out["trustworthy_share_pct"] = out["trustworthy_articles"] / out["articles"] * 100
    out["partial_year"] = out["year"].eq(d["debunk_dt"].dt.year.max())
    return out


def eu_monthly(d: pd.DataFrame) -> pd.DataFrame:
    d = d.dropna(subset=["debunk_dt"])
    u = d.drop_duplicates("debunk_id")
    m = u.groupby(u["debunk_dt"].dt.to_period("M").dt.to_timestamp()).size()
    return m.rename_axis("month_start").rename("debunks").reset_index()


def eu_keywords(d: pd.DataFrame, top: int = 25) -> pd.DataFrame:
    """Keyword x year, counted once per distinct debunk (not per article row)."""
    u = d.dropna(subset=["debunk_dt", "keywords"]).drop_duplicates("debunk_id")[["debunk_id", "debunk_dt", "keywords"]]
    u = u.assign(keyword=u["keywords"].str.split(",")).explode("keyword")
    u["keyword"] = u["keyword"].str.strip()
    u = u[u["keyword"] != ""].drop_duplicates(["debunk_id", "keyword"])
    u["year"] = u["debunk_dt"].dt.year
    keep = u["keyword"].value_counts().head(top).index
    return u[u["keyword"].isin(keep)].groupby(["year", "keyword"]).size().rename("debunks").reset_index()


def eu_languages(d: pd.DataFrame, top: int = 8) -> pd.DataFrame:
    return d["article_language"].value_counts().head(top).rename_axis("language").rename("articles").reset_index()


def eu_domains(d: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    parts = []
    for cls in ("disinformation", "trustworthy"):
        s = d.loc[d["class"] == cls, "article_domain"].value_counts().head(top)
        parts.append(s.rename_axis("domain").rename("articles").reset_index().assign(**{"class": cls}))
    return pd.concat(parts, ignore_index=True)


# ---------------------------------------------------------------------------
# Themes: AIID (English) vs AFNC (Thai), COVID bridge, country mentions
# ---------------------------------------------------------------------------


def aiid_theme_flags(flagged: pd.DataFrame) -> pd.DataFrame:
    text = flagged["title"].fillna("") + " " + flagged["description"].fillna("")
    return pd.DataFrame({k: text.str.contains(rx, case=False, regex=True) for k, _, rx, _ in config.THEMES}, index=flagged.index)


def afnc_theme_flags(items: pd.DataFrame) -> pd.DataFrame:
    text = items["title"].fillna("") + " " + items["topic_tags"].fillna("")
    return pd.DataFrame({k: text.str.contains(rx, case=True, regex=True) for k, _, _, rx in config.THEMES}, index=items.index)


def theme_year(flagged: pd.DataFrame, aiid_flags: pd.DataFrame, items: pd.DataFrame, afnc_flags: pd.DataFrame) -> pd.DataFrame:
    """Long table: source, year, theme, n matching, total items that year (AFNC = false verdicts only)."""
    rows = []
    a = aiid_flags.assign(year=flagged["year"].to_numpy())
    tot_a = a.groupby("year").size()
    for k, label, _, _ in config.THEMES:
        for y, n in a.groupby("year")[k].sum().items():
            rows.append(("AIID", int(y), k, label, int(n), int(tot_a[y])))
    mask = (items["item_type"] == "Verdict") & items["verdict_en"].isin(["Fake", "Distorted"])
    f = afnc_flags[mask].assign(year=items.loc[mask, "year"].to_numpy())
    tot_f = f.groupby("year").size()
    for k, label, _, _ in config.THEMES:
        for y, n in f.groupby("year")[k].sum().items():
            rows.append(("AFNC", int(y), k, label, int(n), int(tot_f[y])))
    return pd.DataFrame(rows, columns=["source", "year", "theme", "theme_th", "n", "total"])


def covid_share(eu_deb: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    """Yearly share of EUvsDisinfo debunks / AFNC verdicts that are about COVID."""
    d = eu_deb.dropna(subset=["debunk_date"]).copy()
    d["year"] = pd.to_datetime(d["debunk_date"]).dt.year
    d["covid"] = d["keywords"].fillna("").map(lambda s: bool({k.strip() for k in s.split(",")} & config.COVID_KEYWORDS_EU))
    eu = d.groupby("year").agg(n=("covid", "sum"), total=("covid", "size")).reset_index().assign(source="EUvsDisinfo")
    v = items[items["item_type"] == "Verdict"].copy()
    v["covid"] = v["topic_tags"].fillna("").map(lambda s: bool({t.strip() for t in s.split(";")} & config.COVID_TAGS_TH))
    th = v.groupby("year").agg(n=("covid", "sum"), total=("covid", "size")).reset_index().assign(source="AFNC (ไทย)")
    out = pd.concat([eu, th], ignore_index=True)
    out["share_pct"] = out["n"] / out["total"] * 100
    return out


def aiid_country_mentions(flagged: pd.DataFrame, fotn: pd.DataFrame, year: int) -> pd.DataFrame:
    """Incidents whose title/description mention each FOTN country (a *mention*, not where it happened)."""
    import re
    text = flagged["title"].fillna("") + " " + flagged["description"].fillna("")
    y = fotn[fotn["data_year"] == year]
    rows = []
    for _, r in y.iterrows():
        base = re.sub(r" \(.*\)", "", r["country"])
        if base in config.COUNTRY_TEXT_SKIP:
            continue
        keys = config.COUNTRY_TEXT_ALIASES.get(r["country"], [base])
        pat = r"\b(?:" + "|".join(re.escape(k) for k in keys) + r")\b"
        rows.append({"country": r["country"], "iso3": r["iso3"], "mentions": int(text.str.contains(pat, regex=True).sum()),
                     "total_score": r["total_score"], "status_code": r["status_code"]})
    return pd.DataFrame(rows)
