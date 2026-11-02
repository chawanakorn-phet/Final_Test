"""Read the raw files. No cleaning beyond parsing happens here."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import config

AFNC_COLS = [
    "post_id", "date", "week_start", "year", "month", "item_type", "verdict_en", "category_en",
    "checked_by_agency", "topic_tags", "view_count", "title",
]
AIID_COLS = [
    "Incident ID", "date", "title", "description", "Implicated Systems", "Risk Domain", "Intent",
    "report_count",
]


def read_panel(raw: Path) -> pd.DataFrame:
    return pd.read_csv(raw / config.PANEL_FILE, encoding="utf-8-sig", parse_dates=["week_start", "week_end"])


def read_acsc(raw: Path) -> pd.DataFrame:
    return pd.read_csv(raw / config.ACSC_FILE, encoding="utf-8-sig", parse_dates=["week_start", "week_end"])


def read_afnc(raw: Path) -> pd.DataFrame:
    """AFNC items without the 68 MB `content` column."""
    df = pd.read_csv(raw / config.AFNC_FILE, encoding="utf-8-sig", usecols=AFNC_COLS, low_memory=False)
    df["date"] = pd.to_datetime(df["date"])
    df["week_start"] = pd.to_datetime(df["week_start"])
    return df


def read_aiid_incidents(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Incidents", header=2, usecols=columns or AIID_COLS)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def aiid_snapshot_paths(raw: Path) -> list[tuple[pd.Timestamp, Path]]:
    """All AIID exports (weekly versions + latest), oldest first."""
    base = raw / config.AIID_DIR
    paths = sorted((base / config.AIID_WEEKLY_DIR).glob("AIID_Excel_Export-*.xlsx"))
    paths.append(base / config.AIID_LATEST)
    out = []
    for p in paths:
        stamp = p.stem.rsplit("-", 1)[-1]
        out.append((pd.to_datetime(stamp, format="%Y%m%d"), p))
    return sorted(out)


def read_fotn(raw: Path) -> pd.DataFrame:
    return pd.read_csv(raw / config.FOTN_FILE, encoding="utf-8-sig")


def read_eu(raw: Path) -> pd.DataFrame:
    return pd.read_csv(raw / config.EU_FILE, encoding="utf-8-sig")
