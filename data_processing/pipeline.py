"""Build every processed table from the raw files.

    python -m data_processing.pipeline            # auto-detect raw folder
    FT_RAW_DIR=D:\\data python -m data_processing.pipeline
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import config
from data_processing import loaders as ld
from data_processing import transform as tf
from data_processing import validation as vd

log = logging.getLogger(__name__)


def build_all(raw: Path) -> tuple[dict[str, pd.DataFrame], dict]:
    checks: list[vd.Check] = []
    clog: list[dict] = []

    def step(dataset: str, action: str, before, after, detail: str = "") -> None:
        clog.append({"dataset": dataset, "action": action, "before": before, "after": after, "detail": detail})

    # --- Thai: weekly panel, ACSC, AFNC -----------------------------------
    panel = ld.read_panel(raw)
    items = ld.read_afnc(raw)
    weekly = tf.build_weekly(panel)
    checks += [
        vd.check_weekly_continuity(panel),
        vd.check_afnc_matches_panel(panel, items),
        vd.check_unique("AFNC post_id", items["post_id"]),
        vd.check_suspect_weeks(weekly),
        vd.check_missing_acsc_weeks(weekly),
        vd.check_loss_per_case(weekly),
        vd.check_scam_types_mapped(weekly, config.ACSC_TYPE_OTHER),
        vd.check_rounded_loss(weekly),
    ]
    step("ACSC/panel", "ตั้งป้ายสัปดาห์คดีที่ติดป้ายน่าสงสัยและตัดออกจากสถิติ", int(weekly["acsc_reported"].sum()),
         int(weekly["acsc_usable"].sum()), "สัปดาห์ 16–22 ส.ค. 2026 (79,311 คดี)")
    in_range = weekly["week_start"] >= weekly.loc[weekly["acsc_reported"], "week_start"].min()
    gap = in_range & ~weekly["acsc_reported"]
    step("ACSC/panel", "สัปดาห์ที่ไม่มีตัวเลขคดีในช่วงที่มีการแถลง คงเป็นค่าว่าง (ไม่เติม 0)", int(gap.sum()),
         int(weekly.loc[gap, "acsc_cases"].fillna(0).ne(0).sum()), "ก่อน=จำนวนสัปดาห์ว่าง, หลัง=สัปดาห์ที่ถูกเติมค่า (ต้องเป็น 0)")
    raw_types = pd.concat([panel["acsc_top_type_th"], panel["acsc_highest_loss_type_th"]]).dropna()
    grouped = pd.concat([weekly["top_type_group"], weekly["highest_loss_group"]]).dropna()
    step("ACSC/panel", "รวมป้ายประเภทคดีที่สะกดต่างกันเป็นกลุ่ม", int(raw_types.nunique()), int(grouped.nunique()), "ป้ายต่างกันตามสำนักข่าว")
    step("ACSC/panel", "คำนวณความเสียหายต่อคดีใหม่ ไม่ใช้ค่าเปลี่ยนจากสัปดาห์ก่อนที่แถลง", int(weekly["acsc_reported"].sum()),
         int(weekly["acsc_loss_per_case_calc"].notna().sum()), "ตรวจตรงกับค่าในไฟล์ ±1 บาท")
    cat_before = items.loc[items["item_type"] == "Verdict", "category_en"].nunique()
    cat_after = items.loc[items["item_type"] == "Verdict", "category_en"].map(tf._category_th).nunique()
    step("AFNC", "ใช้เฉพาะโพสต์ประเภทคำตัดสินในกราฟข่าวเท็จ", len(items), int((items["item_type"] == "Verdict").sum()), "ตัดบทความความรู้ ประกาศเตือนภัย กิจกรรม")
    step("AFNC", "รวมหมวดเล็ก (Economy, Drugs, Other news) เป็น 'อื่น ๆ' และแปลเป็นไทย", int(cat_before), int(cat_after), "")
    tag_raw = items["topic_tags"].dropna().str.split(";").explode().str.strip()
    tag_new = items["topic_tags"].map(tf.normalize_tags).explode().dropna()
    step("AFNC", "รวมแท็กที่สะกดต่างกัน (เช่น โควิด-19/COVID19) และตัดแท็กทั่วไป",
         int((tag_raw.value_counts() >= 15).sum()), int((tag_new.value_counts() >= 15).sum()), "นับเฉพาะแท็กที่พบ ≥ 15 โพสต์")
    step("AFNC", "ตรวจโพสต์ซ้ำตาม post_id", len(items), int(items["post_id"].nunique()), "")
    step("AFNC", "คำตัดสินที่ไม่มีหน่วยงานตรวจสอบ (คงเป็นค่าว่าง)", int((items["item_type"] == "Verdict").sum()),
         int(items.loc[items["item_type"] == "Verdict", "checked_by_agency"].notna().sum()), "ไม่เติมค่า")
    tables = {
        "weekly": weekly,
        "acsc_types": tf.acsc_type_summary(weekly),
        "afnc_monthly": tf.afnc_monthly(items),
        "afnc_agencies": tf.afnc_agencies(items),
        "afnc_tags": tf.afnc_tags(items),
    }
    afnc_last = items["date"].max()

    # --- AIID: latest export + weekly snapshots ---------------------------
    snaps = ld.aiid_snapshot_paths(raw)
    snap_frames = [(stamp, ld.read_aiid_incidents(p, ["Incident ID", "date"])) for stamp, p in snaps]
    latest_stamp, latest_path = snaps[-1]
    flagged = tf.aiid_flags(ld.read_aiid_incidents(latest_path))
    growth = tf.aiid_growth(snap_frames)
    checks += [vd.check_unique("AIID Incident ID", flagged["Incident ID"]),
               vd.check_aiid_no_removed(growth), vd.check_aiid_unclassified(flagged)]
    step("AIID", "แปลงวันที่เหตุการณ์", len(flagged), int(flagged["date"].notna().sum()), "")
    step("AIID", "ติดธง deepfake / scam / ไทย จากข้อความ (ไม่แยกตัวพิมพ์)", len(flagged),
         int(flagged["is_deepfake"].sum()), f"scam/fraud {int(flagged['is_scam'].sum())}, ไทย {int(flagged['is_thai'].sum())}")
    step("AIID", "เหตุการณ์ที่ยังไม่ถูกจัดหมวดความเสี่ยง แสดงเป็น 'ยังไม่จัดหมวด'", len(flagged), int(flagged["classified"].sum()), "")
    step("AIID", "เทียบ 13 ฉบับรายสัปดาห์ด้วย Incident ID", int(snap_frames[0][1].shape[0]), len(flagged), "ก่อน=ฉบับ 3 ส.ค., หลัง=ฉบับ 26 ต.ค. ไม่มีเหตุการณ์ถูกลบ")
    tables |= {
        "aiid_clean": flagged.drop(columns=["description", "Implicated Systems"]),
        "aiid_yearly": tf.aiid_yearly(flagged),
        "aiid_risk": tf.aiid_risk(flagged),
        "aiid_thai": tf.aiid_thai(flagged),
        "aiid_top": tf.aiid_top_reported(flagged),
        "aiid_growth": growth,
    }

    # --- Freedom on the Net ----------------------------------------------
    fotn_raw = ld.read_fotn(raw)
    fotn = tf.build_fotn(fotn_raw)
    checks += [vd.check_unique("FOTN (ประเทศ, ปี)", fotn["iso3"] + fotn["data_year"].astype(str)),
               vd.check_fotn_sum(fotn), vd.check_fotn_coverage(fotn)]
    tables["fotn"] = fotn
    step("FOTN", "ตั้งชื่อคอลัมน์ใหม่/เพิ่ม % ของคะแนนเต็ม 3 ส่วน (ไม่เติมปีที่ไม่มีข้อมูล)", len(fotn_raw), len(fotn), "ช่องว่าง ≠ 0")

    # --- EUvsDisinfo ------------------------------------------------------
    eu = tf.eu_prepare(ld.read_eu(raw))
    checks += [vd.check_eu_dates(eu), vd.check_eu_partial(eu)]
    afnc_flags = tf.afnc_theme_flags(items)
    aiid_flags = tf.aiid_theme_flags(flagged)
    tables["theme_year"] = tf.theme_year(flagged, aiid_flags, items, afnc_flags)
    step("AIID+AFNC", "ติดธงธีมภัย (10 ธีม) จากข้อความ เพื่อเทียบสากลกับไทย", len(flagged), int(aiid_flags.any(axis=1).sum()),
         f"AFNC: {int(afnc_flags.any(axis=1).sum())} จาก {len(items)} โพสต์ตรงอย่างน้อย 1 ธีม")
    afnc_clean = tf.clean_afnc_items(items)
    tables["afnc_scam_share"] = tf.afnc_scam_share(afnc_clean)
    step("EUvsDisinfo", "แปลงวันที่จากข้อความ DD-MM-YYYY", len(eu), int(eu["debunk_dt"].notna().sum()), "แปลงได้ทั้งหมด")
    step("EUvsDisinfo", "ยุบเป็น 1 แถวต่อการหักล้าง (debunk_id)", len(eu), int(eu["debunk_id"].nunique()), "ใช้นับเรื่อง ไม่นับบทความ")
    step("EUvsDisinfo", "แถวที่ไม่มี keywords ถูกข้ามในกราฟประเด็น", len(eu), int(eu["keywords"].notna().sum()), "ไม่เติมค่า")
    eu_deb = tf.eu_debunks(eu)
    tables["covid_share"] = tf.covid_share(eu_deb, items)
    tables["aiid_country"] = tf.aiid_country_mentions(flagged, fotn, int(fotn["data_year"].max()))
    step("AIID", "ดึงชื่อประเทศจากข้อความ (ช่องประเทศมีเพียง ~8%) เพื่อเทียบกับคะแนนเสรีภาพ", int(flagged.shape[0]),
         int((tables["aiid_country"]["mentions"] > 0).sum()), "ก่อน=เหตุการณ์ หลัง=จำนวนประเทศที่ถูกกล่าวถึง ≥ 1 ครั้ง · เป็นการกล่าวถึง ไม่ใช่สถานที่เกิดเหตุ")
    tables |= {
        "afnc_clean": afnc_clean,
        "eu_debunks": eu_deb,
        "eu_yearly": tf.eu_yearly(eu),
        "eu_monthly": tf.eu_monthly(eu),
        "eu_keywords": tf.eu_keywords(eu),
        "eu_languages": tf.eu_languages(eu),
        "eu_domains": tf.eu_domains(eu),
    }

    tables["validation"] = vd.to_frame(checks)
    tables["cleaning_log"] = pd.DataFrame(clog)
    usable = weekly[weekly["acsc_usable"]]
    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aiid_snapshot": latest_stamp.strftime("%Y-%m-%d"),
        "afnc_last_date": afnc_last.strftime("%Y-%m-%d"),
        "acsc_first_week": weekly.loc[weekly["acsc_reported"], "week_start"].min().strftime("%Y-%m-%d"),
        "acsc_last_week": weekly.loc[weekly["acsc_reported"], "week_start"].max().strftime("%Y-%m-%d"),
        "acsc_weeks_usable": int(len(usable)),
        "eu_last_date": eu["debunk_dt"].max().strftime("%Y-%m-%d"),
        "fotn_last_year": int(fotn["data_year"].max()),
        "n_aiid_incidents": int(len(flagged)),
        "n_afnc_posts": int(len(items)),
        "n_eu_debunks": int(eu["debunk_id"].nunique()),
    }
    return tables, meta


def write_all(tables: dict[str, pd.DataFrame], meta: dict, out: Path = config.PROCESSED_DIR) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False, encoding="utf-8-sig")
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def run(raw: Path | None = None) -> dict:
    raw = raw or config.find_raw_dir()
    if raw is None:
        raise FileNotFoundError(
            "ไม่พบโฟลเดอร์ข้อมูลดิบ — วางโฟลเดอร์ 01_… 04_… ไว้ใน data/raw/ หรือกำหนด FT_RAW_DIR")
    log.info("building from %s", raw)
    tables, meta = build_all(raw)
    write_all(tables, meta)
    return meta


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        m = run()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    print(json.dumps(m, ensure_ascii=False, indent=2))
