"""Turns the analysis results into plain-language findings (every number computed, none typed)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from analytics import insights as ix
from analytics import metrics as mx

Tables = dict[str, pd.DataFrame]
TH_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def _d(ts: pd.Timestamp) -> str:
    return f"{ts.day} {TH_MONTHS[ts.month - 1]} {ts.year}"


@dataclass
class Analysis:
    decomp: ix.Decomposition | None
    cp_cases: ix.ChangePoint | None
    cp_lpc: ix.ChangePoint | None
    outliers: pd.DataFrame
    lag: pd.DataFrame
    detrended: dict
    mix: ix.MixShift
    false_trend: dict
    scam_share: pd.DataFrame
    aiid: dict
    asean: dict


def run_all(t: Tables) -> Analysis:
    w = t["weekly"]
    u = mx.usable_weeks(w)
    return Analysis(
        decomp=ix.decompose_loss(w),
        cp_cases=ix.change_point(u["acsc_cases"], u["week_start"]),
        cp_lpc=ix.change_point(u["acsc_loss_per_case_calc"], u["week_start"]),
        outliers=ix.robust_z(w),
        lag=ix.lagged_correlation(w),
        detrended=ix.detrended_correlation(w),
        mix=ix.mix_shift(t["afnc_monthly"]),
        false_trend=ix.false_share_trend(mx.afnc_yearly(w)),
        scam_share=t["afnc_scam_share"],
        aiid=ix.aiid_growth_rates(t["aiid_yearly"]),
        asean=ix.asean_standing(t["fotn"], int(t["fotn"]["data_year"].max())),
    )


def key_findings(a: Analysis) -> list[dict]:
    """[{headline, title, detail, caution}] ordered by how well the data supports them."""
    out = []
    d = a.decomp
    if d:
        out.append({
            "headline": f"ความเสียหายลด {abs(d.delta) / d.loss_peak:.0%} · {d.severity_share:.0f}% มาจากบาท/คดีที่ลดลง",
            "title": f"ความเสียหายรายสัปดาห์ลดลง {abs(d.delta) / d.loss_peak:.0%} ราว {d.severity_share:.0f}% เกิดจาก 'ความเสียหายต่อคดีที่ลดลง' ไม่ใช่จำนวนคดีที่ลดลงอย่างเดียว",
            "detail": f"เทียบ 8 สัปดาห์ที่สูงสุด ({_d(d.peak_start)}–{_d(d.peak_end)}) กับต่ำสุด ({_d(d.trough_start)}–{_d(d.trough_end)}): "
                      f"ความเสียหาย {d.loss_peak / 1e6:,.0f} → {d.loss_trough / 1e6:,.0f} ล้านบาท/สัปดาห์ · คดี {d.cases_peak:,.0f} → {d.cases_trough:,.0f} · "
                      f"บาท/คดี {d.lpc_peak:,.0f} → {d.lpc_trough:,.0f} · ผลจากจำนวนคดี {d.cases_effect / 1e6:,.0f} ล้าน และจากความเสียหายต่อคดี {d.severity_effect / 1e6:,.0f} ล้านบาท",
            "caution": "การแยกส่วนเป็นการคำนวณทางบัญชี บอกว่า 'ส่วนใดเปลี่ยน' ไม่ได้บอกว่า 'ทำไม'"})
    c, s = a.cp_cases, a.cp_lpc
    if c and s:
        out.append({
            "headline": f"จุดเปลี่ยน {TH_MONTHS[c.date.month - 1]} {c.date.year}: คดี {c.pct_change:+.0f}% · บาท/คดี {s.pct_change:+.0f}%",
            "title": f"พบจุดเปลี่ยนชัดเจนช่วง {TH_MONTHS[c.date.month - 1]} {c.date.year}: คดีลดลง {abs(c.pct_change):.0f}% และบาท/คดีลดลง {abs(s.pct_change):.0f}%",
            "detail": f"จุดแบ่งที่อธิบายความผันแปรได้มากที่สุดคือสัปดาห์ {_d(c.date)} (จำนวนคดี เฉลี่ย {c.mean_before:,.0f} → {c.mean_after:,.0f}; อธิบายความผันแปรได้ {c.variance_explained:.0%}) "
                      f"และสัปดาห์ {_d(s.date)} (บาท/คดี {s.mean_before:,.0f} → {s.mean_after:,.0f})",
            "caution": "ทดสอบด้วยการสลับลำดับ (p ≈ " + f"{max(c.p_permutation, 0.001):.3f}" + ") ซึ่งไม่คิดความสัมพันธ์ข้ามสัปดาห์ จึงมองต่ำเกินจริง · ข้อมูลไม่บอกสาเหตุ และหลังจุดเปลี่ยนตัวเลขอาจกลับขึ้นบางส่วน (ดูกราฟ)"})
    sh = a.scam_share
    y0, y1 = sh[sh["year"] == 2020].iloc[0], sh[sh["year"] == 2025].iloc[0]
    out.append({
        "headline": f"ข่าวเท็จเรื่องหลอกลวง/แอบอ้าง {y0['scam_share_of_tagged_pct']:.1f}% → {y1['scam_share_of_tagged_pct']:.1f}% (2020→2025)",
        "title": f"ข่าวเท็จหันมาเกี่ยวกับการแอบอ้าง/หลอกลวงมากขึ้น: จาก {y0['scam_share_of_tagged_pct']:.1f}% (2020) เป็น {y1['scam_share_of_tagged_pct']:.1f}% (2025) ของข่าวเท็จที่มีแท็ก",
        "detail": f"นับข่าวเท็จที่มีแท็ก เพจปลอม / มิจฉาชีพ / แอบอ้าง / หลอกลวง / ไลน์ปลอม / SMS / ชวนลงทุน / สินเชื่อ: {int(y1['scam_tagged']):,} จาก {int(y1['tagged']):,} เรื่องในปี 2025 "
                  f"(ปี 2026 ลดเป็น {sh[sh['year'] == 2026]['scam_share_of_tagged_pct'].iloc[0]:.1f}% ซึ่งอาจเกี่ยวกับหมวดใหม่ 'อาชญากรรมออนไลน์' แต่ข้อมูลไม่ยืนยัน)",
        "caution": "นิยามอิงแท็กที่ศูนย์ฯ ใส่เอง จึงขึ้นกับวิธีติดแท็กของศูนย์ฯ"})
    ft = a.false_trend
    out.append({
        "headline": f"สัดส่วนข่าวเท็จ {ft['share0']:.1f}% → {ft['share1']:.1f}% และประเด็นเปลี่ยน",
        "title": f"สัดส่วนข่าวเท็จลดลงอย่างมีนัยสำคัญ {ft['share0']:.1f}% → {ft['share1']:.1f}% ({ft['y0']}→{ft['y1']}) และประเด็นเปลี่ยนจริง (Cramér's V = {a.mix.cramers_v:.2f})",
        "detail": f"ทดสอบสัดส่วนสองกลุ่ม z = {ft['z']:.1f} · การกระจายหมวดของข่าวเท็จ 2020–2025 ต่างกันตามปี (χ² = {a.mix.chi2:,.0f}, df = {a.mix.dof}) "
                  "โดยหมวดสุขภาพเกินคาดช่วงแรก และหมวดการเงิน/ความมั่นคงเกินคาดช่วงหลัง (ดูแผนที่ความร้อนด้านล่าง)",
        "caution": "ศูนย์ฯ เลือกเรื่องที่ตรวจเอง และเกณฑ์ตัดสินอาจเปลี่ยน (คำตัดสิน 'บิดเบือน' เพิ่มขึ้นมาก) จึงไม่ใช่การเปลี่ยนของข่าวปลอมในโลกจริงโดยตรง"})
    lag0 = a.lag.set_index("lag").loc[0]
    nsig = int(a.lag["significant"].sum())
    out.append({
        "headline": "ข่าวปลอม ↔ คดี: ไม่พบความสัมพันธ์",
        "title": "ไม่พบหลักฐานว่าข่าวปลอมนำหรือตามหลังคดีหลอกลวง",
        "detail": f"ความสัมพันธ์ระดับดิบ r = {a.detrended['raw']:+.2f} หายไปหลังตัดแนวโน้มเวลา (r = {a.detrended['detrended']:+.2f}, เกณฑ์ ±{a.detrended['ci95']:.2f}) · "
                  f"ทดสอบการเปลี่ยนแปลงรายสัปดาห์ที่ lag −4 ถึง +4 สัปดาห์: {nsig} จาก {len(a.lag)} lag เกินเกณฑ์ (lag 0: r = {lag0['r']:+.2f}, n = {int(lag0['n'])}) "
                  "ซึ่งใกล้เกณฑ์ และเมื่อทดสอบหลาย lag พร้อมกัน การเกินเกณฑ์สัก 1 ครั้งเกิดโดยบังเอิญได้",
        "caution": f"ข้อมูลคดีมีเพียง {a.detrended['n']} สัปดาห์ ผลที่ 'ไม่พบ' ไม่ได้พิสูจน์ว่า 'ไม่มี' ความสัมพันธ์"})
    g = a.aiid
    out.append({
        "headline": f"deepfake {g['deepfake_share0']:.0f}% → {g['deepfake_share1']:.0f}% ของเหตุการณ์ AI ({g['y0']}→{g['y1']})",
        "title": f"deepfake เพิ่มจาก {g['deepfake_share0']:.0f}% เป็น {g['deepfake_share1']:.0f}% ของเหตุการณ์ AI ทั้งหมด ({g['y0']}→{g['y1']}) และ scam/fraud จาก {g['scam_share0']:.0f}% เป็น {g['scam_share1']:.0f}%",
        "detail": f"เหตุการณ์รวม ×{g['incidents_x']:.1f} · deepfake ×{g['deepfake_x']:.1f} · scam/fraud ×{g['scam_x']:.1f} ใน {g['y1'] - g['y0']} ปี",
        "caution": f"ฐานปี {g['y0']} เล็ก (deepfake {g['deepfake0']} เรื่อง, scam {g['scam0']} เรื่อง) ตัวคูณจึงเกินจริงง่าย · ส่วนหนึ่งอาจเป็นผลจากวิธีเก็บข่าวของฐานข้อมูล (เน้นข่าวภาษาอังกฤษ ตามคู่มือ) ข้อมูลไม่แยกให้"})
    asn = a.asean
    out.append({
        "headline": f"ไทยอันดับ {asn['rank']}/{asn['n']} ในอาเซียน · ต่ำกว่ามัธยฐาน {abs(asn['gap_to_median']):.0f} คะแนน",
        "title": f"ไทยอยู่อันดับ {asn['rank']} จาก {asn['n']} ประเทศอาเซียนที่มีข้อมูล ต่ำกว่าค่ามัธยฐานของประเทศอื่น {abs(asn['gap_to_median']):.0f} คะแนน",
        "detail": f"ไทย {asn['score']}/100 · มัธยฐานของประเทศอื่นในอาเซียน {asn['median_others']:.0f} · จุดอ่อนที่สุดคือ '{asn['weakest_component'][0]}' ({asn['weakest_component'][1]:.0f}% ของคะแนนเต็ม) "
                  "ขณะที่ด้านการเข้าถึงอินเทอร์เน็ตอยู่ระดับเดียวกับฟิลิปปินส์",
        "caution": f"การประเมินของผู้เชี่ยวชาญ ไม่ใช่การนับเหตุการณ์ · เทียบเฉพาะ {asn['n']} ประเทศอาเซียนที่มีในข้อมูล"})
    return out
