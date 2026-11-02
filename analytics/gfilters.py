"""Global (sidebar) filters shared by every page. Pure functions: a Selection in, filtered DataFrames out.

Rules that keep unrelated data from being mixed up:
  * time filters (date range, year, quarter, month) apply to every dataset that has a date; Freedom on the Net is annual,
    so only the date range / year part applies to it;
  * Thai / foreign decides which datasets are in scope (AFNC and ACSC are Thai only; EUvsDisinfo is foreign only);
  * news type and verdict status apply to AFNC only; damage category applies to ACSC only; country / group applies to
    Freedom on the Net only;
  * an empty multi-select means "all".
A dataset that a filter cannot apply to is left untouched by that filter and `notes()` says so.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import pandas as pd

SOURCES = ["AFNC (ข่าวปลอมไทย)", "ACSC (คดีหลอกลวง)", "EUvsDisinfo", "AI Incident Database", "Freedom on the Net"]
SRC = {"afnc": SOURCES[0], "acsc": SOURCES[1], "eu": SOURCES[2], "aiid": SOURCES[3], "fotn": SOURCES[4]}
REGIONS = {"all": "ทั้งหมด", "th": "ประเทศไทย", "foreign": "ต่างประเทศ"}
STATUS_LABELS = ["ข่าวปลอม", "ข่าวบิดเบือน", "ข่าวจริง", "อื่น ๆ (ไม่ใช่คำตัดสิน)"]
GROUPS = ["ทุกประเทศ", "อาเซียน", "เสรี", "เสรีบางส่วน", "ไม่เสรี"]
TH_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
_STATUS_OF = {"Fake": "ข่าวปลอม", "Distorted": "ข่าวบิดเบือน", "True": "ข่าวจริง"}
_STATUS_OTHER = STATUS_LABELS[3]


@dataclass(frozen=True)
class Selection:
    date_from: pd.Timestamp
    date_to: pd.Timestamp
    years: tuple[int, ...] = ()
    quarters: tuple[int, ...] = ()
    months: tuple[int, ...] = ()
    region: str = "all"
    group: str = "ทุกประเทศ"
    countries: tuple[str, ...] = ()          # iso3
    cats: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    damage: tuple[str, ...] = ()
    sources: tuple[str, ...] = tuple(SOURCES)
    _bounds: tuple = field(default=(), repr=False, compare=False)

    def has(self, key: str) -> bool:
        return SRC[key] in self.sources


def default_selection(date_min, date_max) -> Selection:
    lo, hi = pd.Timestamp(date_min), pd.Timestamp(date_max)
    return Selection(lo, hi, _bounds=(lo, hi))


def reset(sel: Selection) -> Selection:
    lo, hi = sel._bounds
    return default_selection(lo, hi)


# --------------------------------------------------------------------------- masks


def _time_mask(dates: pd.Series, s: Selection) -> pd.Series:
    m = (dates >= s.date_from) & (dates <= s.date_to + pd.Timedelta(hours=23, minutes=59))
    if s.years:
        m &= dates.dt.year.isin(s.years)
    if s.quarters:
        m &= dates.dt.quarter.isin(s.quarters)
    if s.months:
        m &= dates.dt.month.isin(s.months)
    return m


def status_of(items: pd.DataFrame) -> pd.Series:
    """Verdict status in Thai; any post that is not a verdict (articles, advisories, ...) is 'อื่น ๆ'."""
    v = items["verdict_en"].map(_STATUS_OF)
    return v.where(items["item_type"].eq("Verdict") & v.notna(), _STATUS_OTHER)


def afnc(items: pd.DataFrame, s: Selection) -> pd.DataFrame:
    if not s.has("afnc") or s.region == "foreign":
        return items.iloc[0:0]
    d = items[_time_mask(items["date"], s)]
    if s.cats:
        d = d[d["category_th"].isin(s.cats)]
    if s.statuses:
        d = d[status_of(d).isin(s.statuses)]
    return d


def weekly(w: pd.DataFrame, s: Selection) -> pd.DataFrame:
    if not s.has("acsc") or s.region == "foreign":
        return w.iloc[0:0]
    d = w[_time_mask(w["week_start"], s)]
    if s.damage:
        d = d[d["highest_loss_group"].isin(s.damage)]
    return d


def eu(deb: pd.DataFrame, s: Selection) -> pd.DataFrame:
    if not s.has("eu") or s.region == "th":
        return deb.iloc[0:0]
    return deb[_time_mask(deb["debunk_date"], s)]


def aiid(inc: pd.DataFrame, s: Selection) -> pd.DataFrame:
    if not s.has("aiid"):
        return inc.iloc[0:0]
    d = inc[_time_mask(inc["date"], s)]
    if s.region == "th":
        d = d[d["is_thai"]]
    elif s.region == "foreign":
        d = d[~d["is_thai"]]
    return d


def fotn(f: pd.DataFrame, s: Selection, asean: dict | None = None) -> pd.DataFrame:
    """Annual scores. Only the year part of the time filters applies; Thailand follows the region switch."""
    if not s.has("fotn"):
        return f.iloc[0:0]
    d = f[(f["data_year"] >= s.date_from.year) & (f["data_year"] <= s.date_to.year)]
    if s.years:
        d = d[d["data_year"].isin(s.years)]
    if s.region == "th":
        return d[d["iso3"] == "THA"]
    last = f[f["data_year"] == f["data_year"].max()]
    if s.group == "อาเซียน":
        keep = set(asean or [])
    elif s.group in ("เสรี", "เสรีบางส่วน", "ไม่เสรี"):
        code = {"เสรี": 1, "เสรีบางส่วน": 2, "ไม่เสรี": 3}[s.group]
        keep = set(last.loc[last["status_code"] == code, "iso3"])
    else:
        keep = set(f["iso3"])
    if s.countries:
        keep = set(s.countries)
    if s.region == "foreign":
        return d[d["iso3"].isin(keep) & (d["iso3"] != "THA")]
    return d[d["iso3"].isin(keep | {"THA"})]


# --------------------------------------------------------------------------- explanations


def why_not(key: str, s: Selection) -> str:
    """'' when the dataset is in scope, otherwise the reason it shows no data."""
    if not s.has(key):
        return f"ไม่ได้เลือกแหล่งข้อมูล {SRC[key]} ในตัวกรอง"
    if key in ("afnc", "acsc") and s.region == "foreign":
        return f"{SRC[key]} เป็นข้อมูลของประเทศไทยเท่านั้น — ตัวกรองถูกตั้งเป็น 'ต่างประเทศ'"
    if key == "eu" and s.region == "th":
        return "EUvsDisinfo เป็นข้อมูลต่างประเทศ (ไม่มีรายการของไทย) — ตัวกรองถูกตั้งเป็น 'ประเทศไทย'"
    return ""


def notes(s: Selection) -> list[str]:
    """Filters that exist but cannot apply to some dataset (so nobody assumes they did)."""
    out = []
    if s.months or s.quarters:
        out.append("เดือน/ไตรมาส ไม่ใช้กับ Freedom on the Net (ข้อมูลรายปี)")
    if s.cats or s.statuses:
        out.append("ประเภทข่าว/สถานะข่าว ใช้กับ AFNC เท่านั้น (EUvsDisinfo ใช้การจัดหมวดคนละระบบ)")
    if s.damage:
        out.append("หมวดหมู่ความเสียหาย ใช้กับ ACSC โดยเลือกสัปดาห์ที่ประเภทที่เสียหายสูงสุดตรงกับที่เลือก")
    if s.countries or s.group != "ทุกประเทศ":
        out.append("ประเทศ/กลุ่มประเทศ ใช้กับ Freedom on the Net เท่านั้น (AFNC/ACSC เป็นของไทย)")
    return out


def chips(s: Selection) -> list[str]:
    """Human-readable list of filters that differ from the default."""
    out = []
    lo, hi = s._bounds if s._bounds else (s.date_from, s.date_to)
    if (s.date_from, s.date_to) != (lo, hi):
        out.append(f"ช่วงวันที่ {s.date_from:%Y-%m-%d} → {s.date_to:%Y-%m-%d}")
    if s.years:
        out.append("ปี " + ", ".join(map(str, s.years)))
    if s.quarters:
        out.append("ไตรมาส " + ", ".join(f"Q{q}" for q in s.quarters))
    if s.months:
        out.append("เดือน " + ", ".join(TH_MONTHS[m - 1] for m in s.months))
    if s.region != "all":
        out.append(REGIONS[s.region])
    if s.group != "ทุกประเทศ":
        out.append(f"กลุ่ม: {s.group}")
    if s.countries:
        out.append(f"ประเทศ {len(s.countries)} ประเทศ")
    if s.cats:
        out.append(f"ประเภทข่าว {len(s.cats)} หมวด")
    if s.statuses:
        out.append("สถานะ: " + ", ".join(s.statuses))
    if s.damage:
        out.append("ความเสียหาย: " + ", ".join(s.damage))
    if set(s.sources) != set(SOURCES):
        out.append(f"แหล่งข้อมูล {len(s.sources)}/{len(SOURCES)}")
    return out


def update(sel: Selection, **kw) -> Selection:
    return replace(sel, **kw)
