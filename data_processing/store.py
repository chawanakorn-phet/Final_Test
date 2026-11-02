"""Read the processed tables back (this is all the dashboard ever reads)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import config

DATE_COLS = {
    "weekly": ["week_start", "week_end"],
    "afnc_monthly": ["month_start"],
    "aiid_thai": ["date"],
    "aiid_top": ["date"],
    "aiid_growth": ["snapshot"],
    "eu_monthly": ["month_start"],
    "eu_debunks": ["debunk_date"],
    "afnc_clean": ["date", "week_start"],
    "aiid_clean": ["date"],
}
TABLES = [
    "weekly", "acsc_types", "afnc_monthly", "afnc_agencies", "afnc_tags", "aiid_yearly", "aiid_risk",
    "aiid_thai", "aiid_top", "aiid_growth", "fotn", "eu_yearly", "eu_monthly", "eu_keywords",
    "eu_languages", "eu_domains", "validation", "cleaning_log", "afnc_scam_share", "theme_year", "covid_share", "aiid_country", "eu_debunks",
    "afnc_clean", "aiid_clean",
]


def is_built(directory: Path = config.PROCESSED_DIR) -> bool:
    return all((directory / f"{t}.csv").exists() for t in TABLES) and (directory / "meta.json").exists()


def signature(directory: Path = config.PROCESSED_DIR) -> str:
    """Changes whenever any processed file changes (used as a cache key)."""
    parts = [f"{p.name}:{p.stat().st_mtime_ns}" for p in sorted(directory.glob("*.csv")) + [directory / "meta.json"] if p.exists()]
    return "|".join(parts)


def load_tables(directory: Path = config.PROCESSED_DIR) -> dict[str, pd.DataFrame]:
    out = {}
    for t in TABLES:
        out[t] = pd.read_csv(directory / f"{t}.csv", encoding="utf-8-sig", parse_dates=DATE_COLS.get(t, []))
    return out


def load_meta(directory: Path = config.PROCESSED_DIR) -> dict:
    return json.loads((directory / "meta.json").read_text(encoding="utf-8"))
