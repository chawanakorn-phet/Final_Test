"""Data-quality checks. Each check returns (name, status, detail); status is ok / warn / fail."""
from __future__ import annotations

import pandas as pd

Check = tuple[str, str, str]


def _c(name: str, ok: bool, detail: str, severity: str = "fail") -> Check:
    return (name, "ok" if ok else severity, detail)


def check_weekly_continuity(panel: pd.DataFrame) -> Check:
    gaps = panel["week_start"].sort_values().diff().dropna().dt.days
    bad = int((gaps != 7).sum())
    return _c("สัปดาห์ในตารางรวมต่อเนื่องทุก 7 วัน", bad == 0, f"{len(panel)} สัปดาห์, ผิดปกติ {bad} จุด")


def check_afnc_matches_panel(panel: pd.DataFrame, items: pd.DataFrame) -> Check:
    v = items[items["item_type"] == "Verdict"]
    recomputed = v.groupby("week_start").size().reindex(panel["week_start"]).fillna(0).astype(int).to_numpy()
    diff = int((recomputed != panel["afnc_verdicts"].to_numpy()).sum())
    return _c("จำนวนคำตัดสินรายสัปดาห์ตรงกับที่นับใหม่จากโพสต์ AFNC", diff == 0, f"สัปดาห์ที่ไม่ตรง {diff}")


def check_unique(name: str, s: pd.Series) -> Check:
    dup = int(s.duplicated().sum())
    return _c(f"{name} ไม่ซ้ำ", dup == 0, f"ซ้ำ {dup} แถว")


def check_suspect_weeks(weekly: pd.DataFrame) -> Check:
    n = int(weekly["acsc_suspect"].sum())
    weeks = ", ".join(weekly.loc[weekly["acsc_suspect"], "week_start"].dt.strftime("%Y-%m-%d"))
    return ("สัปดาห์คดีที่ติดป้ายน่าสงสัย (ตัดออกจากสถิติ)", "warn" if n else "ok", f"{n} สัปดาห์: {weeks or '-'}")


def check_missing_acsc_weeks(weekly: pd.DataFrame) -> Check:
    start = weekly.loc[weekly["acsc_reported"], "week_start"].min()
    miss = weekly[(weekly["week_start"] >= start) & ~weekly["acsc_reported"]]
    weeks = ", ".join(miss["week_start"].dt.strftime("%Y-%m-%d"))
    return ("สัปดาห์ที่ไม่มีตัวเลขคดี (แสดงเป็นช่องว่าง ไม่ใช่ 0)", "warn" if len(miss) else "ok", f"{len(miss)} สัปดาห์: {weeks or '-'}")


def check_loss_per_case(weekly: pd.DataFrame) -> Check:
    r = weekly[weekly["acsc_reported"] & weekly["acsc_loss_per_case_baht"].notna()]
    diff = (r["acsc_loss_baht"] / r["acsc_cases"] - r["acsc_loss_per_case_baht"]).abs()
    bad = int((diff > 1).sum())
    return _c("ความเสียหายต่อคดีที่คำนวณใหม่ตรงกับค่าในไฟล์ (±1 บาท)", bad == 0, f"ไม่ตรง {bad} สัปดาห์", "warn")


def check_scam_types_mapped(weekly: pd.DataFrame, other_label: str) -> Check:
    n = int((weekly["top_type_group"].eq(other_label) | weekly["highest_loss_group"].eq(other_label)).sum())
    return _c("ป้ายประเภทคดีทุกแบบถูกจัดเข้ากลุ่ม", n == 0, f"ตกไปกลุ่ม 'อื่น ๆ' {n} แถว", "warn")


def check_rounded_loss(weekly: pd.DataFrame) -> Check:
    n = int(weekly["acsc_rounded"].sum())
    return ("ตัวเลขความเสียหายที่ถูกปัดเป็นล้านบาท", "warn" if n else "ok", f"{n} สัปดาห์ (ตั้งแต่ 9 ส.ค. 2026) แสดงเป็นจุดโปร่ง")


def check_fotn_sum(f: pd.DataFrame) -> Check:
    s = f["obstacles_to_access"] + f["limits_on_content"] + f["violations_of_user_rights"]
    bad = int((s != f["total_score"]).sum())
    return _c("คะแนนรวม FOTN เท่ากับผลรวม 3 ส่วน", bad == 0, f"ไม่ตรง {bad} แถว")


def check_fotn_coverage(f: pd.DataFrame) -> Check:
    n = f.groupby("data_year")["iso3"].nunique()
    return ("จำนวนประเทศ FOTN ต่อปีไม่คงที่ (ห้ามเทียบค่าเฉลี่ยข้ามปี)", "warn", f"{int(n.min())} ประเทศ (ปี {n.idxmin()}) ถึง {int(n.max())} ประเทศ (ปี {n.idxmax()})")


def check_eu_dates(eu: pd.DataFrame) -> Check:
    bad = int(eu["debunk_dt"].isna().sum())
    return _c("วันที่ EUvsDisinfo แปลงได้ทั้งหมด (DD-MM-YYYY)", bad == 0, f"แปลงไม่ได้ {bad} แถว")


def check_eu_partial(eu: pd.DataFrame) -> Check:
    last = eu["debunk_dt"].max()
    return ("ข้อมูล EUvsDisinfo ปีสุดท้ายไม่ครบปี", "warn", f"ถึง {last:%d %b %Y}")


def check_aiid_no_removed(growth: pd.DataFrame) -> Check:
    removed = int(growth["removed"].fillna(0).sum())
    return _c("ไม่มีเหตุการณ์ AIID หายไประหว่างฉบับรายสัปดาห์", removed == 0, f"หายไปรวม {removed}")


def check_aiid_unclassified(flagged: pd.DataFrame) -> Check:
    n = int((~flagged["classified"]).sum())
    return ("เหตุการณ์ AIID ที่ยังไม่ถูกจัดหมวดความเสี่ยง", "warn", f"{n} จาก {len(flagged)} ({n / len(flagged):.1%})")


def to_frame(checks: list[Check]) -> pd.DataFrame:
    return pd.DataFrame(checks, columns=["check", "status", "detail"])
