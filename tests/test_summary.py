"""The written summary is built from the processed tables; check structure and that nothing is empty or broken."""
import re

import pytest

import config
from analytics import qfindings as qf
from dashboard import summary
from data_processing import store


@pytest.fixture(scope="module")
def md():
    if not store.is_built():
        pytest.skip("processed tables not built")
    t = store.load_tables()
    return summary.build_summary_markdown(t, store.load_meta(), qf.run(t)), t


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
    assert f"{int(t['validation']['status'].eq('ok').sum())}" in text
    for name in ("AFNC", "ACSC", "EUvsDisinfo", "AI Incident Database", "Freedom on the Net"):
        assert name in text


def test_no_broken_values_or_empty_tables(md):
    text, _ = md
    assert not re.search(r"\bnan\b|\bNaT\b|\bNone\b|inf\b", text)
    for tbl in re.findall(r"(\|[^\n]*\|\n\|[-|]+\|\n(?:\|[^\n]*\|\n?)*)", text):
        assert len(tbl.strip().splitlines()) >= 3, "table with no data rows"


def test_limits_are_stated(md):
    text, _ = md
    assert "ไม่ใช่ข้อมูลเปิดของตำรวจ" in text and "ไม่ใช่ที่เกิดเหตุ" in text and "ไม่พบความสัมพันธ์" in text


def test_guide_covers_every_menu_page_filter_and_switch(md):
    text, _ = md
    for page in ["ภาพรวม", "Q1 ข้อมูลบิดเบือน", "Q2 ภัยหลอกลวง", "Q3 เสรีภาพ", "รายละเอียดแต่ละชุดข้อมูล", "คุณภาพข้อมูล"]:
        assert page in text.split("## 3.")[0], page
    for f in ["ช่วงปี", "หมวดข่าวไทย", "ช่วงสัปดาห์", "ความไวตรวจความผิดปกติ", "ปีข้อมูลเสรีภาพ", "เปรียบเทียบประเทศ", "ช่วงปีเหตุการณ์ AI"]:
        assert f in text, f
    for sw in ["สรุปแดชบอร์ดทั้งหมด", "แสดงหมายเหตุ", "ประมวลผลใหม่"]:
        assert sw in text


def test_guide_labels_match_the_real_widgets():
    src = open(config.ROOT / "dashboard" / "question_pages.py", encoding="utf-8").read() + open(config.ROOT / "app.py", encoding="utf-8").read()
    for label in ["ช่วงปี", "หมวดข่าวไทย", "ผลตรวจที่นับในกราฟหมวด", "ช่วงสัปดาห์", "ความไวตรวจความผิดปกติ", "ปีข้อมูลเสรีภาพ", "เปรียบเทียบประเทศ", "ช่วงปีเหตุการณ์ AI",
                  "สรุปแดชบอร์ดทั้งหมด", "แสดงหมายเหตุ"]:
        assert label in src, label
    assert "ประมวลผลใหม่" in src
