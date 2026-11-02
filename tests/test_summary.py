"""The written summary and the data bundle are built from the processed tables; check structure and that nothing is broken."""
import json
import re

import pytest

import config
from analytics import qfindings as qf
from dashboard import summary
from data_processing import store
from pipeline import build_data as bd


@pytest.fixture(scope="module")
def built():
    if not store.is_built():
        pytest.skip("processed tables not built")
    return bd.build()


@pytest.fixture(scope="module")
def md(built):
    return built["summary_md"], store.load_tables()


def test_has_every_section_and_question(md):
    text, _ = md
    for h in ["## 1. สรุปสั้น", "## 2. อ่านแดชบอร์ดนี้อย่างไร", "## 3. ข้อมูลที่ใช้", "## 4. การทำความสะอาด", "## 5. Q1", "## 6. Q2", "## 7. Q3", "## 8. ข้อจำกัดโดยรวม", "## 9. วิธีวิเคราะห์", "## 10. แหล่งที่มา", "สารบัญ"]:
        assert h in text, h
    for q in ("Q1", "Q2", "Q3"):
        assert f"({q})" in text


def test_numbers_match_the_tables(md):
    text, t = md
    w = t["weekly"]
    last = w[w["acsc_usable"]].iloc[-1]
    assert f"{last['acsc_cases']:,.0f} คดี" in text
    for name in ("AFNC", "ACSC", "EUvsDisinfo", "AI Incident Database", "Freedom on the Net"):
        assert name in text


def test_no_broken_values_or_empty_tables(md):
    text, _ = md
    assert not re.search(r"\bnan\b|\bNaT\b|\bNone\b|inf\b", text)
    for tbl in re.findall(r"(\|[^\n]*\|\n\|[-|]+\|\n(?:\|[^\n]*\|\n?)*)", text):
        assert len(tbl.strip().splitlines()) >= 3, "table with no data rows"


def test_limits_and_forecast_and_linkage_are_stated(md):
    text, _ = md
    assert "ไม่ใช่ข้อมูลเปิดของตำรวจ" in text and "ไม่ใช่ที่เกิดเหตุ" in text and "ไม่พบความสัมพันธ์" in text
    assert "พยากรณ์ (แบบจำลอง" in text and "เชื่อมโยงข้ามชุดได้หรือไม่" in text and "ไม่ได้" in text


def test_guide_describes_the_real_tabs_filters_and_buttons(md):
    text, _ = md
    guide = text.split("## 3.")[0]
    ui = "".join(open(config.ROOT / "docs" / f, encoding="utf-8").read() for f in ("index.html", "app.js", "tabs_a.js", "tabs_b.js"))
    for tab in ["1 ภาพรวม", "2 ข่าวปลอมและข้อมูลบิดเบือน", "3 เสรีภาพอินเทอร์เน็ตและเปรียบเทียบประเทศ", "4 ความเสียหาย ความสัมพันธ์ และพยากรณ์", "5 สำรวจข้อมูลและแหล่งที่มา"]:
        assert tab in guide and tab in ui, tab
    for label in ["ช่วงวันที่", "ไตรมาส", "เดือน", "ประเทศไทย / ต่างประเทศ", "กลุ่มประเทศ", "ประเภทข่าว", "สถานะข่าว", "หมวดหมู่ความเสียหาย", "แหล่งข้อมูล"]:
        assert label in ui, label
    for button in ["Reset Filters", "สรุปทั้งแดชบอร์ด", "หน้าแรก", "Open Dashboard"]:
        assert button in ui and (button == "Open Dashboard" or button.replace("สรุปทั้งแดชบอร์ด", "สรุปทั้งแดชบอร์ด") in text), button


def test_bundle_structure_and_consistency(built):
    t = store.load_tables()
    assert len(built["afnc"]["d"]) == len(t["afnc_clean"]) == len(built["afnc"]["id"]) == len(built["afnc"]["st"])
    assert len(built["weekly"]) == len(t["weekly"]) and len(built["eu"]["d"]) == len(t["eu_debunks"]) and len(built["fotn"]) == len(t["fotn"])
    assert built["meta"]["date_min"] <= "1983-09-26" and built["meta"]["date_max"] == store.load_meta()["afnc_last_date"]
    assert sorted(built["analysis"]["findings"]) == ["q1", "q2", "q3"] and all(len(v) >= 5 for v in built["analysis"]["findings"].values())
    for k in ("dictionary", "source_map", "inventory", "linkage", "validation", "cleaning"):
        assert built[k], k


def test_missing_weeks_stay_null_not_zero(built):
    miss = [w for w in built["weekly"] if not w["rep"] and w["ws"] >= "2025-11-09"]
    assert len(miss) == 3 and all(w["cases"] is None and w["loss"] is None for w in miss)
    assert sum(1 for w in built["weekly"] if w["use"]) == 47 and sum(1 for w in built["weekly"] if w["sus"]) == 1


def test_forecasts_have_metrics_and_refusals_are_explained(built):
    for k, fc in built["forecast"].items():
        assert fc["ok"] is True or fc["reason"], k
        if fc["ok"]:
            assert fc["metrics"][0]["model"] == fc["model"] and fc["metrics"][0]["RMSE"] <= max(m["RMSE"] for m in fc["metrics"])
            assert all(r["lower"] <= r["forecast"] <= r["upper"] for r in fc["forecast"])


def test_linkage_flags_the_pairs_that_cannot_be_correlated(built):
    by = {r["pair"]: r for r in built["linkage"]}
    assert by["ACSC ↔ Freedom on the Net"]["ok"] is False and by["AFNC ↔ Freedom on the Net"]["ok"] is False and by["AFNC ↔ ACSC"]["ok"] is True


def test_data_js_is_valid_json_without_nan(tmp_path, built):
    text = json.dumps(built, ensure_ascii=False, separators=(",", ":"), allow_nan=False)   # raises on NaN / inf
    assert json.loads(text)["meta"]["built_at"]
